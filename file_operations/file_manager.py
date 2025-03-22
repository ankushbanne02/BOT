import os
import json
from typing import Dict, List
import platform
from pathlib import Path

class FileManager:
    def __init__(self):
        self.directory_tree = {}
        self.ignored_patterns = [
            # System directories
            '.git', '__pycache__', 'node_modules', 'venv',
            '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll',
            '.env', '.vscode', '.idea', '*.log',
            'dist', 'build', 'target', 'bin',
            '*.tmp', '*.temp', '*.swp', '*.swo',
            'Thumbs.db', '.DS_Store', '*.cache',
            'System Volume Information', '$Recycle.Bin', 'Recovery',
            # Program files
            'Program Files', 'Program Files (x86)', 'Windows',
            'AppData', 'Local', 'Roaming', 'Temp',
            # Large data directories
            'node_modules', 'vendor', 'packages',
            'node_modules', 'bower_components',
            # Version control
            '.git', '.svn', '.hg',
            # Build directories
            'build', 'dist', 'out', 'target',
            'bin', 'obj', 'Debug', 'Release',
            # Cache directories
            '.cache', '.npm', '.yarn',
            'cache', 'temp', 'tmp'
        ]
        
        # User directories to scan
        self.user_dirs = [
            'Documents', 'Downloads', 'Desktop',
            'Pictures', 'Music', 'Videos',
            'Projects', 'Work', 'Personal'
        ]
        
        # Get user's home directory
        self.home_dir = str(Path.home())
        print(f"📁 User home directory: {self.home_dir}")

    def get_system_drives(self) -> List[str]:
        """Get user's home directory"""
        return [self.home_dir]  # Only scan user's home directory

    def is_in_user_directory(self, path: str) -> bool:
        """Check if a path is within any user directory"""
        # Convert path to lowercase for case-insensitive comparison
        path_lower = path.lower()
        # Check if any user directory is in the path
        return any(user_dir.lower() in path_lower for user_dir in self.user_dirs)

    def get_directory_tree(self, start_path: str) -> Dict:
        """Get the directory tree structure"""
        tree = {}
        try:
            for root, dirs, files in os.walk(start_path):
                # Filter out ignored directories and files first
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.ignored_patterns)]
                files[:] = [f for f in files if not any(pattern in f for pattern in self.ignored_patterns)]
                
                # Skip if no files or directories after filtering
                if not dirs and not files:
                    continue
                
                # Check if this is a user directory or contains user directories
                if self.is_in_user_directory(root):
                    relative_path = os.path.relpath(root, start_path)
                    tree[relative_path] = {
                        "dirs": dirs,
                        "files": files
                    }
                else:
                    # If not a user directory, check if any subdirectories are user directories
                    has_user_dirs = False
                    for dir_name in dirs:
                        if self.is_in_user_directory(os.path.join(root, dir_name)):
                            has_user_dirs = True
                            break
                    
                    # If no user directories in subdirectories, clear them to stop traversal
                    if not has_user_dirs:
                        dirs.clear()
        except Exception as e:
            print(f"Error scanning directory {start_path}: {e}")
        return tree

    def scan_system(self) -> Dict:
        """Scan the user's home directory for directory structure"""
        all_trees = {}
        for drive in self.get_system_drives():
            print(f"Scanning directory: {drive}")
            drive_tree = self.get_directory_tree(drive)
            all_trees[drive] = drive_tree
        return all_trees

    def save_directory_tree(self, tree: Dict, filename: str = "directory_tree.json"):
        """Save directory tree to a JSON file"""
        try:
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(tree, f, indent=2)
            print(f"✅ Directory structure saved to {filename}")
        except Exception as e:
            print(f"Error saving directory tree: {e}")

    def load_directory_tree(self, filename: str = "directory_tree.json") -> Dict:
        """Load directory tree from a JSON file"""
        try:
            with open(filename, "r", encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading directory tree: {e}")
            return {}

    def create_file(self, path: str, content: str = "") -> bool:
        """Create a new file with optional content"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error creating file {path}: {e}")
            return False

    def read_file(self, path: str) -> str:
        """Read file content"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return ""

    def delete_file(self, path: str) -> bool:
        """Delete a file"""
        try:
            os.remove(path)
            return True
        except Exception as e:
            print(f"Error deleting file {path}: {e}")
            return False 