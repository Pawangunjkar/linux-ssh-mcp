# Changelog

## [Unreleased]

### Security
- **Host keys are now verified.** The default policy `accept-new` trusts a host on first connection, saves its key
  to `<cache dir>/known_hosts`, and refuses to connect if the key later changes. `SSH_HOST_KEY_POLICY=strict`
  allows only known hosts; `insecure` restores the old no-verification behaviour. `~/.ssh/known_hosts` is honoured.
- **Shell injection fixed in every tool.** Paths and free-text values are shell-quoted; names (containers,
  packages, users, services, hosts, signals, permissions, cron schedules, find filters) are validated. Paths that
  start with `-` cannot be read as options.
- `ssh_delete` refuses system paths such as `/`, `/etc`, `/usr`; `ssh_kill_process` refuses PID 0/1;
  `ssh_remove_cron` refuses an empty pattern (which would delete every job).
- Saved passwords are never displayed, not even the last characters.

### Fixed
- **Commands with large output could hang forever and ignored the timeout.** Output is drained while the command
  runs, memory is bounded, and the timeout stops the command and returns partial output.
- Tools that reported success after a failed command (create directory, move, copy, chmod, chown, sed, compress,
  extract, cron, services) now return the error and exit code.
- `ssh_write_file` uses SFTP, so any content (including the old `MCPEOF` marker) is written byte-for-byte.
- `ssh_execute_script` really sends the script on stdin (`bash -s`).
- `ssh_execute_background` shows the real log path instead of a literal `$(date +%s)`.
- `ssh_failed_logins` falls back to `/var/log/secure` and journalctl correctly.
- `ssh_sed_replace` matches literal text by default (new `use_regex` option for regular expressions).
- `ssh_process_list` keeps sorting when filtering; package-manager detection is more reliable.
- The connect message reports the real auth method and only says credentials were cached when they were.

### Added
- `SSH_HOST_KEY_POLICY` and `SSH_KNOWN_HOSTS` settings (documented in `.env.example` and `mcpize.yaml`).
- `tests/test_ssh_bugfixes.py`: 22 regression tests (command quoting, guards, output reader, host-key policy).
