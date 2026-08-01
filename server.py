"""
Linux SSH MCP Server — Main Entry Point.

Author: Pawan Gunjkar (pawangunjkar@gamil.com)

A comprehensive MCP server providing 50+ SSH tools across 12 categories
for managing remote Linux machines via AI assistants.

Usage:
    uv run server.py                # Run via stdio (for Cursor/Claude Desktop)
    uv run mcp dev server.py        # Run with MCP Inspector (for testing)
"""

import sys
import os
from mcp.server.fastmcp import FastMCP

from ssh_manager import SSHManager
from credential_store import CredentialStore

# ============================================================
# Initialize MCP Server
# ============================================================

mcp = FastMCP(
    "linux-ssh",
    instructions=(
        "Linux SSH MCP Server — Connect to remote Linux machines via SSH. "
        "Use ssh_connect to establish a session first (or set SSH_HOST/SSH_USERNAME/SSH_PASSWORD env vars). "
        "Supports multiple simultaneous sessions via session_name parameter. "
        "All tools default to session_name='default' if not specified."
    ),
)

# Global SSH manager instance
_credential_store = CredentialStore()
_ssh = SSHManager(credential_store=_credential_store)

# Auto-connect if env vars are set
_env_creds = _credential_store.get_from_env()
if _env_creds:
    print(f"Auto-connecting to {_env_creds.host} from environment variables...", file=sys.stderr)
    _ssh.connect(
        session_name="default",
        host=_env_creds.host,
        port=_env_creds.port,
        username=_env_creds.username,
        password=_env_creds.password,
        key_path=_env_creds.key_path,
    )


# ============================================================
# CATEGORY 1: Session & Authentication (6 tools)
# ============================================================

@mcp.tool()
def ssh_connect(
    host: str,
    username: str = "root",
    password: str = "",
    key_path: str = "",
    port: int = 22,
    session_name: str = "default",
) -> str:
    """
    Connect to a remote Linux host via SSH and create a named session.
    
    If a session with the same name exists, it will be disconnected first.
    Credentials are automatically cached for future reconnection.
    
    Args:
        host: Linux server IP address or hostname
        username: SSH username (default: root)
        password: SSH password (leave empty if using key_path)
        key_path: Path to SSH private key file (alternative to password)
        port: SSH port number (default: 22)
        session_name: Name for this session, e.g. 'prod', 'staging' (default: 'default')
    """
    return _ssh.connect(
        session_name=session_name,
        host=host,
        port=port,
        username=username,
        password=password or None,
        key_path=key_path or None,
    )


@mcp.tool()
def ssh_disconnect(session_name: str = "default") -> str:
    """
    Disconnect a specific SSH session.
    
    Args:
        session_name: Name of the session to disconnect (default: 'default')
    """
    return _ssh.disconnect(session_name)


@mcp.tool()
def ssh_disconnect_all() -> str:
    """Disconnect all active SSH sessions."""
    return _ssh.disconnect_all()


@mcp.tool()
def ssh_list_sessions() -> str:
    """
    List all active SSH sessions with connection details.
    
    Shows session name, host, username, uptime, and command count.
    """
    sessions = _ssh.list_sessions()
    if not sessions:
        return (
            "📡 No active sessions.\n\n"
            "Use ssh_connect to create a session:\n"
            "  ssh_connect(host='your-host', username='root', password='your-pass')"
        )
    
    lines = ["📡 Active SSH Sessions:\n"]
    for s in sessions:
        status = "🟢" if s["connected"] else "🔴"
        lines.append(
            f"  {status} {s['session_name']}: {s['username']}@{s['host']}:{s['port']} "
            f"(uptime: {s['uptime']}, commands: {s['commands_executed']})"
        )
    return "\n".join(lines)


@mcp.tool()
def ssh_save_credentials(
    session_name: str,
    host: str,
    username: str = "root",
    password: str = "",
    key_path: str = "",
    port: int = 22,
) -> str:
    """
    Save SSH credentials for a session name (persisted to disk for future use).
    
    Saved credentials are used for auto-reconnect and future sessions.
    
    Args:
        session_name: Name to save these credentials under
        host: Linux server hostname or IP
        username: SSH username
        password: SSH password (leave empty if using key)
        key_path: Path to SSH private key
        port: SSH port
    """
    _credential_store.save_credentials(
        session_name=session_name,
        host=host,
        username=username,
        password=password or None,
        key_path=key_path or None,
        port=port,
    )
    return f"✅ Credentials saved for session '{session_name}' ({username}@{host}:{port})"


