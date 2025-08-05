"""
Project Documentation and Inventory Management System
===================================================

Automated system for tracking project files, features, and documentation updates.

Features:
- Automatic file inventory generation
- Feature tracking and changelog management
- Documentation version control
- Release notes generation
- Development progress tracking
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import glob

class ProjectInventory:
    """Manage project files and documentation inventory"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.inventory_file = os.path.join(project_root, "PROJECT_INVENTORY.json")
        self.changelog_file = os.path.join(project_root, "CHANGELOG.md")
        self.features_file = os.path.join(project_root, "FEATURES.json")
        
    def scan_project_files(self) -> Dict[str, Any]:
        """Scan project directory and create file inventory"""
        inventory = {
            "scan_date": datetime.now().isoformat(),
            "project_root": self.project_root,
            "files": {},
            "directories": [],
            "statistics": {},
            "git_info": self._get_git_info()
        }
        
        # File patterns to track
        patterns = {
            "python_files": "*.py",
            "data_files": "*.csv",
            "model_files": "*.pkl",
            "config_files": "*.json",
            "documentation": "*.md",
            "text_files": "*.txt",
            "notebooks": "*.ipynb",
            "requirements": "requirements*.txt",
            "docker_files": "Dockerfile*",
            "test_files": "test_*.py"
        }
        
        # Scan files by pattern
        for category, pattern in patterns.items():
            files = glob.glob(os.path.join(self.project_root, "**", pattern), recursive=True)
            inventory["files"][category] = []
            
            for file_path in files:
                if self._should_include_file(file_path):
                    file_info = self._get_file_info(file_path)
                    inventory["files"][category].append(file_info)
        
        # Get directory structure
        inventory["directories"] = self._get_directory_structure()
        
        # Calculate statistics
        inventory["statistics"] = self._calculate_statistics(inventory["files"])
        
        return inventory
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed information about a file"""
        try:
            stat = os.stat(file_path)
            relative_path = os.path.relpath(file_path, self.project_root)
            
            info = {
                "path": relative_path,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "hash": self._get_file_hash(file_path),
                "lines": self._count_lines(file_path) if file_path.endswith(('.py', '.md', '.txt', '.json')) else None,
                "purpose": self._identify_file_purpose(relative_path)
            }
            
            return info
        except Exception as e:
            return {
                "path": os.path.relpath(file_path, self.project_root),
                "error": str(e)
            }
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate file hash for change detection"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return "unknown"
    
    def _count_lines(self, file_path: str) -> Optional[int]:
        """Count lines in text files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except:
            return None
    
    def _identify_file_purpose(self, relative_path: str) -> str:
        """Identify the purpose/category of a file"""
        purposes = {
            "dashboard.py": "Main dashboard interface",
            "auth.py": "Authentication and authorization system",
            "mobile_dashboard.py": "Mobile-responsive dashboard components",
            "production_predict_function.py": "Production prediction engine",
            "equipment_api.py": "REST API endpoints",
            "database_integration.py": "Database operations and management",
            "equipment_monitor.py": "Real-time monitoring system",
            "equipment_cleaner.py": "Data preprocessing and cleaning",
            "complete_equipment_failure_prediction_system.pkl": "Trained ML model package",
            "cleaned_equipment_data.csv": "Processed training data",
            "requirements.txt": "Python dependencies",
            "DOCUMENTATION.md": "Complete project documentation",
            "README.md": "Project overview and quick start",
            "CHANGELOG.md": "Version history and updates",
            "Dockerfile": "Container configuration",
            "docker-compose.yml": "Multi-container deployment"
        }
        
        filename = os.path.basename(relative_path)
        if filename in purposes:
            return purposes[filename]
        
        # Pattern-based identification
        if relative_path.startswith("tests/"):
            return "Test suite"
        elif "test_" in filename:
            return "Unit tests"
        elif filename.endswith(".pkl"):
            return "ML model or data file"
        elif filename.endswith(".csv"):
            return "Data file"
        elif filename.endswith(".json"):
            return "Configuration or data file"
        elif filename.endswith(".md"):
            return "Documentation"
        elif filename.endswith(".py"):
            return "Python module"
        else:
            return "Unknown"
    
    def _should_include_file(self, file_path: str) -> bool:
        """Determine if file should be included in inventory"""
        exclude_patterns = [
            "/.git/", "/__pycache__/", "/.pytest_cache/",
            "/venv/", "/.venv/", "/env/", "/.env/",
            "/node_modules/", "/.idea/", "/.vscode/",
            ".pyc", ".pyo", ".pyd", ".so", ".dll"
        ]
        
        relative_path = os.path.relpath(file_path, self.project_root)
        
        for pattern in exclude_patterns:
            if pattern in relative_path:
                return False
        
        return True
    
    def _get_directory_structure(self) -> List[str]:
        """Get project directory structure"""
        directories = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden and virtual environment directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'env', '__pycache__', 'node_modules']]
            
            relative_root = os.path.relpath(root, self.project_root)
            if relative_root != '.':
                directories.append(relative_root)
        
        return sorted(directories)
    
    def _calculate_statistics(self, files: Dict[str, List]) -> Dict[str, Any]:
        """Calculate project statistics"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "total_lines": 0,
            "by_category": {}
        }
        
        for category, file_list in files.items():
            category_stats = {
                "count": len(file_list),
                "size": sum(f.get("size", 0) for f in file_list),
                "lines": sum(f.get("lines", 0) for f in file_list if f.get("lines"))
            }
            
            stats["by_category"][category] = category_stats
            stats["total_files"] += category_stats["count"]
            stats["total_size"] += category_stats["size"]
            stats["total_lines"] += category_stats["lines"]
        
        return stats
    
    def _get_git_info(self) -> Optional[Dict[str, str]]:
        """Get git repository information"""
        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root
            ).decode().strip()
            
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root
            ).decode().strip()
            
            return {
                "branch": branch,
                "commit": commit[:8],
                "full_commit": commit
            }
        except:
            return None
    
    def save_inventory(self, inventory: Dict[str, Any]):
        """Save inventory to JSON file"""
        with open(self.inventory_file, 'w') as f:
            json.dump(inventory, f, indent=2, default=str)
    
    def load_previous_inventory(self) -> Optional[Dict[str, Any]]:
        """Load previous inventory for comparison"""
        try:
            with open(self.inventory_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def detect_changes(self, current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect changes between inventories"""
        if not previous:
            return {"status": "initial_scan", "changes": []}
        
        changes = {
            "status": "updated",
            "changes": [],
            "added_files": [],
            "modified_files": [],
            "deleted_files": []
        }
        
        # Create file hash maps for comparison
        current_files = {}
        for category, files in current["files"].items():
            for file_info in files:
                current_files[file_info["path"]] = file_info
        
        previous_files = {}
        for category, files in previous["files"].items():
            for file_info in files:
                previous_files[file_info["path"]] = file_info
        
        # Detect added files
        for path in current_files:
            if path not in previous_files:
                changes["added_files"].append(path)
                changes["changes"].append(f"Added: {path}")
        
        # Detect deleted files
        for path in previous_files:
            if path not in current_files:
                changes["deleted_files"].append(path)
                changes["changes"].append(f"Deleted: {path}")
        
        # Detect modified files
        for path in current_files:
            if path in previous_files:
                current_hash = current_files[path].get("hash")
                previous_hash = previous_files[path].get("hash")
                if current_hash != previous_hash:
                    changes["modified_files"].append(path)
                    changes["changes"].append(f"Modified: {path}")
        
        return changes

