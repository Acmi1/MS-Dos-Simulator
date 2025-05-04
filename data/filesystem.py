"""
Virtual file system implementation for the DOS Simulator
"""
import os
import json
import time
import shlex
from datetime import datetime
from colorama import Fore, Style
from utils import parse_path, is_valid_filename

class FileSystem:
    """Virtual file system that simulates a DOS directory structure"""
    
    def __init__(self):
        """Initialize the file system with root directory"""
        self.root = {
            "type": "dir",
            "name": "C:",
            "created": time.time(),
            "modified": time.time(),
            "content": {
                "DOS": {
                    "type": "dir",
                    "name": "DOS",
                    "created": time.time(),
                    "modified": time.time(),
                    "content": {
                        "README.TXT": {
                            "type": "file",
                            "name": "README.TXT",
                            "created": time.time(),
                            "modified": time.time(),
                            "size": 177,
                            "content": "Welcome to DOS-Simulator!\n\nThis is a Python-based simulation of an MS-DOS like environment.\nType HELP to see available commands.\n\nEnjoy exploring the virtual DOS system!"
                        }
                    }
                }
            }
        }
        
        # Current directory path (list of directory names)
        self.current_path = ["C:"]
        
        # Total virtual disk space (10 MB)
        self.total_space = 10 * 1024 * 1024
        self.used_space = self._calculate_used_space(self.root)
    
    def _calculate_used_space(self, node):
        """Recursively calculate used space for a directory"""
        if node["type"] == "file":
            return node["size"]
        
        total = 0
        if "content" in node:
            for item in node["content"].values():
                total += self._calculate_used_space(item)
        
        return total
    
    def get_free_space(self):
        """Return available free space"""
        self.used_space = self._calculate_used_space(self.root)
        return self.total_space - self.used_space
    
    def _get_node_at_path(self, path, create_dirs=False):
        """Get the node at the specified path"""
        # Start at root
        if not path or path == "C:" or path == "C:\\":
            return self.root
        
        # Parse the path
        parts = parse_path(path)
        if not parts:
            return self.root
        
        # Check if this is an absolute path or relative
        if parts[0] == "C:":
            current = self.root
            parts = parts[1:]
        else:
            # Start from current directory
            current = self._get_current_node()
            
            # Handle parent directory references
            if parts[0] == "..":
                if len(self.current_path) > 1:  # Can't go above C:
                    parts = parts[1:]
                    current = self._get_node_at_path("\\".join(self.current_path[:-1]))
                else:
                    parts = parts[1:]
                    current = self.root
            
            # Handle current directory references
            if parts and parts[0] == ".":
                parts = parts[1:]
        
        # Traverse the path
        for i, part in enumerate(parts):
            if part == "":
                continue
                
            if current["type"] != "dir":
                return None
            
            if part not in current["content"]:
                # If we're asked to create directories, do that
                if create_dirs and i < len(parts) - 1:
                    current["content"][part] = {
                        "type": "dir",
                        "name": part,
                        "created": time.time(),
                        "modified": time.time(),
                        "content": {}
                    }
                else:
                    return None
            
            current = current["content"][part]
        
        return current
    
    def _get_current_node(self):
        """Get the node of the current directory"""
        return self._get_node_at_path("\\".join(self.current_path))
    
    def resolve_path(self, path):
        """Resolve a path to a node"""
        return self._get_node_at_path(path)
    
    def get_current_path(self):
        """Get the current directory path as a string"""
        return "\\".join(self.current_path)
    
    def get_full_path(self, path):
        """Convert a relative path to a full path"""
        if path == ".":
            return self.get_current_path()
            
        # If it's an absolute path, return as is
        if path.startswith("C:"):
            return path
        
        # Handle parent directory
        if path == "..":
            if len(self.current_path) > 1:
                return "\\".join(self.current_path[:-1])
            else:
                return "C:"
        
        # Construct the full path
        if path.startswith("\\"):
            return f"C:{path}"
        else:
            return f"{self.get_current_path()}\\{path}"
    
    def list_directory(self, path="."):
        """List the contents of a directory"""
        node = self._get_node_at_path(path)
        if not node or node["type"] != "dir":
            return []
        
        files = []
        
        # Add . and .. entries
        files.append({
            "name": ".",
            "type": "dir",
            "size": 0,
            "created": node["created"],
            "modified": node["modified"]
        })
        
        # Add parent directory unless we're at root
        if path != "C:" and path != "C:\\":
            parent_node = self._get_node_at_path("..") if path == "." else self._get_node_at_path(os.path.dirname(path))
            files.append({
                "name": "..",
                "type": "dir",
                "size": 0,
                "created": parent_node["created"] if parent_node else node["created"],
                "modified": parent_node["modified"] if parent_node else node["modified"]
            })
        
        # Add all files and subdirectories
        for name, item in node["content"].items():
            files.append({
                "name": name,
                "type": item["type"],
                "size": item.get("size", 0),
                "created": item["created"],
                "modified": item["modified"]
            })
        
        return files
    
    def change_directory(self, path):
        """Change current directory to the specified path"""
        new_node = self._get_node_at_path(path)
        if not new_node or new_node["type"] != "dir":
            return False
        
        # Update current path
        if path == "..":
            if len(self.current_path) > 1:
                self.current_path.pop()
        elif path == ".":
            pass  # Stay in current directory
        elif path.startswith("C:"):
            # Absolute path
            parts = parse_path(path)
            if parts[0] == "C:":
                self.current_path = parts
        else:
            # Relative path
            parts = parse_path(path)
            for part in parts:
                if part == "..":
                    if len(self.current_path) > 1:
                        self.current_path.pop()
                elif part != "." and part:
                    self.current_path.append(part)
        
        return True
    
    def create_directory(self, path):
        """Create a new directory"""
        # Handle path
        dirname, basename = os.path.split(path)
        
        if not is_valid_filename(basename):
            return False
        
        parent = self._get_node_at_path(dirname or ".")
        if not parent or parent["type"] != "dir":
            return False
        
        # Check if directory already exists
        if basename in parent["content"]:
            return False
        
        # Create the directory
        parent["content"][basename] = {
            "type": "dir",
            "name": basename,
            "created": time.time(),
            "modified": time.time(),
            "content": {}
        }
        
        parent["modified"] = time.time()
        return True
    
    def remove_directory(self, path):
        """Remove a directory (must be empty)"""
        dirname, basename = os.path.split(path)
        
        parent = self._get_node_at_path(dirname or ".")
        if not parent or parent["type"] != "dir":
            return False
        
        # Check if directory exists
        if basename not in parent["content"]:
            return False
        
        dir_node = parent["content"][basename]
        if dir_node["type"] != "dir":
            return False
        
        # Check if directory is empty
        if dir_node["content"] and len(dir_node["content"]) > 0:
            print(f"{Fore.RED}Directory not empty{Style.RESET_ALL}")
            return False
        
        # Remove the directory
        del parent["content"][basename]
        parent["modified"] = time.time()
        return True
    
    def read_file(self, path):
        """Read the contents of a file"""
        node = self._get_node_at_path(path)
        if not node or node["type"] != "file":
            return None
        
        return node["content"]
    
    def write_file(self, path, content):
        """Write content to a file, creating it if it doesn't exist"""
        dirname, basename = os.path.split(path)
        
        if not is_valid_filename(basename):
            raise ValueError(f"Invalid filename: {basename}")
        
        parent = self._get_node_at_path(dirname or ".", create_dirs=True)
        if not parent or parent["type"] != "dir":
            raise ValueError(f"Invalid directory: {dirname}")
        
        file_size = len(content)
        
        # Check disk space
        existing_size = 0
        if basename in parent["content"] and parent["content"][basename]["type"] == "file":
            existing_size = parent["content"][basename]["size"]
        
        if self.get_free_space() + existing_size < file_size:
            raise IOError("Insufficient disk space")
        
        # Create/update the file
        now = time.time()
        if basename in parent["content"] and parent["content"][basename]["type"] == "file":
            # Update existing file
            parent["content"][basename]["content"] = content
            parent["content"][basename]["size"] = file_size
            parent["content"][basename]["modified"] = now
        else:
            # Create new file
            parent["content"][basename] = {
                "type": "file",
                "name": basename,
                "created": now,
                "modified": now,
                "size": file_size,
                "content": content
            }
        
        parent["modified"] = now
        return True
    
    def copy_file(self, source, destination):
        """Copy a file from source to destination"""
        # Read source file
        content = self.read_file(source)
        if content is None:
            return False
        
        # Write to destination
        try:
            self.write_file(destination, content)
            return True
        except Exception:
            return False
    
    def delete_file(self, path):
        """Delete a file"""
        dirname, basename = os.path.split(path)
        
        parent = self._get_node_at_path(dirname or ".")
        if not parent or parent["type"] != "dir":
            return False
        
        # Check if file exists
        if basename not in parent["content"]:
            return False
        
        file_node = parent["content"][basename]
        if file_node["type"] != "file":
            return False
        
        # Delete the file
        del parent["content"][basename]
        parent["modified"] = time.time()
        return True
    
    def rename_file(self, oldpath, newname):
        """Rename a file or directory"""
        dirname, oldname = os.path.split(oldpath)
        
        if not is_valid_filename(newname):
            return False
        
        parent = self._get_node_at_path(dirname or ".")
        if not parent or parent["type"] != "dir":
            return False
        
        # Check if old file exists
        if oldname not in parent["content"]:
            return False
        
        # Check if new name already exists
        if newname in parent["content"]:
            return False
        
        # Rename the file/directory
        node = parent["content"][oldname]
        node["name"] = newname
        parent["content"][newname] = node
        del parent["content"][oldname]
        
        parent["modified"] = time.time()
        return True
    
    def generate_tree(self, path, show_files=False, prefix=""):
        """Generate a tree representation of directory structure"""
        node = self._get_node_at_path(path)
        if not node or node["type"] != "dir":
            return []
        
        result = []
        
        # Get all directories and optionally files
        items = []
        for name, item in node["content"].items():
            if item["type"] == "dir" or (show_files and item["type"] == "file"):
                items.append((name, item))
        
        # Sort alphabetically with directories first
        items.sort(key=lambda x: (0 if x[1]["type"] == "dir" else 1, x[0].upper()))
        
        for i, (name, item) in enumerate(items):
            is_last = i == len(items) - 1
            
            # Choose the right symbols
            if is_last:
                branch = "└───"
                new_prefix = prefix + "    "
            else:
                branch = "├───"
                new_prefix = prefix + "│   "
            
            # Add the item
            if item["type"] == "dir":
                result.append(f"{prefix}{branch}{name}")
                
                # Recursively add subdirectories
                subdir_tree = self.generate_tree(
                    f"{path}\\{name}" if path != "." else name,
                    show_files,
                    new_prefix
                )
                result.extend(subdir_tree)
            else:
                # For files, show the filename
                result.append(f"{prefix}{branch}{name}")
        
        return result
    
    def save_state(self, filename="dos_state.json"):
        """Save the file system state to a JSON file"""
        state = {
            "filesystem": self.root,
            "current_path": self.current_path,
            "total_space": self.total_space,
            "used_space": self.used_space
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filename="dos_state.json"):
        """Load the file system state from a JSON file"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
                
            self.root = state["filesystem"]
            self.current_path = state["current_path"]
            self.total_space = state["total_space"]
            self.used_space = state["used_space"]
            return True
        except Exception:
            return False