@mcp.tool()
def ssh_list_saved_credentials() -> str:
    """
    List all saved SSH credentials (passwords are masked for security).
    
    Shows credentials from environment variables and cached sessions.
    """
    sessions = _credential_store.list_sessions()
    if not sessions:
        return "📋 No saved credentials found."
    
    lines = ["📋 Saved Credentials:\n"]
    for name, creds in sessions.items():
        lines.append(f"  • {name}: {creds.get('username', '?')}@{creds.get('host', '?')}:{creds.get('port', 22)}")
        if "password" in creds:
            lines.append(f"    Password: {creds['password']}")
        if "key_path" in creds:
            lines.append(f"    Key: {creds['key_path']}")
    return "\n".join(lines)


# ============================================================
# CATEGORY 2: Command Execution (3 tools)
# ============================================================

@mcp.tool()
def ssh_execute(command: str, session_name: str = "default", timeout: int = 30) -> str:
    """
    Execute a shell command on the remote Linux machine.
    
    Returns stdout, stderr, and exit code. Output is truncated if too large.
    
    Args:
        command: Shell command to execute (e.g., 'ls -la /var/log')
        session_name: SSH session to use (default: 'default')
        timeout: Command timeout in seconds (default: 30, max: 300)
    """
    return _ssh.execute(command, session_name=session_name, timeout=timeout)


@mcp.tool()
def ssh_execute_script(script: str, session_name: str = "default", timeout: int = 60) -> str:
    """
    Execute a multi-line bash script on the remote machine.
    
    The script is passed to bash via stdin. Use this for complex operations.
    
    Args:
        script: Multi-line bash script content
        session_name: SSH session to use (default: 'default')
        timeout: Script timeout in seconds (default: 60, max: 300)
    """
    # Escape single quotes in script and wrap in bash -c
    escaped = script.replace("'", "'\\''")
    command = f"bash -c '{escaped}'"
    return _ssh.execute(command, session_name=session_name, timeout=timeout)


@mcp.tool()
def ssh_execute_background(command: str, log_file: str = "", session_name: str = "default") -> str:
    """
    Run a command in the background using nohup.
    
    The command will continue running even after the SSH session ends.
    Output is redirected to a log file.
    
    Args:
        command: Command to run in background
        log_file: Path for output log (default: /tmp/bg_command_<timestamp>.log)
        session_name: SSH session to use (default: 'default')
    """
    if not log_file:
        log_file = f"/tmp/bg_command_$(date +%s).log"
    
    bg_cmd = f"nohup {command} > {log_file} 2>&1 & echo $!"
    result = _ssh.execute(bg_cmd, session_name=session_name, timeout=10)
    
    if result and not result.startswith("❌"):
        pid = result.strip().split("\n")[-1].strip()
        return f"✅ Command started in background\n  PID: {pid}\n  Log: {log_file}\n\nUse ssh_execute('cat {log_file}') to check output."
    return result


# ============================================================
# CATEGORY 3: File & Directory Operations (12 tools)
# ============================================================

@mcp.tool()
def ssh_list_directory(path: str = "/", session_name: str = "default", show_hidden: bool = True) -> str:
    """
    List directory contents with details (permissions, owner, size, date).
    
    Args:
        path: Directory path to list (default: '/')
        session_name: SSH session to use
        show_hidden: Include hidden files (default: True)
    """
    flag = "-la" if show_hidden else "-l"
    return _ssh.execute(f"ls {flag} {path}", session_name=session_name)


@mcp.tool()
def ssh_create_directory(path: str, session_name: str = "default") -> str:
    """
    Create a directory (and parent directories if needed).
    
    Args:
        path: Directory path to create (uses mkdir -p)
        session_name: SSH session to use
    """
    result = _ssh.execute(f"mkdir -p {path} && echo 'Directory created: {path}'", session_name=session_name)
    return result


@mcp.tool()
def ssh_read_file(path: str, session_name: str = "default", max_lines: int = 0) -> str:
    """
    Read the contents of a file on the remote machine.
    
    Args:
        path: Absolute path to the file
        session_name: SSH session to use
        max_lines: Maximum number of lines to read (0 = all lines)
    """
    if max_lines > 0:
        return _ssh.execute(f"head -n {max_lines} {path}", session_name=session_name)
    return _ssh.execute(f"cat {path}", session_name=session_name)


