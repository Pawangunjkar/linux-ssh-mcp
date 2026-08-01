# 🐧 Linux SSH MCP Server

> A powerful Python-based **Model Context Protocol (MCP)** server that enables AI assistants to manage remote Linux machines over SSH — directly from your chat interface.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Configuring Your AI IDE](#-configuring-your-ai-ide)
  - [Cursor](#1--cursor)
  - [Claude Desktop](#2--claude-desktop)
  - [Antigravity (Google DeepMind)](#3--antigravity-google-deepmind)
  - [VS Code with Continue / Cline](#4--vs-code-with-continue--cline)
  - [Windsurf](#5--windsurf)
- [How It Works](#-how-it-works)
- [Environment Variables](#-environment-variables)
- [Complete Tool Reference](#-complete-tool-reference)
  - [Session & Authentication (6 tools)](#category-1-session--authentication-6-tools)
  - [Command Execution (3 tools)](#category-2-command-execution-3-tools)
  - [File & Directory Operations (12 tools)](#category-3-file--directory-operations-12-tools)
  - [Log & Search (5 tools)](#category-4-log--search-5-tools)
  - [System Monitoring (8 tools)](#category-5-system-monitoring-8-tools)
  - [Network (5 tools)](#category-6-network-5-tools)
  - [Docker Operations (7 tools)](#category-7-docker-operations-7-tools)
  - [Package Management (4 tools)](#category-8-package-management-4-tools)
  - [User Management (4 tools)](#category-9-user-management-4-tools)
  - [Cron Jobs (3 tools)](#category-10-cron-jobs-3-tools)
  - [Archive & Compression (2 tools)](#category-11-archive--compression-2-tools)
  - [Security & Audit (3 tools)](#category-12-security--audit-3-tools)
- [Multi-Session Usage Examples](#-multi-session-usage-examples)
- [Security Best Practices](#-security-best-practices)
- [Troubleshooting](#-troubleshooting)
- [Author & Contact](#-author--contact)
- [License](#-license)

---

## 🌐 Overview

**Linux SSH MCP Server** is a Python application built with [FastMCP](https://github.com/jlowin/fastmcp) and [Paramiko](https://www.paramiko.org/) that exposes **50+ tools across 12 categories** to any MCP-compatible AI assistant. Once connected, your AI can execute commands, manage files, monitor systems, control Docker containers, and much more — all on remote Linux servers, all through natural language in your chat.

### How is this different from just "running commands"?

Traditional AI code assistants can run commands on your *local* machine. This MCP server lets them operate on **remote Linux servers** — your production boxes, staging environments, cloud VMs, Raspberry Pis, or any machine reachable via SSH. The AI gets structured, typed tools (not raw shell access), meaning it can reason about parameters, handle errors gracefully, and chain operations intelligently.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **50+ Specialized Tools** | Purpose-built tools across 12 categories — not just raw command execution |
| **Multi-Session Support** | Connect to multiple Linux hosts simultaneously with named sessions |
| **Interactive Credentials** | If environment variables aren't set, the server prompts for credentials directly in the chat |
| **Credential Caching** | Saves credentials in memory and optionally to `~/.ssh-mcp-cache/credentials.json` for reuse |
| **SSH Key Authentication** | Supports password auth, key-based auth, or both |
| **Auto-Detection** | Automatically detects package managers (apt/yum/dnf/pacman) and adjusts commands |
| **stdio Transport** | Runs via stdio using `uv`, the standard transport for MCP servers in AI IDEs |
| **Zero Config Start** | Works with environment variables, saved credentials, or interactive prompting — your choice |

---

## 📥 Quick Install

### Option 1: PyPI / uvx (Recommended)

```bash
uvx pawangunjkar-linux-ssh-mcp
```

**Cursor / Claude Desktop** — add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uvx",
      "args": ["pawangunjkar-linux-ssh-mcp"],
      "env": {
        "SSH_HOST": "your-host",
        "SSH_PORT": "22",
        "SSH_USERNAME": "ubuntu",
        "SSH_KEY_PATH": "/home/user/.ssh/id_rsa"
      }
    }
  }
}
```

### Option 2: Smithery

```bash
npx -y @smithery/cli install linux-ssh-mcp --client cursor
```

### Option 3: Clone from GitHub

```bash
git clone https://github.com/Pawangunjkar/linux-ssh-mcp.git
cd linux-ssh-mcp
uv sync
uv run server.py
```

> See [PUBLISHING.md](PUBLISHING.md) for PyPI, Smithery, and directory submission steps.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AI IDE (Client)                     │
│          Cursor / Claude Desktop / Antigravity          │
│                  VS Code / Windsurf                     │
└──────────────────────┬──────────────────────────────────┘
                       │  stdio (stdin/stdout)
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  MCP Server (server.py)                 │
│               Built with FastMCP + Python               │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Session     │  │  Credential  │  │  Tool         │  │
│  │  Manager     │  │  Cache       │  │  Registry     │  │
│  │  (multi-host)│  │  (mem+disk)  │  │  (50+ tools)  │  │
│  └──────┬──────┘  └──────────────┘  └───────────────┘  │
└─────────┼───────────────────────────────────────────────┘
          │  SSH (Paramiko)
          │
┌─────────▼───────────────────────────────────────────────┐
│              Remote Linux Server(s)                     │
│         Ubuntu / Debian / CentOS / Arch / etc.          │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

Before you begin, make sure you have the following installed on your **local machine** (the machine running the AI IDE):

### 1. Python 3.10 or higher

Verify your Python version:

```powershell
python --version
# Should output: Python 3.10.x or higher
```

If you don't have Python 3.10+, download it from [python.org](https://www.python.org/downloads/).

### 2. uv (Python Package Manager by Astral)

`uv` is a blazing-fast Python package manager that replaces pip, venv, and more. Install it:

```powershell
# Using pip
pip install uv

# Or using the standalone installer (recommended)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify the installation:

```powershell
uv --version
```

> **Why uv?** MCP servers launched by AI IDEs use `uv run` to automatically create virtual environments, install dependencies, and start the server — all in one command. It's the de facto standard for MCP server management.

### 3. A Remote Linux Server with SSH Access

You need at least one Linux machine you can SSH into. This can be:

- A cloud VM (AWS EC2, GCP, Azure, DigitalOcean, etc.)
- A local VM (VirtualBox, VMware, WSL2, etc.)
- A Raspberry Pi or any other Linux device
- A container with SSH enabled

Make sure you have:
- The server's **hostname or IP address**
- A valid **username** and **password** (or SSH private key)
- **SSH port** (default: `22`) is open and accessible from your machine

---

## 🚀 Installation & Setup

### Step 1: Navigate to the project directory

```powershell
cd C:\AI_Workspaces\Anti_Workspace\linux-ssh-mcp
```

### Step 2: Install dependencies

You can set up the project using either `uv` (recommended) or the standard Python tools.

#### Option A: Using `uv` (Recommended)

```powershell
uv sync
```

This single command will:
1. Create a virtual environment (`.venv/`) if one doesn't exist
2. Read `pyproject.toml` for dependency declarations
3. Install all required packages (FastMCP, Paramiko, etc.)
4. Lock dependency versions in `uv.lock`

#### Option B: Using Standard Python `venv` & `pip`

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (CMD):
.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate

# 3. Install the package in editable mode (reads pyproject.toml)
pip install -e .
```

### Step 3: Verify the installation

#### If using `uv`:
```powershell
uv run python -c "import mcp; import paramiko; print('All dependencies installed successfully!')"
```

#### If using standard `venv` (make sure the virtual environment is activated):
```powershell
python -c "import mcp; import paramiko; print('All dependencies installed successfully!')"
```

### Step 4 (Optional): Test with MCP Inspector

The MCP Inspector is a browser-based debugging tool that lets you test your server's tools interactively:

```powershell
uv run mcp dev server.py
```

This opens a web UI where you can invoke any tool, inspect inputs/outputs, and debug issues before connecting to your AI IDE.

---

## 🔌 Configuring Your AI IDE

Each AI IDE reads MCP server configurations from a JSON file. The server is launched automatically when the IDE starts — you do **not** need to start it manually.

### Understanding the Configuration

Every IDE uses the same core JSON structure:

**Recommended (PyPI / uvx — no clone required):**

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uvx",
      "args": ["pawangunjkar-linux-ssh-mcp"],
      "env": {
        "SSH_HOST": "your-host",
        "SSH_PORT": "22",
        "SSH_USERNAME": "your-username",
        "SSH_KEY_PATH": "/path/to/private/key"
      }
    }
  }
}
```

**Alternative (from source):**

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/linux-ssh-mcp", "server.py"],
      "env": {
        "SSH_HOST": "your-host",
        "SSH_PORT": "22",
        "SSH_USERNAME": "your-username",
        "SSH_PASSWORD": "your-password"
      }
    }
  }
}
```

| Field | Purpose |
|---|---|
| `"linux-ssh"` | A unique name for this MCP server (you can change it) |
| `"command"` | `uvx` (PyPI) or `uv` (from source) |
| `"args"` | Package name (`pawangunjkar-linux-ssh-mcp`) or source path + `server.py` |
| `"env"` | **OPTIONAL** — Environment variables for default SSH credentials |

> **💡 The `env` section is entirely optional.** If you omit it, the server will interactively ask for credentials in the chat when you first try to connect. This is the recommended approach for security-sensitive environments.

---

### 1. 🖱 Cursor

Cursor supports both **project-level** and **global** MCP configurations.

#### Project-Level Configuration (Recommended)

Create the file `.cursor/mcp.json` in your project root:

```
your-project/
├── .cursor/
│   └── mcp.json        ← Create this file
├── src/
└── ...
```

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\AI_Workspaces\\Anti_Workspace\\linux-ssh-mcp",
        "server.py"
      ],
      "env": {
        "SSH_HOST": "your-host",
        "SSH_PORT": "22",
        "SSH_USERNAME": "your-username",
        "SSH_PASSWORD": "your-password"
      }
    }
  }
}
```

#### Global Configuration

To make the MCP server available across **all** Cursor projects, add it to your global configuration:

```
~/.cursor/mcp.json
```

The JSON format is identical to the project-level config above.

#### Without Environment Variables (Interactive Mode)

If you prefer the server to ask for credentials in the chat:

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\AI_Workspaces\\Anti_Workspace\\linux-ssh-mcp",
        "server.py"
      ]
    }
  }
}
```

#### Verifying in Cursor

1. Open Cursor
2. Go to **Settings** → **MCP** (or press `Ctrl+Shift+P` → "MCP")
3. You should see `linux-ssh` listed with a green status indicator
4. If red, check the logs for error details

---

### 2. 🤖 Claude Desktop

#### Configuration File Location

| OS | Path |
|---|---|
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |

#### Configuration

Open (or create) the config file and add the MCP server:

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\AI_Workspaces\\Anti_Workspace\\linux-ssh-mcp",
        "server.py"
      ]
    }
  }
}
```

> **Note for macOS users:** Replace the Windows path in `--directory` with the equivalent macOS path where the project is located.

#### Verifying in Claude Desktop

1. Restart Claude Desktop after saving the config
2. Look for the 🔧 (tools) icon in the chat input area
3. Click it to see the list of available tools from `linux-ssh`

---

### 3. 🌀 Antigravity (Google DeepMind)

Antigravity can be configured via the **MCP settings panel** within the application.

#### Configuration

Use the same JSON format as Cursor:

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\AI_Workspaces\\Anti_Workspace\\linux-ssh-mcp",
        "server.py"
      ],
      "env": {
        "SSH_HOST": "your-host",
        "SSH_USERNAME": "your-username",
        "SSH_PASSWORD": "your-password"
      }
    }
  }
}
```

#### Steps

1. Open Antigravity
2. Navigate to the **MCP settings** panel
3. Add a new MCP server configuration
4. Paste the JSON above (adjust credentials as needed)
5. Save and restart if prompted

---

### 4. 💻 VS Code with Continue / Cline

#### Continue Extension

Add the MCP server to `.continue/config.json` in your project or home directory:

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\AI_Workspaces\\Anti_Workspace\\linux-ssh-mcp",
        "server.py"
      ]
    }
  }
}
```

#### Cline Extension

1. Open VS Code
2. Open Cline's settings (click the gear icon in the Cline sidebar)
3. Navigate to the **MCP Servers** section
4. Add a new server with the same `command` and `args` format

---

### 5. 🏄 Windsurf

#### Configuration File Location

```
~/.codeium/windsurf/mcp_config.json
```

#### Configuration

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\AI_Workspaces\\Anti_Workspace\\linux-ssh-mcp",
        "server.py"
      ],
      "env": {
        "SSH_HOST": "your-host",
        "SSH_USERNAME": "your-username",
        "SSH_PASSWORD": "your-password"
      }
    }
  }
}
```

#### Steps

1. Open (or create) the file at `~/.codeium/windsurf/mcp_config.json`
2. Add the configuration above
3. Restart Windsurf to pick up the changes

---

## ⚡ How It Works

### Startup Flow

```
1. AI IDE starts
        │
2. Reads mcp.json / config file
        │
3. Runs: uv run --directory <path> server.py
        │
4. uv automatically:
   ├── Creates .venv if needed
   ├── Installs dependencies from pyproject.toml
   └── Launches server.py
        │
5. server.py initializes FastMCP
   ├── Registers all 50+ tools
   ├── Reads SSH_* environment variables (if set)
   └── Loads cached credentials (if available)
        │
6. Server communicates via stdio (stdin/stdout)
        │
7. AI IDE discovers tools and makes them available in chat
```

### Connection Flow

```
User: "Connect to my production server at 10.0.1.50"
        │
AI calls: ssh_connect(host='10.0.1.50')
        │
        ├── ENV vars set? → Uses SSH_USERNAME / SSH_PASSWORD
        ├── Cached creds? → Uses saved credentials
        └── Neither?      → Prompts user in chat for username/password
                │
        SSH connection established → Session "default" created
        │
User: "Show me disk usage"
        │
AI calls: ssh_disk_usage(session_name='default')
        │
Returns: Formatted df -h output
```

### For Manual Testing / Debugging

```powershell
# Open the MCP Inspector (browser-based tool debugger)
uv run mcp dev server.py
```

The Inspector lets you:
- See all registered tools and their schemas
- Invoke tools with custom parameters
- Inspect raw JSON responses
- Debug connection issues

---

## 🔐 Environment Variables

All environment variables are **optional**. If not set, the server will either use defaults or prompt interactively.

| Variable | Required | Default | Description |
|:---|:---:|:---:|:---|
| `SSH_HOST` | No | — | Hostname or IP address of the remote Linux server. If not set, you must provide it when calling `ssh_connect`. |
| `SSH_PORT` | No | `22` | SSH port number. Only change this if your server uses a non-standard SSH port. |
| `SSH_USERNAME` | No | `root` | SSH username for authentication. |
| `SSH_PASSWORD` | No | — | SSH password for password-based authentication. Mutually optional with `SSH_KEY_PATH`. |
| `SSH_KEY_PATH` | No | — | Absolute path to an SSH private key file (e.g., `C:\Users\pawan\.ssh\id_rsa`). Used for key-based authentication. |
| `SSH_MCP_CACHE_DIR` | No | `~/.ssh-mcp-cache` | Directory where credential cache files are stored. The server creates this directory automatically if it doesn't exist. |

### Authentication Priority

When connecting, the server checks for credentials in this order:

1. **Explicit parameters** passed to `ssh_connect` (highest priority)
2. **Environment variables** (`SSH_HOST`, `SSH_USERNAME`, etc.)
3. **Cached credentials** from `~/.ssh-mcp-cache/credentials.json`
4. **Interactive prompt** — asks the user in chat (lowest priority / fallback)

---

## 📖 Complete Tool Reference

This section documents every tool exposed by the MCP server. All tools return structured responses with clear success/error indicators.

---

### Category 1: Session & Authentication (6 tools)

These tools manage SSH connections, sessions, and credential storage.

---

#### 🔧 `ssh_connect`

**Connect to a remote Linux host and create a named session.**

Establishes an SSH connection to the specified host. Multiple simultaneous connections are supported via named sessions. If credentials are not provided as parameters, the server falls back to environment variables, then cached credentials, then interactive prompting.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `host` | `str` | Yes* | — | Hostname or IP address of the remote server. *Optional if `SSH_HOST` env var is set. |
| `username` | `str` | No | `'root'` | SSH username. |
| `password` | `str` | No | — | SSH password. Either `password` or `key_path` should be provided. |
| `key_path` | `str` | No | — | Path to SSH private key file. |
| `port` | `int` | No | `22` | SSH port number. |
| `session_name` | `str` | No | `'default'` | A unique name for this session. Use different names to manage multiple connections. |

**Examples:**

```python
# Basic connection with password
ssh_connect(host='192.168.1.100', username='admin', password='s3cret')

# Connection with SSH key
ssh_connect(host='10.0.1.50', username='deploy', key_path='/home/user/.ssh/id_rsa')

# Named session for production server
ssh_connect(host='prod.example.com', username='admin', password='s3cret', session_name='prod')

# Named session for staging server (simultaneously)
ssh_connect(host='staging.example.com', username='admin', password='s3cret', session_name='staging')

# Using non-standard port
ssh_connect(host='bastion.example.com', port=2222, username='jump', key_path='/keys/bastion.pem')
```

**Returns:** Confirmation message with session name, connected host, and server OS info.

---

#### 🔧 `ssh_disconnect`

**Disconnect a specific SSH session.**

Gracefully closes the SSH connection for the named session and frees associated resources.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Name of the session to disconnect. |

**Examples:**

```python
# Disconnect the default session
ssh_disconnect()

# Disconnect a named session
ssh_disconnect(session_name='prod')
```

**Returns:** Confirmation that the session was disconnected.

---

#### 🔧 `ssh_disconnect_all`

**Disconnect all active SSH sessions.**

Iterates through all active sessions and disconnects each one. Useful for cleanup.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| *(none)* | — | — | — | This tool takes no parameters. |

**Example:**

```python
ssh_disconnect_all()
```

**Returns:** Summary of how many sessions were disconnected and their names.

---

#### 🔧 `ssh_list_sessions`

**List all active SSH sessions with connection details.**

Provides a comprehensive overview of all currently active sessions including connection status, hostname, uptime, and the number of commands executed in each session.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| *(none)* | — | — | — | This tool takes no parameters. |

**Example:**

```python
ssh_list_sessions()
```

**Returns:** A formatted table/list with:
- Session name
- Connected host and port
- Username
- Connection status (active/disconnected)
- Uptime (how long the session has been active)
- Number of commands executed

---

#### 🔧 `ssh_save_credentials`

**Save SSH credentials for future reuse.**

Persists credentials to disk at `~/.ssh-mcp-cache/credentials.json`. Saved credentials are automatically loaded on server startup and can be used when connecting to a host without explicitly providing credentials. The credential file is created with restricted permissions (600) for security.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Name to identify these saved credentials. |
| `host` | `str` | Yes | — | Hostname or IP address. |
| `username` | `str` | No | `'root'` | SSH username. |
| `password` | `str` | No | — | SSH password. |
| `key_path` | `str` | No | — | Path to SSH private key. |
| `port` | `int` | No | `22` | SSH port number. |

**Example:**

```python
ssh_save_credentials(
    session_name='prod',
    host='prod.example.com',
    username='deploy',
    key_path='/home/user/.ssh/prod_key',
    port=22
)
```

**Returns:** Confirmation that credentials were saved and the file path.

---

#### 🔧 `ssh_list_saved_credentials`

**List all saved credentials.**

Displays all credentials stored in the cache file. **Passwords are masked** for security (only the first and last characters are shown).

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| *(none)* | — | — | — | This tool takes no parameters. |

**Example:**

```python
ssh_list_saved_credentials()
```

**Returns:** A formatted list of saved credentials with:
- Session/credential name
- Host and port
- Username
- Password (masked, e.g., `s****t`)
- Key path (if set)

---

### Category 2: Command Execution (3 tools)

General-purpose command execution tools for running anything on the remote host.

---

#### 🔧 `ssh_execute`

**Execute any shell command on the remote host.**

The most versatile tool — runs a single shell command and returns stdout, stderr, and the exit code. Use this for any command not covered by a specialized tool.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `command` | `str` | Yes | — | The shell command to execute. |
| `session_name` | `str` | No | `'default'` | Session to execute on. |
| `timeout` | `int` | No | `30` | Maximum execution time in seconds. |

**Examples:**

```python
# Simple command
ssh_execute(command='whoami')

# Command with timeout
ssh_execute(command='find / -name "*.log" -size +100M', timeout=120)

# Execute on a specific session
ssh_execute(command='uptime', session_name='prod')

# Piped commands
ssh_execute(command='cat /var/log/syslog | grep ERROR | tail -20')
```

**Returns:** An object containing:
- `stdout` — Standard output of the command
- `stderr` — Standard error output (if any)
- `exit_code` — Exit code (0 = success)

---

#### 🔧 `ssh_execute_script`

**Execute a multi-line bash script on the remote host.**

Uploads and runs a complete bash script. Useful for complex operations that span multiple commands with control flow (if/else, loops, etc.).

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `script` | `str` | Yes | — | Multi-line bash script content. |
| `session_name` | `str` | No | `'default'` | Session to execute on. |
| `timeout` | `int` | No | `30` | Maximum execution time in seconds. |

**Example:**

```python
ssh_execute_script(script="""
#!/bin/bash
set -e

echo "=== System Health Check ==="
echo ""
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo "Kernel: $(uname -r)"
echo ""
echo "=== Disk Usage ==="
df -h | grep -E '^/dev'
echo ""
echo "=== Memory ==="
free -h
echo ""
echo "=== Top 5 CPU Processes ==="
ps aux --sort=-%cpu | head -6
""", timeout=60)
```

**Returns:** Combined output from the script execution with exit code.

---

#### 🔧 `ssh_execute_background`

**Run a command in the background using `nohup`.**

Launches a long-running command that persists even after the SSH session ends. Output is redirected to a log file.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `command` | `str` | Yes | — | The command to run in the background. |
| `log_file` | `str` | No | `/tmp/bg_<timestamp>.log` | Path to redirect stdout/stderr. |
| `session_name` | `str` | No | `'default'` | Session to execute on. |

**Examples:**

```python
# Run a backup in the background
ssh_execute_background(
    command='tar czf /backups/full-backup-$(date +%Y%m%d).tar.gz /var/www',
    log_file='/var/log/backup.log'
)

# Start a long-running data processing job
ssh_execute_background(command='python3 /scripts/process_data.py --all')
```

**Returns:** Confirmation with the PID of the background process and the log file path.

---

### Category 3: File & Directory Operations (12 tools)

Comprehensive file management capabilities — browse, read, write, copy, move, delete, search, and manage permissions.

---

#### 🔧 `ssh_list_directory`

**List the contents of a directory (equivalent to `ls -la`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | No | `'/'` | Directory path to list. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `show_hidden` | `bool` | No | `True` | Whether to include hidden files (dotfiles). |

**Examples:**

```python
# List root directory
ssh_list_directory(path='/')

# List home directory without hidden files
ssh_list_directory(path='/home/admin', show_hidden=False)

# List on a specific session
ssh_list_directory(path='/var/www', session_name='prod')
```

**Returns:** Formatted directory listing with permissions, owner, group, size, modification date, and filename.

---

#### 🔧 `ssh_create_directory`

**Create a directory, including any necessary parent directories (equivalent to `mkdir -p`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | Directory path to create. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
# Creates /var/www/myapp/static/images and all parents
ssh_create_directory(path='/var/www/myapp/static/images')
```

---

#### 🔧 `ssh_read_file`

**Read the contents of a file on the remote server.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | File path to read. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `max_lines` | `int` | No | — | Maximum number of lines to read. If omitted, reads the entire file. |

**Examples:**

```python
# Read entire file
ssh_read_file(path='/etc/nginx/nginx.conf')

# Read first 50 lines of a large file
ssh_read_file(path='/var/log/syslog', max_lines=50)
```

---

#### 🔧 `ssh_write_file`

**Write content to a file. Creates the file if it doesn't exist, or overwrites/appends to it.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | File path to write to. |
| `content` | `str` | Yes | — | Content to write. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `append` | `bool` | No | `False` | If `True`, appends to the file instead of overwriting. |

**Examples:**

```python
# Write a new config file
ssh_write_file(path='/etc/myapp/config.yml', content="""
database:
  host: localhost
  port: 5432
  name: myapp_prod
""")

# Append a line to a file
ssh_write_file(path='/etc/hosts', content='10.0.1.50 api.internal\n', append=True)
```

---

#### 🔧 `ssh_delete`

**Delete a file or directory.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | Path to delete. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `recursive` | `bool` | No | `False` | If `True`, deletes directories recursively (`rm -rf`). Required for non-empty directories. |

**Examples:**

```python
# Delete a single file
ssh_delete(path='/tmp/old-backup.tar.gz')

# Delete a directory and all its contents
ssh_delete(path='/var/www/old-site', recursive=True)
```

> ⚠️ **Warning:** Recursive delete is permanent. There is no recycle bin on Linux.

---

#### 🔧 `ssh_move`

**Move or rename a file or directory.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `source` | `str` | Yes | — | Source path. |
| `destination` | `str` | Yes | — | Destination path. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
# Rename a file
ssh_move(source='/var/www/index.html', destination='/var/www/index.html.bak')

# Move a directory
ssh_move(source='/tmp/release-v2', destination='/var/www/app')
```

---

#### 🔧 `ssh_copy`

**Copy a file or directory.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `source` | `str` | Yes | — | Source path. |
| `destination` | `str` | Yes | — | Destination path. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `recursive` | `bool` | No | `False` | If `True`, copies directories recursively (`cp -r`). |

**Example:**

```python
# Copy a file
ssh_copy(source='/etc/nginx/nginx.conf', destination='/etc/nginx/nginx.conf.bak')

# Copy a directory
ssh_copy(source='/var/www/app', destination='/var/www/app-backup', recursive=True)
```

---

#### 🔧 `ssh_file_info`

**Get detailed information about a file or directory (equivalent to `stat`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | Path to inspect. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_file_info(path='/var/log/syslog')
```

**Returns:** File type, size, permissions, owner, group, creation time, modification time, access time, inode, and link count.

---

#### 🔧 `ssh_file_permissions`

**Change file or directory permissions (equivalent to `chmod`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | Path to modify. |
| `permissions` | `str` | Yes | — | Permission string in octal format (e.g., `'755'`, `'644'`, `'600'`). |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `recursive` | `bool` | No | `False` | If `True`, applies permissions recursively. |

**Examples:**

```python
# Make a script executable
ssh_file_permissions(path='/opt/scripts/deploy.sh', permissions='755')

# Secure a private key file
ssh_file_permissions(path='/home/admin/.ssh/id_rsa', permissions='600')

# Recursively set directory permissions
ssh_file_permissions(path='/var/www/html', permissions='755', recursive=True)
```

---

#### 🔧 `ssh_change_owner`

**Change file or directory ownership (equivalent to `chown`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | Path to modify. |
| `owner` | `str` | Yes | — | New owner username. |
| `group` | `str` | No | — | New group name. If omitted, only the owner is changed. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `recursive` | `bool` | No | `False` | If `True`, applies ownership change recursively. |

**Examples:**

```python
# Change owner
ssh_change_owner(path='/var/www/html', owner='www-data')

# Change owner and group
ssh_change_owner(path='/var/www/html', owner='www-data', group='www-data', recursive=True)
```

---

#### 🔧 `ssh_find_files`

**Search for files and directories with flexible filters (equivalent to `find`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | Starting directory for the search. |
| `name` | `str` | No | — | Filename pattern (supports wildcards, e.g., `'*.log'`, `'config*'`). |
| `type` | `str` | No | — | Filter by type: `'f'` for files only, `'d'` for directories only. |
| `size` | `str` | No | — | Filter by size (e.g., `'+100M'` for files over 100MB, `'-1k'` for files under 1KB). |
| `modified_within` | `str` | No | — | Find files modified within a timeframe (e.g., `'7'` for 7 days, `'1'` for 1 day). |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Examples:**

```python
# Find all .log files in /var/log
ssh_find_files(path='/var/log', name='*.log', type='f')

# Find large files over 500MB
ssh_find_files(path='/', size='+500M', type='f')

# Find recently modified config files
ssh_find_files(path='/etc', name='*.conf', modified_within='7')

# Find empty directories
ssh_find_files(path='/tmp', type='d')
```

---

#### 🔧 `ssh_disk_file_usage`

**Show disk usage for a specific file or directory (equivalent to `du -sh`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | Path to check. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_disk_file_usage(path='/var/log')
# Returns: "2.3G    /var/log"
```

---

### Category 4: Log & Search (5 tools)

Tools for searching through files, viewing logs, and performing text replacements.

---

#### 🔧 `ssh_search_in_files`

**Search for text patterns within files (equivalent to `grep`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `pattern` | `str` | Yes | — | Text or regex pattern to search for. |
| `path` | `str` | Yes | — | File or directory path to search in. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `case_insensitive` | `bool` | No | `False` | If `True`, performs case-insensitive matching. |
| `regex` | `bool` | No | `False` | If `True`, treats the pattern as a regular expression. |

**Examples:**

```python
# Search for errors in a log file
ssh_search_in_files(pattern='ERROR', path='/var/log/app.log')

# Case-insensitive search across a directory
ssh_search_in_files(pattern='database', path='/etc/myapp/', case_insensitive=True)

# Regex search for IP addresses
ssh_search_in_files(pattern=r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', path='/var/log/auth.log', regex=True)
```

---

#### 🔧 `ssh_tail_file`

**View the last N lines of a file (equivalent to `tail -n`).**

Ideal for checking recent log entries.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | File path to tail. |
| `lines` | `int` | No | `50` | Number of lines to show from the end. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
# View last 100 lines of syslog
ssh_tail_file(path='/var/log/syslog', lines=100)
```

---

#### 🔧 `ssh_head_file`

**View the first N lines of a file (equivalent to `head -n`).**

Useful for inspecting file headers, CSV column names, or configuration file structures.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `path` | `str` | Yes | — | File path to read from. |
| `lines` | `int` | No | `50` | Number of lines to show from the beginning. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
# View first 20 lines of a CSV file
ssh_head_file(path='/data/export.csv', lines=20)
```

---

#### 🔧 `ssh_search_logs`

**Search through system logs using `journalctl` or grep.**

Provides a higher-level interface for log searching that works with both systemd journal and traditional log files.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `pattern` | `str` | Yes | — | Text pattern to search for in logs. |
| `log_path` | `str` | No | — | Specific log file to search. If omitted, searches the systemd journal. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `since` | `str` | No | — | Time filter (e.g., `'1 hour ago'`, `'today'`, `'2024-01-15'`). Only works with `journalctl`. |

**Examples:**

```python
# Search systemd journal for SSH errors
ssh_search_logs(pattern='sshd', since='1 hour ago')

# Search a specific log file
ssh_search_logs(pattern='OutOfMemory', log_path='/var/log/app/error.log')

# Search for recent kernel errors
ssh_search_logs(pattern='error', since='today')
```

---

#### 🔧 `ssh_sed_replace`

**Find and replace text in a file using `sed`.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `file_path` | `str` | Yes | — | Path to the file to modify. |
| `find` | `str` | Yes | — | Text or pattern to find. |
| `replace` | `str` | Yes | — | Replacement text. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `backup` | `bool` | No | `True` | If `True`, creates a backup of the original file (`.bak` extension). |

**Examples:**

```python
# Update a port in a config file
ssh_sed_replace(
    file_path='/etc/myapp/config.yml',
    find='port: 3000',
    replace='port: 8080'
)

# Replace without backup
ssh_sed_replace(
    file_path='/tmp/test.txt',
    find='old_value',
    replace='new_value',
    backup=False
)
```

---

### Category 5: System Monitoring (8 tools)

Monitor system resources, processes, and performance metrics.

---

#### 🔧 `ssh_system_info`

**Get a comprehensive system summary.**

Returns a consolidated overview of the entire system in one call.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_system_info()
```

**Returns:** Hostname, OS/distro, kernel version, architecture, CPU info, total/used memory, disk usage, uptime, load averages, and network interfaces.

---

#### 🔧 `ssh_disk_usage`

**Show disk space usage for all mounted filesystems (equivalent to `df -h`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_disk_usage()
```

**Returns:** Formatted table with filesystem, size, used, available, use%, and mount point for each partition.

---

#### 🔧 `ssh_memory_usage`

**Show memory and swap usage (equivalent to `free -h`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_memory_usage()
```

**Returns:** Total, used, free, shared, buff/cache, and available memory along with swap usage.

---

#### 🔧 `ssh_cpu_info`

**Get CPU details and current load.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_cpu_info()
```

**Returns:** CPU model, number of cores/threads, clock speed, architecture, and current load averages (1/5/15 minutes).

---

#### 🔧 `ssh_process_list`

**List running processes (equivalent to `ps aux`) with optional filtering and sorting.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |
| `filter_pattern` | `str` | No | — | Filter processes by name pattern (e.g., `'nginx'`, `'python'`). |
| `sort_by` | `str` | No | — | Sort by `'cpu'` or `'mem'`. |

**Examples:**

```python
# List all processes
ssh_process_list()

# Find all Python processes
ssh_process_list(filter_pattern='python')

# List processes sorted by memory usage
ssh_process_list(sort_by='mem')
```

---

#### 🔧 `ssh_top_processes`

**Show the top N processes by CPU or memory consumption.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |
| `count` | `int` | No | `10` | Number of top processes to show. |
| `sort_by` | `str` | No | `'cpu'` | Sort by `'cpu'` or `'mem'`. |

**Example:**

```python
# Top 5 memory-hungry processes
ssh_top_processes(count=5, sort_by='mem')
```

---

#### 🔧 `ssh_kill_process`

**Kill a process by its PID.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `pid` | `int` | Yes | — | Process ID to kill. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `signal` | `str` | No | `'TERM'` | Signal to send. Common values: `'TERM'` (graceful), `'KILL'` (force), `'HUP'` (reload). |

**Examples:**

```python
# Gracefully terminate a process
ssh_kill_process(pid=12345)

# Force kill a stuck process
ssh_kill_process(pid=12345, signal='KILL')

# Send HUP to reload config (e.g., nginx)
ssh_kill_process(pid=9876, signal='HUP')
```

---

#### 🔧 `ssh_system_load`

**Get current system load averages.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_system_load()
```

**Returns:** 1-minute, 5-minute, and 15-minute load averages along with the number of CPU cores for context.

---

### Category 6: Network (5 tools)

Network diagnostics and information tools.

---

#### 🔧 `ssh_network_info`

**Show all network interfaces and their IP addresses.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_network_info()
```

**Returns:** Interface names, IPv4/IPv6 addresses, MAC addresses, and status (UP/DOWN).

---

#### 🔧 `ssh_open_ports`

**List all open/listening ports (equivalent to `ss -tlnp`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_open_ports()
```

**Returns:** Protocol, local address, port, and the process/PID listening on each port.

---

#### 🔧 `ssh_check_port`

**Test if a specific port is reachable from the remote server.**

Useful for verifying firewall rules, checking if a service is accessible, or testing connectivity between servers.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `host` | `str` | Yes | — | Target hostname or IP to test. |
| `port` | `int` | Yes | — | Port number to test. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
# Check if database port is reachable
ssh_check_port(host='db.internal', port=5432)

# Check if external API is accessible
ssh_check_port(host='api.example.com', port=443)
```

---

#### 🔧 `ssh_ping`

**Ping a host from the remote server.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `target` | `str` | Yes | — | Hostname or IP to ping. |
| `count` | `int` | No | `4` | Number of ping packets to send. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_ping(target='8.8.8.8', count=3)
```

**Returns:** Ping statistics including round-trip times (min/avg/max) and packet loss percentage.

---

#### 🔧 `ssh_dns_lookup`

**Perform DNS lookup for a domain (equivalent to `dig` or `nslookup`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `domain` | `str` | Yes | — | Domain name to look up. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_dns_lookup(domain='example.com')
```

**Returns:** DNS records including A, AAAA, MX, NS, and CNAME records (where available).

---

### Category 7: Docker Operations (7 tools)

Manage Docker containers, images, and compose stacks on the remote host.

---

#### 🔧 `ssh_docker_ps`

**List Docker containers.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |
| `all` | `bool` | No | `False` | If `True`, shows all containers (including stopped). Default shows only running. |

**Examples:**

```python
# List running containers
ssh_docker_ps()

# List all containers (including stopped)
ssh_docker_ps(all=True)
```

---

#### 🔧 `ssh_docker_logs`

**View logs from a Docker container.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `container` | `str` | Yes | — | Container name or ID. |
| `session_name` | `str` | No | `'default'` | Session to use. |
| `lines` | `int` | No | `100` | Number of log lines to retrieve. |

**Example:**

```python
ssh_docker_logs(container='nginx-proxy', lines=50)
```

---

#### 🔧 `ssh_docker_exec`

**Execute a command inside a running Docker container.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `container` | `str` | Yes | — | Container name or ID. |
| `command` | `str` | Yes | — | Command to execute inside the container. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Examples:**

```python
# Check nginx config inside container
ssh_docker_exec(container='nginx', command='nginx -t')

# List files in a container
ssh_docker_exec(container='myapp', command='ls -la /app')

# Check environment variables
ssh_docker_exec(container='myapp', command='env')
```

---

#### 🔧 `ssh_docker_images`

**List all Docker images on the remote host.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_docker_images()
```

**Returns:** Repository, tag, image ID, creation date, and size for each image.

---

#### 🔧 `ssh_docker_stats`

**Show real-time resource usage statistics for running containers.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_docker_stats()
```

**Returns:** CPU %, memory usage/limit, memory %, network I/O, and block I/O for each running container.

---

#### 🔧 `ssh_docker_compose`

**Run Docker Compose commands on a compose project.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `action` | `str` | Yes | — | Compose action: `'up'`, `'down'`, `'restart'`, `'ps'`, or `'logs'`. |
| `path` | `str` | Yes | — | Path to the `docker-compose.yml` file or its parent directory. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Examples:**

```python
# Start services in detached mode
ssh_docker_compose(action='up', path='/opt/myapp/docker-compose.yml')

# Check running services
ssh_docker_compose(action='ps', path='/opt/myapp/')

# Restart all services
ssh_docker_compose(action='restart', path='/opt/myapp/')

# Bring everything down
ssh_docker_compose(action='down', path='/opt/myapp/')

# View compose logs
ssh_docker_compose(action='logs', path='/opt/myapp/')
```

---

#### 🔧 `ssh_docker_inspect`

**Inspect a Docker container's configuration and state.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `container` | `str` | Yes | — | Container name or ID. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_docker_inspect(container='redis-cache')
```

**Returns:** Detailed JSON output including container config, network settings, mount points, environment variables, and state information.

---

### Category 8: Package Management (4 tools)

Install, remove, and manage system packages. **Auto-detects** the package manager on the remote system:

| Distro Family | Package Manager |
|:---|:---|
| Debian / Ubuntu | `apt` |
| RHEL / CentOS / Fedora | `yum` or `dnf` |
| Arch Linux | `pacman` |

---

#### 🔧 `ssh_install_package`

**Install a system package.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `package` | `str` | Yes | — | Package name to install (e.g., `'nginx'`, `'htop'`, `'git'`). |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_install_package(package='nginx')
# Auto-detects: runs "apt install -y nginx" on Ubuntu, "yum install -y nginx" on CentOS, etc.
```

---

#### 🔧 `ssh_remove_package`

**Remove/uninstall a system package.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `package` | `str` | Yes | — | Package name to remove. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_remove_package(package='apache2')
```

---

#### 🔧 `ssh_list_packages`

**List installed packages with optional filtering.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `filter` | `str` | No | — | Filter pattern to search for (e.g., `'python'`, `'lib*ssl*'`). |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Examples:**

```python
# List all installed packages
ssh_list_packages()

# List only Python-related packages
ssh_list_packages(filter='python')
```

---

#### 🔧 `ssh_check_updates`

**Check for available package updates.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_check_updates()
```

**Returns:** List of packages with available updates, including current and available versions.

---

### Category 9: User Management (4 tools)

View and inspect user accounts and login history.

---

#### 🔧 `ssh_list_users`

**List all user accounts on the system.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_list_users()
```

**Returns:** Username, UID, GID, home directory, and shell for each user.

---

#### 🔧 `ssh_user_info`

**Get detailed information about a specific user.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `username` | `str` | Yes | — | Username to look up. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_user_info(username='deploy')
```

**Returns:** Username, UID, GID, groups (primary and supplementary), home directory, shell, account status, and last login.

---

#### 🔧 `ssh_whoami`

**Show the current authenticated user on the remote session.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_whoami()
```

**Returns:** The username of the currently authenticated SSH user.

---

#### 🔧 `ssh_last_logins`

**Show recent login history.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_last_logins()
```

**Returns:** Recent login records including username, terminal, source IP/hostname, and login/logout times.

---

### Category 10: Cron Jobs (3 tools)

Manage scheduled tasks (cron jobs) on the remote server.

---

#### 🔧 `ssh_list_cron`

**List all cron jobs for the current user (or root).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_list_cron()
```

**Returns:** All crontab entries with their schedule expressions and commands.

---

#### 🔧 `ssh_add_cron`

**Add a new cron job.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `schedule` | `str` | Yes | — | Cron schedule expression (e.g., `'0 2 * * *'` for daily at 2 AM). |
| `command` | `str` | Yes | — | Command to execute on schedule. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Examples:**

```python
# Daily backup at 2 AM
ssh_add_cron(schedule='0 2 * * *', command='/opt/scripts/backup.sh >> /var/log/backup.log 2>&1')

# Every 5 minutes health check
ssh_add_cron(schedule='*/5 * * * *', command='curl -s http://localhost:8080/health > /dev/null')

# Weekly log rotation on Sunday at midnight
ssh_add_cron(schedule='0 0 * * 0', command='/usr/sbin/logrotate /etc/logrotate.conf')
```

**Cron Schedule Quick Reference:**

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 7, where 0 and 7 = Sunday)
│ │ │ │ │
* * * * *  command
```

---

#### 🔧 `ssh_remove_cron`

**Remove a cron job matching a pattern.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `pattern` | `str` | Yes | — | Pattern to match against cron entries. All matching entries are removed. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
# Remove the backup cron job
ssh_remove_cron(pattern='backup.sh')
```

---

### Category 11: Archive & Compression (2 tools)

Create and extract compressed archives.

---

#### 🔧 `ssh_compress`

**Create a compressed archive (tar.gz or zip).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `source` | `str` | Yes | — | Path to file or directory to compress. |
| `destination` | `str` | Yes | — | Output archive path (e.g., `/tmp/backup.tar.gz` or `/tmp/files.zip`). |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Examples:**

```python
# Create a tar.gz archive
ssh_compress(source='/var/www/html', destination='/backups/site-backup.tar.gz')

# Create a zip archive
ssh_compress(source='/home/admin/documents', destination='/tmp/documents.zip')
```

> The archive format is automatically determined by the file extension of `destination`.

---

#### 🔧 `ssh_extract`

**Extract a compressed archive.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `source` | `str` | Yes | — | Path to the archive file. |
| `destination` | `str` | Yes | — | Directory to extract into. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Examples:**

```python
# Extract a tar.gz
ssh_extract(source='/backups/site-backup.tar.gz', destination='/var/www/html')

# Extract a zip
ssh_extract(source='/tmp/release-v2.zip', destination='/opt/app')
```

> Supports `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`, `.zip`, and `.tar` formats.

---

### Category 12: Security & Audit (3 tools)

Service management and security auditing tools.

---

#### 🔧 `ssh_check_service`

**Check the status of a systemd service (equivalent to `systemctl status`).**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `service` | `str` | Yes | — | Service name (e.g., `'nginx'`, `'sshd'`, `'docker'`). |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_check_service(service='nginx')
```

**Returns:** Service active/inactive status, enabled/disabled state, PID, memory usage, and recent log entries.

---

#### 🔧 `ssh_manage_service`

**Start, stop, restart, enable, or disable a systemd service.**

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `service` | `str` | Yes | — | Service name. |
| `action` | `str` | Yes | — | Action to perform: `'start'`, `'stop'`, `'restart'`, `'enable'`, or `'disable'`. |
| `session_name` | `str` | No | `'default'` | Session to use. |

**Examples:**

```python
# Restart nginx after config change
ssh_manage_service(service='nginx', action='restart')

# Enable a service to start on boot
ssh_manage_service(service='docker', action='enable')

# Stop a service
ssh_manage_service(service='apache2', action='stop')
```

---

#### 🔧 `ssh_failed_logins`

**Show failed SSH login attempts (checks auth logs and/or `lastb`).**

Useful for security auditing — detect brute-force attempts, unauthorized access, and suspicious login activity.

| Parameter | Type | Required | Default | Description |
|:---|:---:|:---:|:---:|:---|
| `session_name` | `str` | No | `'default'` | Session to use. |

**Example:**

```python
ssh_failed_logins()
```

**Returns:** Recent failed login attempts with timestamp, username attempted, source IP address, and authentication method.

---

## 🔀 Multi-Session Usage Examples

One of the most powerful features of this MCP server is the ability to manage **multiple Linux servers simultaneously** through named sessions.

### Example: Managing Production + Staging

```
You: "Connect to my production server at prod.example.com and staging at staging.example.com"

→ AI calls: ssh_connect(host='prod.example.com', username='admin', password='...', session_name='prod')
→ AI calls: ssh_connect(host='staging.example.com', username='admin', password='...', session_name='staging')

You: "Show disk usage on both servers"

→ AI calls: ssh_disk_usage(session_name='prod')
→ AI calls: ssh_disk_usage(session_name='staging')

→ AI presents a comparison table of disk usage across both environments
```

### Example: Rolling Deployment Across Multiple Servers

```
You: "Connect to all three web servers"

→ ssh_connect(host='web1.internal', session_name='web1')
→ ssh_connect(host='web2.internal', session_name='web2')
→ ssh_connect(host='web3.internal', session_name='web3')

You: "Deploy the latest version to each server one at a time"

→ For each server:
   1. ssh_manage_service(service='nginx', action='stop', session_name='web1')
   2. ssh_execute(command='cd /var/www && git pull origin main', session_name='web1')
   3. ssh_manage_service(service='nginx', action='start', session_name='web1')
   4. ssh_check_service(service='nginx', session_name='web1')  # verify healthy
   → Repeat for web2, web3...
```

### Example: Comparing Configurations Across Environments

```
You: "Compare the nginx config between prod and staging"

→ ssh_read_file(path='/etc/nginx/nginx.conf', session_name='prod')
→ ssh_read_file(path='/etc/nginx/nginx.conf', session_name='staging')

→ AI shows a diff of the two configurations
```

### Session Management

```
You: "Show me all my active sessions"

→ ssh_list_sessions()

Result:
┌──────────┬──────────────────┬──────────┬────────┬──────────┐
│ Session  │ Host             │ Username │ Uptime │ Commands │
├──────────┼──────────────────┼──────────┼────────┼──────────┤
│ prod     │ prod.example.com │ admin    │ 45m    │ 23       │
│ staging  │ stg.example.com  │ admin    │ 42m    │ 18       │
│ web1     │ web1.internal    │ deploy   │ 12m    │ 8        │
└──────────┴──────────────────┴──────────┴────────┴──────────┘

You: "Disconnect from all servers"

→ ssh_disconnect_all()
```

---

## 🛡 Security Best Practices

### 1. Use SSH Key Authentication in Production

Password-based authentication is convenient for development but less secure. For production servers:

```python
ssh_connect(host='prod.example.com', username='deploy', key_path='C:\\Users\\pawan\\.ssh\\prod_key')
```

Generate a key pair if you don't have one:

```bash
ssh-keygen -t ed25519 -C "mcp-server"
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@remote-host
```

### 2. Credential Cache File Permissions

The credential cache at `~/.ssh-mcp-cache/credentials.json` is created with restricted permissions (`600` — owner read/write only). Verify this:

```bash
ls -la ~/.ssh-mcp-cache/credentials.json
# Should show: -rw------- 1 user user ... credentials.json
```

### 3. Don't Commit Credentials to Git

**Never** commit `mcp.json` files containing passwords to version control.

Add to your `.gitignore`:

```gitignore
# MCP configuration with credentials
.cursor/mcp.json
mcp.json

# SSH MCP credential cache
.ssh-mcp-cache/
```

### 4. Use Environment Variables or Interactive Mode

Instead of hardcoding passwords in config files:

- **Option A:** Set environment variables in your shell profile (they won't be in any file checked into git)
- **Option B:** Omit the `env` section entirely and let the server prompt you in chat

### 5. Principle of Least Privilege

Create a dedicated SSH user for MCP operations with only the permissions needed:

```bash
# On the remote server
sudo useradd -m -s /bin/bash mcp-user
sudo usermod -aG docker mcp-user  # if Docker access is needed
# Avoid giving root access unless absolutely necessary
```

### 6. Network Security

- Use a **VPN** or **SSH bastion host** for accessing production servers
- Configure **firewall rules** to restrict SSH access to known IP addresses
- Consider using **fail2ban** to block brute-force attempts

---

## 🔧 Troubleshooting

### Server Not Loading in AI IDE

**Symptom:** The MCP server shows as disconnected or doesn't appear in the tools list.

**Solutions:**
1. **Verify `uv` is in your PATH:**
   ```powershell
   uv --version
   ```
   If not found, reinstall uv or add it to your system PATH.

2. **Check the config file path:** Ensure your `mcp.json` is in the correct location for your IDE (see [Configuring Your AI IDE](#-configuring-your-ai-ide)).

3. **Validate JSON syntax:** A single missing comma or bracket will break the config. Use a JSON validator.

4. **Check the `--directory` path:** Make sure the path in `args` points to the actual project directory containing `server.py`.

5. **Restart the IDE:** Some IDEs only read MCP configs on startup.

---

### Connection Refused

**Symptom:** `ssh_connect` fails with "Connection refused."

**Solutions:**
1. **Verify the host is reachable:**
   ```powershell
   ping your-host
   ```
2. **Check SSH is running on the remote host:**
   ```bash
   sudo systemctl status sshd
   ```
3. **Verify the port:**
   ```powershell
   Test-NetConnection -ComputerName your-host -Port 22
   ```
4. **Check firewall rules** on both the remote server and your local network.

---

### Authentication Failed

**Symptom:** `ssh_connect` fails with "Authentication failed."

**Solutions:**
1. **Verify credentials manually:**
   ```powershell
   ssh username@host
   ```
2. **Check username/password:** Ensure no typos, especially with special characters.
3. **SSH key permissions:** Private key files must have restricted permissions:
   ```bash
   chmod 600 ~/.ssh/id_rsa
   ```
4. **Server allows password auth:** Check `/etc/ssh/sshd_config` on the remote host:
   ```
   PasswordAuthentication yes
   ```

---

### Command Timeout

**Symptom:** Commands fail with a timeout error.

**Solutions:**
1. **Increase the timeout parameter:**
   ```python
   ssh_execute(command='find / -name "*.log"', timeout=120)
   ```
2. **Use background execution for long-running commands:**
   ```python
   ssh_execute_background(command='tar czf /backup/full.tar.gz /')
   ```
3. **Check network latency** between your machine and the remote host.

---

### Debugging with MCP Inspector

For any issue, the MCP Inspector provides detailed insight:

```powershell
cd C:\AI_Workspaces\Anti_Workspace\linux-ssh-mcp
uv run mcp dev server.py
```

This opens a browser-based UI where you can:
- See all registered tools and their schemas
- Test individual tools with custom inputs
- View raw JSON requests and responses
- Check server logs for errors

---

### Common Error Messages

| Error Message | Likely Cause | Fix |
|:---|:---|:---|
| `No active session 'default'` | Not connected yet | Call `ssh_connect` first |
| `Session 'prod' already exists` | Duplicate session name | Use a different name or disconnect first |
| `Connection timed out` | Host unreachable or wrong port | Check host, port, and firewall |
| `Authentication failed` | Wrong credentials | Verify username/password/key |
| `Permission denied` | Insufficient privileges | Use `sudo` or connect as root |
| `Command not found` | Missing tool on remote host | Install the required package |
| `No such file or directory` | Invalid path | Verify the path exists on the remote server |

---

## 👥 Author & Contact

This project was created by **Pawan Gunjkar**.

- **Author**: Pawan Gunjkar
- **Email**: pawangunjkar@gamil.com
- **Bug Reports**: If you find any bugs, issues, or want to report bugs/request help, please report them to me at my email above.

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 Pawan Gunjkar <pawangunjkar@gamil.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">

**Built with ❤️ using [FastMCP](https://github.com/jlowin/fastmcp) + [Paramiko](https://www.paramiko.org/)**

*If you find this useful, give it a ⭐!*

</div>
