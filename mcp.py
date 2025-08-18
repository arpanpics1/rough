# file: filesystem_mcp_server.py
# Requires: pip install mcp pydantic

import os
import json
import mimetypes
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from pydantic import BaseModel, Field, validator
from mcp.server.fastmcp import FastMCP

# ===== ENV CONFIG =====
# Base directory for file operations (defaults to current working directory)
BASE_DIR = os.getenv("FILESYSTEM_BASE_DIR", os.getcwd())
MAX_FILE_SIZE = int(os.getenv("FILESYSTEM_MAX_FILE_SIZE", "10485760"))  # 10MB default
ALLOWED_EXTENSIONS = os.getenv("FILESYSTEM_ALLOWED_EXTENSIONS", "").split(",") if os.getenv("FILESYSTEM_ALLOWED_EXTENSIONS") else None

# ===== MCP SERVER =====
mcp = FastMCP("filesystem")

# ===== MODELS =====
class PathInput(BaseModel):
    path: str = Field(..., description="File or directory path (relative to base directory)")
    
    @validator("path")
    def validate_path(cls, v):
        # Prevent directory traversal attacks
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid path: directory traversal not allowed")
        return v

class ReadFileInput(PathInput):
    encoding: str = Field("utf-8", description="Text encoding for reading files")
    max_size: int = Field(MAX_FILE_SIZE, description="Maximum file size to read in bytes")

class WriteFileInput(PathInput):
    content: str = Field(..., description="Content to write to the file")
    encoding: str = Field("utf-8", description="Text encoding for writing files")
    create_dirs: bool = Field(True, description="Create parent directories if they don't exist")

class SearchInput(BaseModel):
    pattern: str = Field(..., description="Search pattern (supports wildcards)")
    path: str = Field(".", description="Directory to search in (relative to base)")
    recursive: bool = Field(True, description="Search recursively in subdirectories")
    include_content: bool = Field(False, description="Include file content in results")

# ===== HELPERS =====
def _get_absolute_path(relative_path: str) -> Path:
    """Convert relative path to absolute path within BASE_DIR."""
    base = Path(BASE_DIR).resolve()
    target = (base / relative_path).resolve()
    
    # Ensure the target path is within BASE_DIR
    if not str(target).startswith(str(base)):
        raise ValueError("Path is outside the allowed base directory")
    
    return target

def _get_file_info(path: Path) -> Dict[str, Any]:
    """Get comprehensive file information."""
    try:
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path.relative_to(Path(BASE_DIR))),
            "absolute_path": str(path),
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "is_symlink": path.is_symlink(),
            "size": stat.st_size if path.is_file() else None,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:],
            "mime_type": mimetypes.guess_type(str(path))[0] if path.is_file() else None,
        }
    except (OSError, ValueError) as e:
        return {"error": str(e), "path": str(path)}

def _is_text_file(path: Path) -> bool:
    """Check if a file is likely to be text-based."""
    if not path.is_file():
        return False
    
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type:
        return mime_type.startswith('text/') or mime_type in [
            'application/json', 'application/xml', 'application/javascript'
        ]
    
    # Check first few bytes for binary content
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' not in chunk
    except:
        return False

# ===== TOOLS =====
@mcp.tool(description="List files and directories in a given path.")
def list_directory(input: PathInput) -> List[Dict[str, Any]]:
    """List contents of a directory with detailed information."""
    abs_path = _get_absolute_path(input.path)
    
    if not abs_path.exists():
        raise ValueError(f"Path does not exist: {input.path}")
    
    if not abs_path.is_dir():
        raise ValueError(f"Path is not a directory: {input.path}")
    
    results = []
    try:
        for item in sorted(abs_path.iterdir()):
            results.append(_get_file_info(item))
    except PermissionError:
        raise ValueError(f"Permission denied accessing directory: {input.path}")
    
    return results

@mcp.tool(description="Get detailed information about a file or directory.")
def get_file_info(input: PathInput) -> Dict[str, Any]:
    """Get detailed information about a specific file or directory."""
    abs_path = _get_absolute_path(input.path)
    
    if not abs_path.exists():
        raise ValueError(f"Path does not exist: {input.path}")
    
    info = _get_file_info(abs_path)
    
    # Add additional info for files
    if abs_path.is_file():
        info["is_text"] = _is_text_file(abs_path)
        if info["size"] and info["size"] > 0:
            try:
                with open(abs_path, 'rb') as f:
                    content = f.read()
                    info["md5"] = hashlib.md5(content).hexdigest()
                    info["sha256"] = hashlib.sha256(content).hexdigest()
            except:
                pass
    
    return info

@mcp.tool(description="Read the contents of a text file.")
def read_file(input: ReadFileInput) -> Dict[str, Any]:
    """Read and return the contents of a text file."""
    abs_path = _get_absolute_path(input.path)
    
    if not abs_path.exists():
        raise ValueError(f"File does not exist: {input.path}")
    
    if not abs_path.is_file():
        raise ValueError(f"Path is not a file: {input.path}")
    
    # Check file size
    file_size = abs_path.stat().st_size
    if file_size > input.max_size:
        raise ValueError(f"File too large: {file_size} bytes (max: {input.max_size})")
    
    # Check if allowed extension
    if ALLOWED_EXTENSIONS and abs_path.suffix.lower().lstrip('.') not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension not allowed: {abs_path.suffix}")
    
    try:
        with open(abs_path, 'r', encoding=input.encoding) as f:
            content = f.read()
        
        return {
            "path": input.path,
            "size": file_size,
            "encoding": input.encoding,
            "line_count": content.count('\n') + 1,
            "content": content
        }
    except UnicodeDecodeError:
        raise ValueError(f"Could not decode file with encoding '{input.encoding}'. File may be binary.")
    except PermissionError:
        raise ValueError(f"Permission denied reading file: {input.path}")