@mcp.tool()
def ssh_write_file(path: str, content: str, session_name: str = "default", append: bool = False) -> str:
    """
    Write content to a file on the remote machine.
    
    Args:
        path: Absolute path to the file
        content: Content to write
        session_name: SSH session to use
        append: If True, append to file instead of overwriting
    """
    operator = ">>" if append else ">"
    # Use heredoc for safe content writing
    escaped_content = content.replace("\\", "\\\\").replace("$", "\\$").replace("`", "\\`")
    command = f'cat {operator} {path} << \'MCPEOF\'\n{content}\nMCPEOF'
    result = _ssh.execute(command, session_name=session_name, timeout=10)
    
    if not result.startswith("❌"):
        action = "Appended to" if append else "Written to"
        return f"✅ {action} {path} ({len(content)} bytes)"
    return result


@mcp.tool()
def ssh_delete(path: str, session_name: str = "default", recursive: bool = False) -> str:
    """
    Delete a file or directory on the remote machine.
    
    Args:
        path: Path to delete
        session_name: SSH session to use
        recursive: If True, delete directories recursively (rm -rf)
    """
    if recursive:
        cmd = f"rm -rf {path} && echo 'Deleted: {path}'"
    else:
        cmd = f"rm -f {path} && echo 'Deleted: {path}'"
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_move(source: str, destination: str, session_name: str = "default") -> str:
    """
    Move or rename a file/directory.
    
    Args:
        source: Source path
        destination: Destination path
        session_name: SSH session to use
    """
    return _ssh.execute(f"mv {source} {destination} && echo 'Moved: {source} → {destination}'", session_name=session_name)


@mcp.tool()
def ssh_copy(source: str, destination: str, session_name: str = "default", recursive: bool = False) -> str:
    """
    Copy a file or directory.
    
    Args:
        source: Source path
        destination: Destination path
        session_name: SSH session to use
        recursive: If True, copy directories recursively
    """
    flag = "-r" if recursive else ""
    return _ssh.execute(f"cp {flag} {source} {destination} && echo 'Copied: {source} → {destination}'", session_name=session_name)


@mcp.tool()
def ssh_file_info(path: str, session_name: str = "default") -> str:
    """
    Get detailed information about a file (size, type, permissions, owner, timestamps).
    
    Args:
        path: Path to the file
        session_name: SSH session to use
    """
    cmd = f"stat {path} 2>/dev/null && echo '---' && file {path} 2>/dev/null"
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_file_permissions(path: str, permissions: str, session_name: str = "default", recursive: bool = False) -> str:
    """
    Change file permissions (chmod).
    
    Args:
        path: Path to file/directory
        permissions: Permission string (e.g., '755', '644', 'u+x')
        session_name: SSH session to use
        recursive: Apply recursively to directories
    """
    flag = "-R" if recursive else ""
    return _ssh.execute(f"chmod {flag} {permissions} {path} && echo 'Permissions set: {path} → {permissions}'", session_name=session_name)


@mcp.tool()
def ssh_change_owner(path: str, owner: str, group: str = "", session_name: str = "default", recursive: bool = False) -> str:
    """
    Change file ownership (chown).
    
    Args:
        path: Path to file/directory
        owner: New owner username
        group: New group name (optional)
        session_name: SSH session to use
        recursive: Apply recursively
    """
    ownership = f"{owner}:{group}" if group else owner
    flag = "-R" if recursive else ""
    return _ssh.execute(f"chown {flag} {ownership} {path} && echo 'Owner changed: {path} → {ownership}'", session_name=session_name)


@mcp.tool()
def ssh_find_files(
    path: str = "/",
    name: str = "",
    file_type: str = "",
    size: str = "",
    modified_within: str = "",
    session_name: str = "default",
) -> str:
    """
    Find files and directories using the 'find' command with filters.
    
    Args:
        path: Base directory to search in
        name: File name pattern (supports wildcards, e.g., '*.log')
        file_type: Type filter — 'f' for files, 'd' for directories, 'l' for symlinks
        size: Size filter (e.g., '+10M' for >10MB, '-1k' for <1KB)
        modified_within: Time filter (e.g., '7' for modified in last 7 days)
        session_name: SSH session to use
    """
    cmd_parts = [f"find {path}"]
    if name:
        cmd_parts.append(f"-name '{name}'")
    if file_type:
        cmd_parts.append(f"-type {file_type}")
    if size:
        cmd_parts.append(f"-size {size}")
    if modified_within:
        cmd_parts.append(f"-mtime -{modified_within}")
    cmd_parts.append("2>/dev/null | head -100")
    
    return _ssh.execute(" ".join(cmd_parts), session_name=session_name)


@mcp.tool()
def ssh_disk_file_usage(path: str, session_name: str = "default") -> str:
    """
    Check disk usage of a file or directory (du -sh).
    
    Args:
        path: Path to check
        session_name: SSH session to use
    """
    return _ssh.execute(f"du -sh {path} 2>/dev/null", session_name=session_name)


