# Publishing Guide — Linux SSH MCP

This guide walks you through publishing **linux-ssh-mcp** so developers and AI agents can discover and install it.

## Checklist

- [x] `README.md` with install instructions
- [x] `pyproject.toml` with metadata and console script
- [x] `smithery.yaml` for Smithery registry
- [x] `LICENSE` (MIT)
- [ ] Publish to PyPI
- [ ] Submit to Smithery
- [ ] Submit to Glama & Pulse MCP directories
- [ ] Set GitHub topics

---

## 1. Publish to PyPI

### One-time setup

```bash
pip install build twine
# Create account at https://pypi.org/account/register/
```

### Build and publish

```bash
cd linux-ssh-mcp
python -m build
twine upload dist/*
```

### Verify install

```bash
uvx pawangunjkar-linux-ssh-mcp --help
# Or add to MCP config:
```

```json
{
  "mcpServers": {
    "linux-ssh": {
      "command": "uvx",
      "args": ["pawangunjkar-linux-ssh-mcp"],
      "env": {
        "SSH_HOST": "your-host",
        "SSH_USERNAME": "ubuntu",
        "SSH_KEY_PATH": "/home/user/.ssh/id_rsa"
      }
    }
  }
}
```

---

## 2. Submit to Smithery

Smithery is the primary MCP package registry.

1. Go to [https://smithery.ai](https://smithery.ai) and sign in with GitHub
2. Click **Publish Server** → connect your `Pawangunjkar/linux-ssh-mcp` repository
3. Smithery reads `smithery.yaml` automatically
4. Complete the review flow

**Prerequisite:** Publish to PyPI first (Smithery uses `uvx pawangunjkar-linux-ssh-mcp`).

**CLI alternative:**

```bash
npm install -g @smithery/cli
smithery login
smithery publish
```

---

## 3. List on MCP Directories

### Glama.ai

- Visit [https://glama.ai/mcp/servers](https://glama.ai/mcp/servers)
- Submit your repository URL: `https://github.com/Pawangunjkar/linux-ssh-mcp`

### Pulse MCP

- Visit [https://www.pulsemcp.com](https://www.pulsemcp.com)
- Submit your repository for indexing

These directories feed into community hubs like [apappascs/mcp-servers-hub](https://github.com/apappascs/mcp-servers-hub).

---

## 4. GitHub Discoverability

### Topics

Add these topics on your repo **About** settings:

```
mcp, model-context-protocol, mcp-server, ssh, linux, devops, paramiko, remote-server, python, fastmcp
```

### GitHub CLI

```bash
gh repo edit Pawangunjkar/linux-ssh-mcp \
  --add-topic mcp,model-context-protocol,mcp-server,ssh,linux,devops,paramiko,python
```

---

## 5. Recommended README Badges

Add to the top of `README.md`:

```markdown
[![PyPI version](https://badge.fury.io/py/pawangunjkar-linux-ssh-mcp.svg)](https://pypi.org/project/pawangunjkar-linux-ssh-mcp/)
[![Smithery](https://smithery.ai/badge/linux-ssh-mcp)](https://smithery.ai/server/linux-ssh-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
```

*(Update Smithery badge URL after your server is listed.)*

---

## Support

- **Issues:** https://github.com/Pawangunjkar/linux-ssh-mcp/issues
- **Author:** Pawan Gunjkar — pawangunjkar@gmail.com