class ChangelogManager:
    """Manage project changelog and release notes"""
    
    def __init__(self, changelog_file: str = "CHANGELOG.md"):
        self.changelog_file = changelog_file
    
    def add_entry(self, version: str, changes: List[str], change_type: str = "feature"):
        """Add new changelog entry"""
        date = datetime.now().strftime("%Y-%m-%d")
        
        entry = f"""
## Version {version} - {date}

### {change_type.title()}
"""
        
        for change in changes:
            entry += f"- {change}\n"
        
        entry += "\n"
        
        # Read existing changelog
        existing_content = ""
        if os.path.exists(self.changelog_file):
            with open(self.changelog_file, 'r') as f:
                existing_content = f.read()
        
        # Write new changelog
        with open(self.changelog_file, 'w') as f:
            if "# Changelog" not in existing_content:
                f.write("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n")
            else:
                lines = existing_content.split('\n')
                header_end = next(i for i, line in enumerate(lines) if line.startswith('## '))
                f.write('\n'.join(lines[:header_end]))
                f.write('\n')
            
            f.write(entry)
            
            if existing_content and "## " in existing_content:
                lines = existing_content.split('\n')
                header_start = next(i for i, line in enumerate(lines) if line.startswith('## '))
                f.write('\n'.join(lines[header_start:]))