# ============================================================
# CATEGORY 4: Log & Search (5 tools)
# ============================================================

@mcp.tool()
def ssh_search_in_files(
    pattern: str,
    path: str = ".",
    session_name: str = "default",
    case_insensitive: bool = False,
    recursive: bool = True,
) -> str:
    """
    Search for a pattern in files using grep.
    
    Args:
        pattern: Search pattern (text or regex)
        path: File or directory to search in
        session_name: SSH session to use
        case_insensitive: Case-insensitive search
        recursive: Search recursively in directories
    """
    flags = "-n"  # Show line numbers
    if case_insensitive:
        flags += "i"
    if recursive:
        flags += "r"
    
    return _ssh.execute(f"grep {flags} '{pattern}' {path} 2>/dev/null | head -100", session_name=session_name)


@mcp.tool()
def ssh_tail_file(path: str, lines: int = 50, session_name: str = "default") -> str:
    """
    Get the last N lines of a file (useful for logs).
    
    Args:
        path: Path to the file
        lines: Number of lines from the end (default: 50)
        session_name: SSH session to use
    """
    return _ssh.execute(f"tail -n {lines} {path}", session_name=session_name)


@mcp.tool()
def ssh_head_file(path: str, lines: int = 50, session_name: str = "default") -> str:
    """
    Get the first N lines of a file.
    
    Args:
        path: Path to the file
        lines: Number of lines from the beginning (default: 50)
        session_name: SSH session to use
    """
    return _ssh.execute(f"head -n {lines} {path}", session_name=session_name)


@mcp.tool()
def ssh_search_logs(
    pattern: str,
    log_path: str = "",
    session_name: str = "default",
    since: str = "",
) -> str:
    """
    Search system logs using journalctl or grep.
    
    Args:
        pattern: Search pattern
        log_path: Specific log file path (if empty, uses journalctl)
        session_name: SSH session to use
        since: Time filter for journalctl (e.g., '1 hour ago', '2024-01-01', 'today')
    """
    if log_path:
        return _ssh.execute(f"grep -n '{pattern}' {log_path} 2>/dev/null | tail -100", session_name=session_name)
    else:
        since_flag = f"--since='{since}'" if since else ""
        return _ssh.execute(
            f"journalctl {since_flag} --no-pager 2>/dev/null | grep '{pattern}' | tail -100",
            session_name=session_name,
        )


@mcp.tool()
def ssh_sed_replace(
    file_path: str,
    find: str,
    replace: str,
    session_name: str = "default",
    backup: bool = True,
) -> str:
    """
    Find and replace text in a file using sed.
    
    Args:
        file_path: Path to the file
        find: Text pattern to find
        replace: Replacement text
        session_name: SSH session to use
        backup: Create a .bak backup before modifying (default: True)
    """
    backup_flag = ".bak" if backup else ""
    # Escape sed special characters
    find_escaped = find.replace("/", "\\/").replace("&", "\\&")
    replace_escaped = replace.replace("/", "\\/").replace("&", "\\&")
    
    cmd = f"sed -i{backup_flag} 's/{find_escaped}/{replace_escaped}/g' {file_path}"
    result = _ssh.execute(cmd, session_name=session_name)
    
    if not result.startswith("❌"):
        return f"✅ Replaced '{find}' with '{replace}' in {file_path}" + (f" (backup: {file_path}.bak)" if backup else "")
    return result


# ============================================================
# CATEGORY 5: System Monitoring (8 tools)
# ============================================================

@mcp.tool()
def ssh_system_info(session_name: str = "default") -> str:
    """
    Get comprehensive system information (OS, kernel, CPU, RAM, uptime, hostname).
    
    Args:
        session_name: SSH session to use
    """
    cmd = """echo "=== HOSTNAME ===" && hostname && \
echo "=== OS ===" && cat /etc/os-release 2>/dev/null | head -5 && \
echo "=== KERNEL ===" && uname -r && \
echo "=== UPTIME ===" && uptime && \
echo "=== CPU ===" && nproc && grep "model name" /proc/cpuinfo 2>/dev/null | head -1 && \
echo "=== MEMORY ===" && free -h | head -3 && \
echo "=== DISK ===" && df -h / | tail -1"""
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_disk_usage(session_name: str = "default") -> str:
    """
    Show disk usage across all mounted filesystems (df -h).
    
    Args:
        session_name: SSH session to use
    """
    return _ssh.execute("df -h", session_name=session_name)


