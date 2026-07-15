"""
Credential Store for Linux SSH MCP Server.

Author: Pawan Gunjkar (pawangunjkar@gamil.com)

Manages SSH credentials with a layered lookup strategy:
1. Environment variables (SSH_HOST, SSH_USERNAME, SSH_PASSWORD, etc.)
2. In-memory cache (current server session)
3. Local file cache (~/.ssh-mcp-cache/credentials.json)
4. If none found → returns None (server will prompt user)
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class SSHCredentials:
    """SSH connection credentials."""
    host: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    key_path: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary (excludes None values)."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "SSHCredentials":
        """Create from dictionary."""
        return cls(
            host=data["host"],
            port=int(data.get("port", 22)),
            username=data.get("username", "root"),
            password=data.get("password"),
            key_path=data.get("key_path"),
        )

    def masked_dict(self) -> dict:
        """Return dict with password masked (for display)."""
        d = self.to_dict()
        if "password" in d and d["password"]:
            d["password"] = "****" + d["password"][-2:] if len(d["password"]) > 2 else "****"
        return d


class CredentialStore:
    """
    Multi-layer credential store for SSH connections.
    
    Supports multiple named sessions, each with its own credentials.
    Credentials are cached in memory and optionally persisted to a JSON file.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the credential store."""
        self._memory_cache: dict[str, SSHCredentials] = {}
        
        # Determine cache directory
        if cache_dir:
            self._cache_dir = Path(cache_dir)
        else:
            env_cache_dir = os.environ.get("SSH_MCP_CACHE_DIR")
            if env_cache_dir:
                self._cache_dir = Path(env_cache_dir)
            else:
                self._cache_dir = Path.home() / ".ssh-mcp-cache"
        
        self._cache_file = self._cache_dir / "credentials.json"
        self._ensure_cache_dir()
        self._load_file_cache()

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions on Unix-like systems
            if sys.platform != "win32":
                os.chmod(self._cache_dir, 0o700)
        except OSError as e:
            print(f"Warning: Could not create cache directory: {e}", file=sys.stderr)

    def _load_file_cache(self):
        """Load credentials from the JSON cache file."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "r") as f:
                    data = json.load(f)
                for name, cred_data in data.items():
                    if name not in self._memory_cache:
                        self._memory_cache[name] = SSHCredentials.from_dict(cred_data)
                print(f"Loaded {len(data)} cached credential(s) from {self._cache_file}", file=sys.stderr)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                print(f"Warning: Could not load credential cache: {e}", file=sys.stderr)

    def _save_file_cache(self):
        """Save all credentials to the JSON cache file."""
        try:
            data = {name: cred.to_dict() for name, cred in self._memory_cache.items()}
            with open(self._cache_file, "w") as f:
                json.dump(data, f, indent=2)
            # Set restrictive permissions on the file
            if sys.platform != "win32":
                os.chmod(self._cache_file, 0o600)
        except OSError as e:
            print(f"Warning: Could not save credential cache: {e}", file=sys.stderr)

    def get_from_env(self) -> Optional[SSHCredentials]:
        """
        Try to get credentials from environment variables.
        
        Looks for: SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD, SSH_KEY_PATH
        """
        host = os.environ.get("SSH_HOST")
        if not host:
            return None
        
        return SSHCredentials(
            host=host,
            port=int(os.environ.get("SSH_PORT", "22")),
            username=os.environ.get("SSH_USERNAME", "root"),
            password=os.environ.get("SSH_PASSWORD"),
            key_path=os.environ.get("SSH_KEY_PATH"),
        )

    def get_credentials(self, session_name: str = "default") -> Optional[SSHCredentials]:
        """
        Get credentials for a session using layered lookup.
        
        Order: env vars (for 'default') → memory cache → file cache → None
        """
        # For the default session, try environment variables first
        if session_name == "default":
            env_creds = self.get_from_env()
            if env_creds:
                return env_creds
        
        # Check memory cache (includes file cache loaded at startup)
        if session_name in self._memory_cache:
            return self._memory_cache[session_name]
        
        return None

    def save_credentials(
        self,
        session_name: str,
        host: str,
        username: str = "root",
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        port: int = 22,
    ) -> SSHCredentials:
        """Save credentials to memory and file cache."""
        creds = SSHCredentials(
            host=host,
            port=port,
            username=username,
            password=password,
            key_path=key_path,
        )
        self._memory_cache[session_name] = creds
        self._save_file_cache()
        return creds

    def delete_credentials(self, session_name: str) -> bool:
        """Delete credentials for a session from all caches."""
        if session_name in self._memory_cache:
            del self._memory_cache[session_name]
            self._save_file_cache()
            return True
        return False

    def list_sessions(self) -> dict[str, dict]:
        """List all cached session credentials (with passwords masked)."""
        result = {}
        
        # Include env-based default if available
        env_creds = self.get_from_env()
        if env_creds and "default" not in self._memory_cache:
            result["default (env)"] = env_creds.masked_dict()
        
        for name, cred in self._memory_cache.items():
            result[name] = cred.masked_dict()
        
        return result

    def clear_all(self):
        """Clear all cached credentials."""
        self._memory_cache.clear()
        if self._cache_file.exists():
            try:
                self._cache_file.unlink()
            except OSError:
                pass