@mcp.tool(description="Write content to a file.")
def write_file(input: WriteFileInput) -> Dict[str, Any]:
    """Write content to a file, optionally creating parent directories."""
    abs_path = _get_absolute_path(input.path)
    
    # Check if allowed extension
    if ALLOWED_EXTENSIONS and abs_path.suffix.lower().lstrip('.') not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension not allowed: {abs_path.suffix}")
    
    # Create parent directories if requested
    if input.create_dirs:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(abs_path, 'w', encoding=input.encoding) as f:
            f.write(input.content)
        
        # Get file info after writing
        file_info = _get_file_info(abs_path)
        
        return {
            "path": input.path,
            "bytes_written": len(input.content.encode(input.encoding)),
            "encoding": input.encoding,
            "created_dirs": input.create_dirs,
            "file_info": file_info
        }
    except PermissionError:
        raise ValueError(f"Permission denied writing to file: {input.path}")

@mcp.tool(description="Search for files matching a pattern.")
def search_files(input: SearchInput) -> List[Dict[str, Any]]:
    """Search for files matching a pattern with optional content search."""
    import fnmatch
    
    abs_path = _get_absolute_path(input.path)
    
    if not abs_path.exists():
        raise ValueError(f"Search path does not exist: {input.path}")
    
    if not abs_path.is_dir():
        raise ValueError(f"Search path is not a directory: {input.path}")
    
    results = []
    
    def search_directory(directory: Path):
        try:
            for item in directory.iterdir():
                if item.is_file():
                    if fnmatch.fnmatch(item.name, input.pattern):
                        file_info = _get_file_info(item)
                        if input.include_content and _is_text_file(item):
                            try:
                                with open(item, 'r', encoding='utf-8') as f:
                                    file_info["content"] = f.read()
                            except:
                                file_info["content"] = "<could not read content>"
                        results.append(file_info)
                elif item.is_dir() and input.recursive:
                    search_directory(item)
        except PermissionError:
            pass  # Skip directories we can't access
    
    search_directory(abs_path)
    return sorted(results, key=lambda x: x.get("path", ""))

@mcp.tool(description="Create a new directory.")
def create_directory(input: PathInput) -> Dict[str, Any]:
    """Create a new directory and any necessary parent directories."""
    abs_path = _get_absolute_path(input.path)
    
    try:
        abs_path.mkdir(parents=True, exist_ok=True)
        return {
            "path": input.path,
            "created": True,
            "directory_info": _get_file_info(abs_path)
        }
    except PermissionError:
        raise ValueError(f"Permission denied creating directory: {input.path}")

@mcp.tool(description="Delete a file or empty directory.")
def delete_path(input: PathInput) -> Dict[str, Any]:
    """Delete a file or empty directory."""
    abs_path = _get_absolute_path(input.path)
    
    if not abs_path.exists():
        raise ValueError(f"Path does not exist: {input.path}")
    
    try:
        if abs_path.is_file():
            abs_path.unlink()
            return {"path": input.path, "deleted": True, "type": "file"}
        elif abs_path.is_dir():
            abs_path.rmdir()  # Only removes empty directories
            return {"path": input.path, "deleted": True, "type": "directory"}
    except OSError as e:
        raise ValueError(f"Could not delete {input.path}: {str(e)}")

@mcp.tool(description="Get the current working directory and base directory info.")
def get_workspace_info() -> Dict[str, Any]:
    """Get information about the current workspace/base directory."""
    base_path = Path(BASE_DIR)
    current_path = Path.cwd()
    
    return {
        "base_directory": str(base_path),
        "current_directory": str(current_path),
        "base_directory_info": _get_file_info(base_path),
        "max_file_size": MAX_FILE_SIZE,
        "allowed_extensions": ALLOWED_EXTENSIONS,
        "total_files": sum(1 for _ in base_path.rglob("*") if _.is_file()),
        "total_directories": sum(1 for _ in base_path.rglob("*") if _.is_dir()),
    }

# ===== RESOURCES =====
@mcp.resource("directory_tree/{path}", description="Directory tree structure for {path}")
def resource_directory_tree(path: str = ".") -> Tuple[str, bytes]:
    """Generate a directory tree structure as JSON."""
    def build_tree(directory: Path, max_depth: int = 3, current_depth: int = 0):
        if current_depth >= max_depth:
            return {"name": directory.name, "type": "directory", "truncated": True}
        
        tree = {
            "name": directory.name,
            "type": "directory",
            "children": []
        }
        
        try:
            for item in sorted(directory.iterdir()):
                if item.is_file():
                    tree["children"].append({
                        "name": item.name,
                        "type": "file",
                        "size": item.stat().st_size,
                        "mime_type": mimetypes.guess_type(str(item))[0]
                    })
                elif item.is_dir():
                    tree["children"].append(
                        build_tree(item, max_depth, current_depth + 1)
                    )
        except PermissionError:
            tree["error"] = "Permission denied"
        
        return tree
    
    abs_path = _get_absolute_path(path)
    if not abs_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    
    tree_data = build_tree(abs_path)
    return ("application/json", json.dumps(tree_data, indent=2).encode("utf-8"))

# ===== MAIN =====
if __name__ == "__main__":
    # Start MCP server over stdio
    mcp.run()