@mcp.tool()
def ssh_memory_usage(session_name: str = "default") -> str:
    """
    Show detailed memory and swap usage.
    
    Args:
        session_name: SSH session to use
    """
    return _ssh.execute("free -h && echo '---' && cat /proc/meminfo | head -10", session_name=session_name)


@mcp.tool()
def ssh_cpu_info(session_name: str = "default") -> str:
    """
    Show CPU information, core count, and current load averages.
    
    Args:
        session_name: SSH session to use
    """
    cmd = """echo "=== CPU Model ===" && grep "model name" /proc/cpuinfo | head -1 && \
echo "=== Cores ===" && nproc && \
echo "=== Load Average ===" && cat /proc/loadavg && \
echo "=== CPU Usage ===" && top -bn1 | head -5"""
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_process_list(session_name: str = "default", filter_pattern: str = "", sort_by: str = "") -> str:
    """
    List running processes with optional filtering and sorting.
    
    Args:
        session_name: SSH session to use
        filter_pattern: Filter processes by name/pattern (grep)
        sort_by: Sort by 'cpu' or 'mem' (default: no sorting)
    """
    if sort_by == "cpu":
        cmd = "ps aux --sort=-%cpu | head -30"
    elif sort_by == "mem":
        cmd = "ps aux --sort=-%mem | head -30"
    else:
        cmd = "ps aux | head -50"
    
    if filter_pattern:
        cmd = f"ps aux | grep -i '{filter_pattern}' | grep -v grep"
    
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_top_processes(session_name: str = "default", count: int = 10, sort_by: str = "cpu") -> str:
    """
    Show top N processes by CPU or memory usage.
    
    Args:
        session_name: SSH session to use
        count: Number of processes to show (default: 10)
        sort_by: Sort by 'cpu' or 'mem' (default: 'cpu')
    """
    sort_field = "-%cpu" if sort_by == "cpu" else "-%mem"
    return _ssh.execute(f"ps aux --sort={sort_field} | head -n {count + 1}", session_name=session_name)


@mcp.tool()
def ssh_kill_process(pid: int, session_name: str = "default", signal: str = "TERM") -> str:
    """
    Kill a process by its PID.
    
    Args:
        pid: Process ID to kill
        session_name: SSH session to use
        signal: Signal to send (default: TERM, options: KILL, HUP, INT, etc.)
    """
    result = _ssh.execute(f"kill -{signal} {pid} 2>&1 && echo 'Process {pid} killed with signal {signal}'", session_name=session_name)
    return result


@mcp.tool()
def ssh_system_load(session_name: str = "default") -> str:
    """
    Show system load averages (1, 5, 15 minutes) and running process count.
    
    Args:
        session_name: SSH session to use
    """
    return _ssh.execute("uptime && echo '---' && cat /proc/loadavg", session_name=session_name)


# ============================================================
# CATEGORY 6: Network (5 tools)
# ============================================================

@mcp.tool()
def ssh_network_info(session_name: str = "default") -> str:
    """
    Show network interfaces, IP addresses, and basic network configuration.
    
    Args:
        session_name: SSH session to use
    """
    cmd = "ip addr show 2>/dev/null || ifconfig 2>/dev/null"
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_open_ports(session_name: str = "default") -> str:
    """
    List all listening (open) ports and the processes using them.
    
    Args:
        session_name: SSH session to use
    """
    return _ssh.execute("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null", session_name=session_name)


@mcp.tool()
def ssh_check_port(host: str, port: int, session_name: str = "default") -> str:
    """
    Test if a specific port is reachable from the remote machine.
    
    Args:
        host: Target hostname or IP
        port: Target port number
        session_name: SSH session to use
    """
    cmd = f"timeout 5 bash -c 'echo >/dev/tcp/{host}/{port}' 2>&1 && echo '✅ Port {port} on {host} is OPEN' || echo '❌ Port {port} on {host} is CLOSED/UNREACHABLE'"
    return _ssh.execute(cmd, session_name=session_name, timeout=10)


@mcp.tool()
def ssh_ping(target: str, count: int = 4, session_name: str = "default") -> str:
    """
    Ping a host from the remote machine.
    
    Args:
        target: Hostname or IP to ping
        count: Number of ping packets (default: 4)
        session_name: SSH session to use
    """
    return _ssh.execute(f"ping -c {count} {target}", session_name=session_name, timeout=30)


@mcp.tool()
def ssh_dns_lookup(domain: str, session_name: str = "default") -> str:
    """
    Perform DNS lookup for a domain.
    
    Args:
        domain: Domain name to look up
        session_name: SSH session to use
    """
    return _ssh.execute(f"dig {domain} +short 2>/dev/null || nslookup {domain} 2>/dev/null || host {domain} 2>/dev/null", session_name=session_name)


