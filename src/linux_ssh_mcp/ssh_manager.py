"""
Multi-Session SSH Manager for Linux SSH MCP Server.

Author: Pawan Gunjkar (pawangunjkar@gmail.com)

Manages multiple concurrent SSH connections using paramiko.
Each connection is identified by a session name (e.g., "default", "prod", "staging").
Supports host-key verification, auto-reconnect, enforced command timeouts,
bounded output capture, stdin for scripts, and SFTP file writes.
"""

import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import paramiko

from linux_ssh_mcp.credential_store import CredentialStore, SSHCredentials


# Maximum output size in bytes (50KB default)
MAX_OUTPUT_SIZE = 50 * 1024
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 300
_READ_CHUNK = 32 * 1024

# Host key policies (SSH_HOST_KEY_POLICY):
#   accept-new (default) — trust a host the first time, save its key, and refuse to
#                          connect if that key ever changes (like OpenSSH StrictHostKeyChecking=accept-new)
#   strict               — only connect to hosts already in known_hosts
#   insecure             — accept any key, never verify (legacy behaviour; not recommended)
HOST_KEY_POLICIES = ("accept-new", "strict", "insecure")


@dataclass
class CommandResult:
    """Outcome of one remote command."""
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    error: str = ""
    timed_out: bool = False
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    timeout_seconds: int = 0

    @property
    def ok(self) -> bool:
        return not self.error and not self.timed_out and self.exit_code == 0

    def format(self) -> str:
        """Render as the text the MCP tools return."""
        if self.error:
            return self.error

        out = self.stdout
        err = self.stderr
        if self.stdout_truncated:
            out += f"\n\n... [OUTPUT TRUNCATED — {self.stdout_bytes} bytes total, showing the first {len(self.stdout.encode())} bytes]"
        if self.stderr_truncated:
            err += f"\n\n... [STDERR TRUNCATED — {self.stderr_bytes} bytes total]"

        parts = []
        if self.timed_out:
            parts.append(
                f"❌ Command timed out after {self.timeout_seconds}s and was stopped. Partial output (if any) follows. "
                "Use ssh_execute_background for long-running work."
            )
        if out.strip():
            parts.append(out.strip())
        if err.strip():
            parts.append(f"[STDERR]\n{err.strip()}")
        if self.exit_code not in (0, None):
            parts.append(f"[EXIT CODE: {self.exit_code}]")
        return "\n\n".join(parts) if parts else "(no output)"


class _Capture:
    """Keep the first `limit` bytes of a stream while counting everything received."""

    def __init__(self, limit: int):
        self.limit = limit
        self.chunks: list[bytes] = []
        self.kept = 0
        self.total = 0

    def add(self, data: bytes) -> None:
        self.total += len(data)
        room = self.limit - self.kept
        if room > 0:
            piece = data[:room]
            self.chunks.append(piece)
            self.kept += len(piece)

    def text(self) -> str:
        return b"".join(self.chunks).decode("utf-8", errors="replace")

    @property
    def truncated(self) -> bool:
        return self.total > self.kept


@dataclass
class SSHSession:
    """Represents a single SSH session."""
    name: str
    host: str
    port: int
    username: str
    client: paramiko.SSHClient
    connected_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    command_count: int = 0

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.connected_at

    @property
    def uptime_str(self) -> str:
        secs = int(self.uptime_seconds)
        if secs < 60:
            return f"{secs}s"
        elif secs < 3600:
            return f"{secs // 60}m {secs % 60}s"
        else:
            h = secs // 3600
            m = (secs % 3600) // 60
            return f"{h}h {m}m"

    def is_alive(self) -> bool:
        """Check if the SSH connection is still alive."""
        try:
            if self.client and self.client.get_transport():
                transport = self.client.get_transport()
                if transport and transport.is_active():
                    # Send a keepalive to really verify
                    transport.send_ignore()
                    return True
            return False
        except Exception:
            return False

    def info(self) -> dict:
        """Return session info as a dictionary."""
        return {
            "session_name": self.name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "connected": self.is_alive(),
            "uptime": self.uptime_str,
            "commands_executed": self.command_count,
        }