class FeatureTracker:
    """Track implemented features and development progress"""
    
    def __init__(self, features_file: str = "FEATURES.json"):
        self.features_file = features_file
        self.features = self._load_features()
    
    def _load_features(self) -> Dict[str, Any]:
        """Load existing features from file"""
        if os.path.exists(self.features_file):
            with open(self.features_file, 'r') as f:
                return json.load(f)
        return {"features": [], "categories": {}, "progress": {}}
    
    def add_feature(self, name: str, description: str, category: str, status: str = "planned", 
                   files: List[str] = None, tests: List[str] = None):
        """Add new feature to tracking"""
        feature = {
            "name": name,
            "description": description,
            "category": category,
            "status": status,
            "files": files or [],
            "tests": tests or [],
            "added_date": datetime.now().isoformat(),
            "completed_date": None
        }
        
        self.features["features"].append(feature)
        
        if category not in self.features["categories"]:
            self.features["categories"][category] = []
        self.features["categories"][category].append(name)
        
        self._save_features()
    
    def update_feature_status(self, name: str, status: str):
        """Update feature status"""
        for feature in self.features["features"]:
            if feature["name"] == name:
                feature["status"] = status
                if status == "completed":
                    feature["completed_date"] = datetime.now().isoformat()
                break
        
        self._save_features()
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get development progress summary"""
        total_features = len(self.features["features"])
        
        status_counts = {}
        for feature in self.features["features"]:
            status = feature["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_features": total_features,
            "status_breakdown": status_counts,
            "completion_percentage": (status_counts.get("completed", 0) / total_features * 100) if total_features > 0 else 0,
            "categories": list(self.features["categories"].keys())
        }
    
    def _save_features(self):
        """Save features to file"""
        with open(self.features_file, 'w') as f:
            json.dump(self.features, f, indent=2, default=str)

def generate_project_report():
    """Generate comprehensive project report"""
    inventory = ProjectInventory()
    changelog = ChangelogManager()
    features = FeatureTracker()
    
    # Scan current project state
    current_inventory = inventory.scan_project_files()
    previous_inventory = inventory.load_previous_inventory()
    changes = inventory.detect_changes(current_inventory, previous_inventory)
    
    # Save current inventory
    inventory.save_inventory(current_inventory)
    
    # Get progress summary
    progress = features.get_progress_summary()
    
    # Generate report
    report = {
        "generated_at": datetime.now().isoformat(),
        "project_statistics": current_inventory["statistics"],
        "recent_changes": changes,
        "development_progress": progress,
        "git_info": current_inventory["git_info"],
        "file_summary": {
            category: len(files) for category, files in current_inventory["files"].items()
        }
    }
    
    return report

def initialize_project_features():
    """Initialize feature tracking with current project features"""
    features = FeatureTracker()
    
    # Core ML System
    features.add_feature(
        "Machine Learning Model",
        "Random Forest model with 91% accuracy for equipment failure prediction",
        "Core ML",
        "completed",
        ["production_predict_function.py", "complete_equipment_failure_prediction_system.pkl"],
        ["tests/test_models.py"]
    )
    
    # Dashboard System
    features.add_feature(
        "Streamlit Dashboard", 
        "Interactive web dashboard with 6 views for equipment monitoring",
        "User Interface",
        "completed",
        ["dashboard.py"],
        ["tests/test_dashboard.py"]
    )
    
    # Mobile Responsive Design
    features.add_feature(
        "Mobile-Responsive Dashboard",
        "Mobile-optimized dashboard components with touch-friendly interface",
        "User Interface", 
        "completed",
        ["mobile_dashboard.py"],
        ["tests/test_mobile.py"]
    )
    
    # Authentication System
    features.add_feature(
        "User Authentication",
        "Role-based authentication with session management",
        "Security",
        "completed", 
        ["auth.py"],
        ["tests/test_auth.py"]
    )
    
    # API System
    features.add_feature(
        "REST API",
        "RESTful API endpoints for equipment prediction and management",
        "API",
        "completed",
        ["equipment_api.py"],
        ["tests/test_api.py"]
    )
    
    # Database Integration
    features.add_feature(
        "Database Integration",
        "SQLite database for equipment data and maintenance tracking",
        "Database",
        "completed",
        ["database_integration.py"],
        ["tests/test_database.py"]
    )
    
    # Monitoring System
    features.add_feature(
        "Real-time Monitoring",
        "Automated equipment monitoring and alert generation",
        "Monitoring",
        "completed",
        ["equipment_monitor.py"],
        ["tests/test_monitoring.py"]
    )
    
    # Test Suite
    features.add_feature(
        "Comprehensive Test Suite",
        "Unit tests for all system components with coverage reporting",
        "Testing",
        "completed",
        ["tests/conftest.py", "tests/test_models.py", "tests/test_api.py", "tests/test_dashboard.py"],
        []
    )
    
    print("✅ Feature tracking initialized with current project state")
    return features.get_progress_summary()

if __name__ == "__main__":
    # Initialize and generate project report
    print("🔍 Scanning project files...")
    
    # Initialize features if not already done
    features_summary = initialize_project_features()
    print(f"📊 Features tracked: {features_summary['total_features']}")
    print(f"✅ Completion: {features_summary['completion_percentage']:.1f}%")
    
    # Generate report
    report = generate_project_report()
    
    print("\n📋 PROJECT REPORT GENERATED")
    print("=" * 50)
    print(f"📁 Total Files: {report['project_statistics']['total_files']}")
    print(f"📄 Total Lines: {report['project_statistics']['total_lines']:,}")
    print(f"💾 Total Size: {report['project_statistics']['total_size'] / 1024 / 1024:.2f} MB")
    
    if report['recent_changes']['changes']:
        print(f"\n🔄 Recent Changes: {len(report['recent_changes']['changes'])}")
        for change in report['recent_changes']['changes'][:5]:
            print(f"  - {change}")
    
    print(f"\n🎯 Development Progress: {report['development_progress']['completion_percentage']:.1f}%")
    
    # Save report
    with open("PROJECT_REPORT.json", 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n💾 Report saved to PROJECT_REPORT.json")