# ============================================================
# CATEGORY 7: Docker Operations (7 tools)
# ============================================================

@mcp.tool()
def ssh_docker_ps(session_name: str = "default", all: bool = False) -> str:
    """
    List Docker containers (running or all).
    
    Args:
        session_name: SSH session to use
        all: If True, show all containers including stopped ones
    """
    flag = "-a" if all else ""
    return _ssh.execute(f"docker ps {flag} --format 'table {{{{.ID}}}}\\t{{{{.Names}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Ports}}}}'", session_name=session_name)


@mcp.tool()
def ssh_docker_logs(container: str, session_name: str = "default", lines: int = 100) -> str:
    """
    Get Docker container logs.
    
    Args:
        container: Container name or ID
        session_name: SSH session to use
        lines: Number of log lines to retrieve (default: 100)
    """
    return _ssh.execute(f"docker logs --tail {lines} {container}", session_name=session_name)


@mcp.tool()
def ssh_docker_exec(container: str, command: str, session_name: str = "default") -> str:
    """
    Execute a command inside a running Docker container.
    
    Args:
        container: Container name or ID
        command: Command to execute inside the container
        session_name: SSH session to use
    """
    return _ssh.execute(f"docker exec {container} {command}", session_name=session_name)


@mcp.tool()
def ssh_docker_images(session_name: str = "default") -> str:
    """
    List Docker images on the remote machine.
    
    Args:
        session_name: SSH session to use
    """
    return _ssh.execute("docker images --format 'table {{.Repository}}\\t{{.Tag}}\\t{{.Size}}\\t{{.CreatedSince}}'", session_name=session_name)


@mcp.tool()
def ssh_docker_stats(session_name: str = "default") -> str:
    """
    Show Docker container resource usage statistics (CPU, memory, network).
    
    Args:
        session_name: SSH session to use
    """
    return _ssh.execute("docker stats --no-stream --format 'table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}'", session_name=session_name)


@mcp.tool()
def ssh_docker_compose(action: str, path: str = ".", session_name: str = "default") -> str:
    """
    Run docker compose commands.
    
    Args:
        action: Compose action — 'up', 'down', 'restart', 'ps', 'logs', 'build', 'pull'
        path: Path to the directory containing docker-compose.yml
        session_name: SSH session to use
    """
    valid_actions = ["up", "down", "restart", "ps", "logs", "build", "pull", "stop", "start"]
    if action not in valid_actions:
        return f"❌ Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}"
    
    extra = "-d" if action == "up" else ""
    return _ssh.execute(f"cd {path} && docker compose {action} {extra}", session_name=session_name, timeout=120)


@mcp.tool()
def ssh_docker_inspect(container: str, session_name: str = "default") -> str:
    """
    Inspect a Docker container (detailed configuration and state).
    
    Args:
        container: Container name or ID
        session_name: SSH session to use
    """
    return _ssh.execute(f"docker inspect {container}", session_name=session_name)


# ============================================================
# CATEGORY 8: Package Management (4 tools)
# ============================================================

def _detect_pkg_manager(session_name: str) -> str:
    """Detect the package manager available on the system."""
    result = _ssh.execute(
        "which apt-get 2>/dev/null && echo 'apt' || (which dnf 2>/dev/null && echo 'dnf' || (which yum 2>/dev/null && echo 'yum' || (which pacman 2>/dev/null && echo 'pacman' || echo 'unknown')))",
        session_name=session_name,
        timeout=5,
    )
    for mgr in ["apt", "dnf", "yum", "pacman"]:
        if mgr in result:
            return mgr
    return "unknown"


@mcp.tool()
def ssh_install_package(package: str, session_name: str = "default") -> str:
    """
    Install a package (auto-detects apt/yum/dnf/pacman).
    
    Args:
        package: Package name to install
        session_name: SSH session to use
    """
    mgr = _detect_pkg_manager(session_name)
    commands = {
        "apt": f"DEBIAN_FRONTEND=noninteractive apt-get install -y {package}",
        "dnf": f"dnf install -y {package}",
        "yum": f"yum install -y {package}",
        "pacman": f"pacman -S --noconfirm {package}",
    }
    if mgr not in commands:
        return "❌ Could not detect package manager (apt/dnf/yum/pacman)"
    
    return _ssh.execute(commands[mgr], session_name=session_name, timeout=120)


