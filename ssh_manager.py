"""
Multi-Session SSH Manager for Linux SSH MCP Server.

Author: Pawan Gunjkar (pawangunjkar@gamil.com)

Manages multiple concurrent SSH connections using paramiko.
Each connection is identified by a session name (e.g., "default", "prod", "staging").
Supports auto-reconnect, command timeouts, and output truncation.
"""

import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import paramiko

from credential_store import CredentialStore, SSHCredentials


# Maximum output size in bytes (50KB default)
MAX_OUTPUT_SIZE = 50 * 1024
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 300


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

        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": 10,
                "allow_agent": False,
                "look_for_keys": False,
            }

            if key_path:
                connect_kwargs["key_filename"] = key_path
                connect_kwargs["look_for_keys"] = True
            elif password:
                connect_kwargs["password"] = password
            else:
                # Try agent and default keys as fallback
                connect_kwargs["allow_agent"] = True
                connect_kwargs["look_for_keys"] = True

            client.connect(**connect_kwargs)

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
            return (
                f"✅ Connected successfully!\n"
                f"  • Session: {session_name}\n"
                f"  • Host: {host}:{port}\n"
                f"  • User: {username}\n"
                f"  • Auth: {'key' if key_path else 'password'}\n"
                f"  • Credentials cached for future use"
            )

        except paramiko.AuthenticationException:
            return f"❌ Authentication failed for {username}@{host}:{port}. Check your username/password."
        except paramiko.SSHException as e:
            return f"❌ SSH error connecting to {host}:{port}: {str(e)}"
        except TimeoutError:
            return f"❌ Connection timed out to {host}:{port}. Check if the host is reachable."
        except Exception as e:
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

    def execute(
        self,
        command: str,
        session_name: str = "default",
        timeout: int = DEFAULT_TIMEOUT,
        max_output: int = MAX_OUTPUT_SIZE,
    ) -> str:
        """
        Execute a command on a session.
        
        Returns formatted output with stdout, stderr, and exit code.
        """
        session, error = self._get_session(session_name)
        if error:
            return error

        # Clamp timeout
        timeout = min(max(timeout, 1), MAX_TIMEOUT)

        try:
            stdin, stdout, stderr = session.client.exec_command(command, timeout=timeout)
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read()
            stderr_data = stderr.read()

            session.last_used = time.time()
            session.command_count += 1

            # Decode output
            out = stdout_data.decode("utf-8", errors="replace")
            err = stderr_data.decode("utf-8", errors="replace")

            # Truncate if too large
            truncated = False
            if len(out) > max_output:
                out = out[:max_output] + f"\n\n... [OUTPUT TRUNCATED — {len(stdout_data)} bytes total, showing first {max_output} bytes]"
                truncated = True
            if len(err) > max_output:
                err = err[:max_output] + f"\n\n... [STDERR TRUNCATED — {len(stderr_data)} bytes total, showing first {max_output} bytes]"
                truncated = True

            # Format result
            parts = []
            if out.strip():
                parts.append(out.strip())
            if err.strip():
                parts.append(f"[STDERR]\n{err.strip()}")
            if exit_code != 0:
                parts.append(f"[EXIT CODE: {exit_code}]")

            result = "\n\n".join(parts) if parts else "(no output)"
            return result

        except paramiko.SSHException as e:
            return f"❌ SSH error executing command: {str(e)}"
        except TimeoutError:
            return f"❌ Command timed out after {timeout}s: {command}"
        except Exception as e:
            return f"❌ Error executing command: {str(e)}"

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