class SSHManager:
    """
    Manages multiple concurrent SSH sessions.

    Uses CredentialStore for credential management and caching.
    """

    def __init__(self, credential_store: Optional[CredentialStore] = None):
        self._sessions: dict[str, SSHSession] = {}
        self._credentials = credential_store or CredentialStore()

    @property
    def credential_store(self) -> CredentialStore:
        return self._credentials

    @property
    def known_hosts_path(self) -> Path:
        """known_hosts file this server maintains (inside the cache directory)."""
        override = os.environ.get("SSH_KNOWN_HOSTS")
        if override:
            return Path(override).expanduser()
        return self._credentials.cache_dir / "known_hosts"

    @staticmethod
    def host_key_policy() -> str:
        value = os.environ.get("SSH_HOST_KEY_POLICY", "accept-new").strip().lower()
        aliases = {"tofu": "accept-new", "reject": "strict", "auto": "insecure", "auto-add": "insecure"}
        value = aliases.get(value, value)
        return value if value in HOST_KEY_POLICIES else "accept-new"

    def _new_client(self) -> paramiko.SSHClient:
        """Create an SSHClient that verifies host keys according to SSH_HOST_KEY_POLICY."""
        client = paramiko.SSHClient()
        policy = self.host_key_policy()

        if policy == "insecure":
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            return client

        try:
            client.load_system_host_keys()  # ~/.ssh/known_hosts, read-only
        except Exception:
            pass

        known = self.known_hosts_path
        try:
            known.parent.mkdir(parents=True, exist_ok=True)
            if not known.exists():
                known.touch()
                if sys.platform != "win32":
                    os.chmod(known, 0o600)
            # Loading also tells paramiko where to save newly accepted keys.
            client.load_host_keys(str(known))
        except OSError as exc:
            print(f"Warning: could not use known_hosts file {known}: {exc}", file=sys.stderr)

        if policy == "strict":
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def connect(
        self,
        session_name: str = "default",
        host: Optional[str] = None,
        port: int = 22,
        username: str = "root",
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        save_credentials: bool = True,
    ) -> str:
        """
        Connect to a remote host and create a named session.

        If host is not provided, tries to load from credential store.
        Returns a status message.
        """
        # If already connected with this session name, disconnect first
        if session_name in self._sessions and self._sessions[session_name].is_alive():
            self.disconnect(session_name)

        # If no host provided, try to get from credential store
        if not host:
            creds = self._credentials.get_credentials(session_name)
            if creds:
                host = creds.host
                port = creds.port
                username = creds.username
                password = password or creds.password
                key_path = key_path or creds.key_path
            else:
                return (
                    f"❌ No credentials found for session '{session_name}'.\n\n"
                    f"Please provide connection details:\n"
                    f"  • host: Your Linux server IP or hostname\n"
                    f"  • username: SSH username (default: root)\n"
                    f"  • password: SSH password\n"
                    f"  • key_path: Path to SSH private key (alternative to password)\n"
                    f"  • port: SSH port (default: 22)\n"
                    f"  • session_name: Name for this session (default: 'default')\n\n"
                    f"Example: ssh_connect(host='192.168.1.100', username='root', password='mypass')"
                )

        client = self._new_client()

        try:
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": 10,
                "banner_timeout": 15,
                "auth_timeout": 15,
                "allow_agent": False,
                "look_for_keys": False,
            }

            if key_path:
                connect_kwargs["key_filename"] = os.path.expanduser(key_path)
                auth_method = "key"
            elif password:
                connect_kwargs["password"] = password
                auth_method = "password"
            else:
                # Try agent and default keys as fallback
                connect_kwargs["allow_agent"] = True
                connect_kwargs["look_for_keys"] = True
                auth_method = "ssh-agent / default keys"

            client.connect(**connect_kwargs)
            transport = client.get_transport()
            if transport is not None:
                transport.set_keepalive(30)

            # Create session
            session = SSHSession(
                name=session_name,
                host=host,
                port=port,
                username=username,
                client=client,
            )
            self._sessions[session_name] = session

            # Cache credentials for future use
            if save_credentials:
                self._credentials.save_credentials(
                    session_name=session_name,
                    host=host,
                    username=username,
                    password=password,
                    key_path=key_path,
                    port=port,
                )

            print(f"Connected to {host}:{port} as {username} (session: {session_name})", file=sys.stderr)
            lines = [
                "✅ Connected successfully!",
                f"  • Session: {session_name}",
                f"  • Host: {host}:{port}",
                f"  • User: {username}",
                f"  • Auth: {auth_method}",
                f"  • Host key policy: {self.host_key_policy()}",
            ]
            if save_credentials:
                lines.append("  • Credentials cached for future use")
            return "\n".join(lines)

        except paramiko.BadHostKeyException as e:
            client.close()
            return (
                f"❌ HOST KEY MISMATCH for {host}:{port}. The server presented a different key than the one "
                f"recorded earlier ({e.key.get_name()}). This can mean a man-in-the-middle attack, or that the "
                f"server was rebuilt.\nIf the change is expected, remove the old entry for {host} from "
                f"{self.known_hosts_path} (or ~/.ssh/known_hosts) and connect again."
            )
        except paramiko.AuthenticationException:
            client.close()
            return f"❌ Authentication failed for {username}@{host}:{port}. Check your username/password."
        except paramiko.SSHException as e:
            client.close()
            if "not found in known_hosts" in str(e):
                return (
                    f"❌ {host}:{port} is not in known_hosts and SSH_HOST_KEY_POLICY=strict.\n"
                    f"Add its key first, e.g. `ssh-keyscan -p {port} {host} >> {self.known_hosts_path}` "
                    f"(verify the fingerprint out of band), or use SSH_HOST_KEY_POLICY=accept-new."
                )
            return f"❌ SSH error connecting to {host}:{port}: {str(e)}"
        except TimeoutError:
            client.close()
            return f"❌ Connection timed out to {host}:{port}. Check if the host is reachable."
        except Exception as e:
            client.close()
            return f"❌ Failed to connect to {host}:{port}: {str(e)}"

    def disconnect(self, session_name: str = "default") -> str:
        """Disconnect a specific session."""
        if session_name not in self._sessions:
            return f"⚠️ No active session named '{session_name}'."

        session = self._sessions.pop(session_name)
        try:
            session.client.close()
        except Exception:
            pass

        return f"✅ Disconnected session '{session_name}' from {session.host}"

    def disconnect_all(self) -> str:
        """Disconnect all sessions."""
        if not self._sessions:
            return "⚠️ No active sessions to disconnect."

        names = list(self._sessions.keys())
        for name in names:
            self.disconnect(name)

        return f"✅ Disconnected {len(names)} session(s): {', '.join(names)}"

    def _get_session(self, session_name: str = "default") -> tuple[Optional[SSHSession], Optional[str]]:
        """
        Get a session by name, auto-reconnecting if needed.

        Returns (session, error_message). If error_message is set, session is None.
        """
        if session_name not in self._sessions:
            # Try auto-connect from credentials
            creds = self._credentials.get_credentials(session_name)
            if creds:
                result = self.connect(
                    session_name=session_name,
                    host=creds.host,
                    port=creds.port,
                    username=creds.username,
                    password=creds.password,
                    key_path=creds.key_path,
                    save_credentials=False,
                )
                if session_name in self._sessions:
                    return self._sessions[session_name], None
                else:
                    return None, result

            return None, (
                f"❌ No active session '{session_name}'.\n\n"
                f"Please connect first using ssh_connect with your server details:\n"
                f"  ssh_connect(host='your-host', username='your-user', password='your-pass', session_name='{session_name}')\n\n"
                f"Active sessions: {', '.join(self._sessions.keys()) if self._sessions else 'none'}"
            )

        session = self._sessions[session_name]

        # Check if still alive, try reconnect
        if not session.is_alive():
            print(f"Session '{session_name}' dropped, attempting reconnect...", file=sys.stderr)
            creds = self._credentials.get_credentials(session_name)
            if creds:
                result = self.connect(
                    session_name=session_name,
                    host=creds.host,
                    port=creds.port,
                    username=creds.username,
                    password=creds.password,
                    key_path=creds.key_path,
                    save_credentials=False,
                )
                if session_name in self._sessions:
                    return self._sessions[session_name], None
                else:
                    return None, f"❌ Session '{session_name}' dropped and reconnect failed.\n{result}"
            else:
                self._sessions.pop(session_name, None)
                return None, f"❌ Session '{session_name}' dropped and no cached credentials for reconnect."

        return session, None

    def run(
        self,
        command: str,
        session_name: str = "default",
        timeout: int = DEFAULT_TIMEOUT,
        max_output: int = MAX_OUTPUT_SIZE,
        stdin_data: Optional[str] = None,
    ) -> CommandResult:
        """
        Run a command and return a structured result.

        stdout and stderr are drained while the command runs, so large output can
        never stall the remote process, and the timeout is enforced for the whole
        command. Only the first `max_output` bytes of each stream are kept.
        """
        session, error = self._get_session(session_name)
        if error:
            return CommandResult(error=error)

        timeout = min(max(int(timeout), 1), MAX_TIMEOUT)
        channel = None
        try:
            transport = session.client.get_transport()
            if transport is None:
                return CommandResult(error=f"❌ Session '{session_name}' has no active transport.")
            channel = transport.open_session(timeout=10)
            channel.exec_command(command)
            if stdin_data is not None:
                channel.sendall(stdin_data.encode("utf-8"))
                channel.shutdown_write()

            out, err = _Capture(max_output), _Capture(max_output)
            deadline = time.monotonic() + timeout
            timed_out = False
            while True:
                progressed = False
                while channel.recv_ready():
                    out.add(channel.recv(_READ_CHUNK))
                    progressed = True
                while channel.recv_stderr_ready():
                    err.add(channel.recv_stderr(_READ_CHUNK))
                    progressed = True
                if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                    break
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                if not progressed:
                    time.sleep(0.02)

            exit_code = None if timed_out else channel.recv_exit_status()
            session.last_used = time.time()
            session.command_count += 1
            return CommandResult(
                stdout=out.text(),
                stderr=err.text(),
                exit_code=exit_code,
                timed_out=timed_out,
                stdout_bytes=out.total,
                stderr_bytes=err.total,
                stdout_truncated=out.truncated,
                stderr_truncated=err.truncated,
                timeout_seconds=timeout,
            )

        except paramiko.SSHException as e:
            return CommandResult(error=f"❌ SSH error executing command: {str(e)}")
        except Exception as e:
            return CommandResult(error=f"❌ Error executing command: {str(e)}")
        finally:
            if channel is not None:
                try:
                    channel.close()
                except Exception:
                    pass

    def execute(
        self,
        command: str,
        session_name: str = "default",
        timeout: int = DEFAULT_TIMEOUT,
        max_output: int = MAX_OUTPUT_SIZE,
        stdin_data: Optional[str] = None,
    ) -> str:
        """
        Execute a command on a session.

        Returns formatted output with stdout, stderr, and exit code.
        """
        return self.run(command, session_name=session_name, timeout=timeout,
                        max_output=max_output, stdin_data=stdin_data).format()

    def write_file(
        self,
        path: str,
        content: str,
        session_name: str = "default",
        append: bool = False,
    ) -> tuple[bool, str]:
        """Write text to a remote file over SFTP. Returns (ok, message). Content is written byte-for-byte."""
        session, error = self._get_session(session_name)
        if error:
            return False, error
        try:
            sftp = session.client.open_sftp()
            try:
                with sftp.open(path, "a" if append else "w") as handle:
                    handle.write(content.encode("utf-8"))
            finally:
                sftp.close()
            session.last_used = time.time()
            session.command_count += 1
            return True, ""
        except FileNotFoundError:
            return False, f"❌ Cannot write {path}: the parent directory does not exist."
        except PermissionError:
            return False, f"❌ Permission denied writing {path}."
        except Exception as e:
            return False, f"❌ SFTP error writing {path}: {str(e)}"

    def list_sessions(self) -> list[dict]:
        """List all active sessions with their info."""
        sessions = []
        for session in self._sessions.values():
            sessions.append(session.info())
        return sessions

    def get_active_session_names(self) -> list[str]:
        """Get names of all active sessions."""
        return list(self._sessions.keys())

    def is_connected(self, session_name: str = "default") -> bool:
        """Check if a session is connected."""
        if session_name not in self._sessions:
            return False
        return self._sessions[session_name].is_alive()