@mcp.tool()
def ssh_remove_package(package: str, session_name: str = "default") -> str:
    """
    Remove/uninstall a package.
    
    Args:
        package: Package name to remove
        session_name: SSH session to use
    """
    mgr = _detect_pkg_manager(session_name)
    commands = {
        "apt": f"apt-get remove -y {package}",
        "dnf": f"dnf remove -y {package}",
        "yum": f"yum remove -y {package}",
        "pacman": f"pacman -R --noconfirm {package}",
    }
    if mgr not in commands:
        return "❌ Could not detect package manager"
    
    return _ssh.execute(commands[mgr], session_name=session_name, timeout=60)


@mcp.tool()
def ssh_list_packages(filter_pattern: str = "", session_name: str = "default") -> str:
    """
    List installed packages with optional filter.
    
    Args:
        filter_pattern: Filter packages by name pattern
        session_name: SSH session to use
    """
    mgr = _detect_pkg_manager(session_name)
    commands = {
        "apt": "dpkg -l",
        "dnf": "dnf list installed",
        "yum": "yum list installed",
        "pacman": "pacman -Q",
    }
    if mgr not in commands:
        return "❌ Could not detect package manager"
    
    cmd = commands[mgr]
    if filter_pattern:
        cmd += f" | grep -i '{filter_pattern}'"
    else:
        cmd += " | head -50"
    
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_check_updates(session_name: str = "default") -> str:
    """
    Check for available package updates.
    
    Args:
        session_name: SSH session to use
    """
    mgr = _detect_pkg_manager(session_name)
    commands = {
        "apt": "apt list --upgradable 2>/dev/null",
        "dnf": "dnf check-update 2>/dev/null",
        "yum": "yum check-update 2>/dev/null",
        "pacman": "pacman -Qu 2>/dev/null",
    }
    if mgr not in commands:
        return "❌ Could not detect package manager"
    
    return _ssh.execute(commands[mgr], session_name=session_name, timeout=60)


# ============================================================
# CATEGORY 9: User Management (4 tools)
# ============================================================

@mcp.tool()
def ssh_list_users(session_name: str = "default") -> str:
    """
    List system users (human accounts with login shells).
    
    Args:
        session_name: SSH session to use
    """
    cmd = "awk -F: '$3 >= 1000 || $3 == 0 {printf \"%-20s UID=%-6s HOME=%s SHELL=%s\\n\", $1, $3, $6, $7}' /etc/passwd"
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_user_info(username: str, session_name: str = "default") -> str:
    """
    Get detailed information about a specific user.
    
    Args:
        username: Username to look up
        session_name: SSH session to use
    """
    cmd = f"id {username} && echo '---' && grep '^{username}:' /etc/passwd && echo '---' && groups {username}"
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_whoami(session_name: str = "default") -> str:
    """
    Show current user, groups, and environment info.
    
    Args:
        session_name: SSH session to use
    """
    cmd = "echo 'User:' && whoami && echo 'Groups:' && groups && echo 'Home:' && echo $HOME && echo 'Shell:' && echo $SHELL"
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_last_logins(session_name: str = "default", count: int = 20) -> str:
    """
    Show recent login history.
    
    Args:
        session_name: SSH session to use
        count: Number of recent logins to show (default: 20)
    """
    return _ssh.execute(f"last -n {count} 2>/dev/null || last | head -n {count}", session_name=session_name)


# ============================================================
# CATEGORY 10: Cron Jobs (3 tools)
# ============================================================

@mcp.tool()
def ssh_list_cron(user: str = "", session_name: str = "default") -> str:
    """
    List cron jobs for the current or specified user.
    
    Args:
        user: Username (empty = current user)
        session_name: SSH session to use
    """
    if user:
        cmd = f"crontab -l -u {user} 2>/dev/null || echo 'No crontab for {user}'"
    else:
        cmd = "crontab -l 2>/dev/null || echo 'No crontab for current user'"
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_add_cron(schedule: str, command: str, session_name: str = "default") -> str:
    """
    Add a new cron job for the current user.
    
    Args:
        schedule: Cron schedule expression (e.g., '0 2 * * *' for daily at 2am)
        command: Command to run
        session_name: SSH session to use
    """
    cmd = f"(crontab -l 2>/dev/null; echo '{schedule} {command}') | crontab - && echo '✅ Cron job added: {schedule} {command}'"
    return _ssh.execute(cmd, session_name=session_name)


@mcp.tool()
def ssh_remove_cron(pattern: str, session_name: str = "default") -> str:
    """
    Remove cron jobs matching a pattern.
    
    Args:
        pattern: Pattern to match (lines containing this will be removed)
        session_name: SSH session to use
    """
    cmd = f"crontab -l 2>/dev/null | grep -v '{pattern}' | crontab - && echo '✅ Removed cron jobs matching: {pattern}'"
    return _ssh.execute(cmd, session_name=session_name)


# ============================================================
# CATEGORY 11: Archive & Compression (2 tools)
# ============================================================

@mcp.tool()
def ssh_compress(source: str, destination: str = "", session_name: str = "default", format: str = "tar.gz") -> str:
    """
    Compress files or directories into an archive.
    
    Args:
        source: Path to file/directory to compress
        destination: Output archive path (auto-generated if empty)
        session_name: SSH session to use
        format: Archive format — 'tar.gz' (default), 'tar.bz2', 'zip'
    """
    if not destination:
        base = source.rstrip("/").split("/")[-1]
        if format == "zip":
            destination = f"{source}.zip"
        elif format == "tar.bz2":
            destination = f"{source}.tar.bz2"
        else:
            destination = f"{source}.tar.gz"
    
    commands = {
        "tar.gz": f"tar -czf {destination} {source}",
        "tar.bz2": f"tar -cjf {destination} {source}",
        "zip": f"zip -r {destination} {source}",
    }
    
    if format not in commands:
        return f"❌ Unsupported format '{format}'. Use: tar.gz, tar.bz2, zip"
    
    result = _ssh.execute(commands[format], session_name=session_name, timeout=120)
    if not result.startswith("❌"):
        return f"✅ Compressed {source} → {destination}"
    return result


@mcp.tool()
def ssh_extract(archive: str, destination: str = ".", session_name: str = "default") -> str:
    """
    Extract an archive file.
    
    Supports: .tar.gz, .tgz, .tar.bz2, .tar, .zip, .gz, .bz2
    
    Args:
        archive: Path to the archive file
        destination: Directory to extract to (default: current directory)
        session_name: SSH session to use
    """
    if archive.endswith((".tar.gz", ".tgz")):
        cmd = f"tar -xzf {archive} -C {destination}"
    elif archive.endswith(".tar.bz2"):
        cmd = f"tar -xjf {archive} -C {destination}"
    elif archive.endswith(".tar"):
        cmd = f"tar -xf {archive} -C {destination}"
    elif archive.endswith(".zip"):
        cmd = f"unzip -o {archive} -d {destination}"
    elif archive.endswith(".gz"):
        cmd = f"gunzip -k {archive}"
    elif archive.endswith(".bz2"):
        cmd = f"bunzip2 -k {archive}"
    else:
        return f"❌ Unsupported archive format. Supported: .tar.gz, .tgz, .tar.bz2, .tar, .zip, .gz, .bz2"
    
    result = _ssh.execute(cmd, session_name=session_name, timeout=120)
    if not result.startswith("❌"):
        return f"✅ Extracted {archive} → {destination}"
    return result


# ============================================================
# CATEGORY 12: Security & Audit (3 tools)
# ============================================================

@mcp.tool()
def ssh_check_service(service: str, session_name: str = "default") -> str:
    """
    Check the status of a systemd service.
    
    Args:
        service: Service name (e.g., 'nginx', 'docker', 'sshd')
        session_name: SSH session to use
    """
    return _ssh.execute(f"systemctl status {service} 2>/dev/null || service {service} status 2>/dev/null", session_name=session_name)


@mcp.tool()
def ssh_manage_service(service: str, action: str, session_name: str = "default") -> str:
    """
    Manage a systemd service (start, stop, restart, enable, disable).
    
    Args:
        service: Service name (e.g., 'nginx', 'docker')
        action: Action — 'start', 'stop', 'restart', 'enable', 'disable', 'reload'
        session_name: SSH session to use
    """
    valid_actions = ["start", "stop", "restart", "enable", "disable", "reload"]
    if action not in valid_actions:
        return f"❌ Invalid action '{action}'. Valid: {', '.join(valid_actions)}"
    
    return _ssh.execute(f"systemctl {action} {service} && echo '✅ Service {service}: {action} successful'", session_name=session_name)


@mcp.tool()
def ssh_failed_logins(session_name: str = "default", count: int = 30) -> str:
    """
    Show recent failed login attempts (from auth.log or journalctl).
    
    Args:
        session_name: SSH session to use
        count: Number of entries to show (default: 30)
    """
    cmd = f"grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -n {count} || journalctl _COMM=sshd --no-pager 2>/dev/null | grep -i 'failed' | tail -n {count}"
    return _ssh.execute(cmd, session_name=session_name)


# ============================================================
# Entry Point
# ============================================================

def main() -> None:
    """Console entry point for PyPI / uvx installs."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
