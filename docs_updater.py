"""
Automated Documentation Update System
===================================

Automatically updates project documentation when new features are added or removed.

Features:
- Real-time documentation synchronization
- API documentation auto-generation
- Feature documentation updates
- README maintenance
- Version tracking and changelogs
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import ast
import inspect

class DocumentationUpdater:
    """Automatically update project documentation"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.docs_config = self._load_docs_config()
    
    def _load_docs_config(self) -> Dict[str, Any]:
        """Load documentation configuration"""
        default_config = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "auto_update": True,
            "sections": {
                "readme": {
                    "file": "README.md",
                    "auto_sections": ["installation", "features", "api", "changelog"]
                },
                "documentation": {
                    "file": "DOCUMENTATION.md", 
                    "auto_sections": ["architecture", "features", "api", "deployment"]
                },
                "api_docs": {
                    "file": "API_DOCUMENTATION.txt",
                    "auto_generate": True
                },
                "changelog": {
                    "file": "CHANGELOG.md",
                    "auto_generate": True
                }
            },
            "feature_tracking": {
                "completed_features": [],
                "in_progress_features": [],
                "planned_features": []
            }
        }
        
        config_file = os.path.join(self.project_root, "docs_config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key not in loaded_config:
                        loaded_config[key] = default_config[key]
                return loaded_config
        
        return default_config
    
    def update_readme_features(self, new_features: List[Dict[str, Any]]):
        """Update README.md with new features"""
        readme_path = os.path.join(self.project_root, "README.md")
        
        if not os.path.exists(readme_path):
            self._create_initial_readme()
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find features section
        features_start = content.find("## 📊 Key Features")
        if features_start == -1:
            # Add features section
            content = self._add_features_section(content, new_features)
        else:
            # Update existing features section
            content = self._update_features_section(content, new_features, features_start)
        
        # Update last modified
        content = self._update_last_modified(content)
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_initial_readme(self):
        """Create initial README.md if it doesn't exist"""
        readme_content = f"""# 🔧 Equipment Failure Prediction System

A comprehensive machine learning system for predicting equipment failures and optimizing maintenance schedules.

## 🎯 Project Overview

This system uses advanced machine learning techniques to predict equipment failures before they occur, enabling:
- **Proactive maintenance scheduling**
- **Cost reduction** through prevention of unexpected failures
- **Minimized downtime** and operational disruptions
- **Data-driven maintenance decisions**

## 📊 Key Features

*Features will be auto-updated by the documentation system*

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Basic Usage
```python
from production_predict_function import production_predict
import pandas as pd

# Load your equipment data
equipment_data = pd.read_csv('your_equipment_data.csv')

# Make predictions
predictions = production_predict(equipment_data)
print(predictions)
```

## 📞 Support

For questions and support, please contact: jamalnabila3709@gmail.com

---

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Documentation automatically maintained by the Equipment Failure Prediction System*
"""
        
        with open(os.path.join(self.project_root, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _add_features_section(self, content: str, features: List[Dict[str, Any]]) -> str:
        """Add features section to README"""
        features_section = self._generate_features_markdown(features)
        
        # Find insertion point (after project overview)
        overview_end = content.find("## 🚀 Quick Start")
        if overview_end == -1:
            overview_end = len(content)
        
        new_content = (
            content[:overview_end] + 
            "\n## 📊 Key Features\n\n" + 
            features_section + 
            "\n\n" + 
            content[overview_end:]
        )
        
        return new_content
    
    def _update_features_section(self, content: str, features: List[Dict[str, Any]], start_pos: int) -> str:
        """Update existing features section"""
        # Find end of features section
        next_section = content.find("\n## ", start_pos + 1)
        if next_section == -1:
            next_section = len(content)
        
        features_section = self._generate_features_markdown(features)
        
        new_content = (
            content[:start_pos] +
            "## 📊 Key Features\n\n" +
            features_section +
            "\n\n" +
            content[next_section:]
        )
        
        return new_content
    
    def _generate_features_markdown(self, features: List[Dict[str, Any]]) -> str:
        """Generate markdown for features list"""
        markdown = ""
        
        # Group features by category
        categories = {}
        for feature in features:
            category = feature.get('category', 'General')
            if category not in categories:
                categories[category] = []
            categories[category].append(feature)
        
        for category, feature_list in categories.items():
            markdown += f"### {category}\n\n"
            for feature in feature_list:
                status_icon = self._get_status_icon(feature.get('status', 'planned'))
                markdown += f"- {status_icon} **{feature['name']}**: {feature['description']}\n"
            markdown += "\n"
        
        # Add completion statistics
        total_features = len(features)
        completed_features = len([f for f in features if f.get('status') == 'completed'])
        completion_pct = (completed_features / total_features * 100) if total_features > 0 else 0
        
        markdown += f"**Project Progress:** {completed_features}/{total_features} features completed ({completion_pct:.1f}%)\n\n"
        
        return markdown
    
    def _get_status_icon(self, status: str) -> str:
        """Get emoji icon for feature status"""
        icons = {
            'completed': '✅',
            'in_progress': '🔄',
            'planned': '📋',
            'testing': '🧪',
            'deprecated': '❌'
        }
        return icons.get(status, '📋')
    
    def _update_last_modified(self, content: str) -> str:
        """Update last modified timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Look for existing timestamp
        last_updated_pattern = r"\*Last updated: [^*]+\*"
        if re.search(last_updated_pattern, content):
            content = re.sub(last_updated_pattern, f"*Last updated: {timestamp}*", content)
        else:
            # Add timestamp at the end
            content += f"\n\n---\n\n*Last updated: {timestamp}*\n*Documentation automatically maintained by the Equipment Failure Prediction System*\n"
        
        return content
    
    def generate_api_documentation(self):
        """Auto-generate API documentation from code"""
        api_docs = {
            "title": "Equipment Failure Prediction API Documentation",
            "version": self.docs_config["version"],
            "generated_at": datetime.now().isoformat(),
            "endpoints": [],
            "models": [],
            "examples": []
        }
        
        # Scan API files
        api_files = ["equipment_api.py", "production_predict_function.py"]
        
        for filename in api_files:
            filepath = os.path.join(self.project_root, filename)
            if os.path.exists(filepath):
                endpoints = self._extract_api_endpoints(filepath)
                api_docs["endpoints"].extend(endpoints)
        
        # Generate markdown documentation
        self._write_api_docs_markdown(api_docs)
        
        return api_docs
    
    def _extract_api_endpoints(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from Python file"""
        endpoints = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to find route decorators
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Look for route decorators
                    for decorator in node.decorator_list:
                        if self._is_route_decorator(decorator):
                            endpoint_info = self._extract_endpoint_info(node, decorator, content)
                            if endpoint_info:
                                endpoints.append(endpoint_info)
        
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
        
        return endpoints
    
    def _is_route_decorator(self, decorator) -> bool:
        """Check if decorator is a route decorator"""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr in ['route', 'get', 'post', 'put', 'delete']
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id in ['route']
        return False
    
    def _extract_endpoint_info(self, func_node, decorator, content: str) -> Optional[Dict[str, Any]]:
        """Extract endpoint information from function and decorator"""
        try:
            # Get function name and docstring
            func_name = func_node.name
            docstring = ast.get_docstring(func_node) or "No description available"
            
            # Extract route path and methods
            route_path = "/"
            methods = ["GET"]
            
            if isinstance(decorator, ast.Call) and decorator.args:
                if isinstance(decorator.args[0], ast.Str):
                    route_path = decorator.args[0].s
                elif isinstance(decorator.args[0], ast.Constant):
                    route_path = decorator.args[0].value
            
            # Extract methods from decorator keywords
            for keyword in decorator.keywords if isinstance(decorator, ast.Call) else []:
                if keyword.arg == 'methods':
                    if isinstance(keyword.value, ast.List):
                        methods = [elt.s if isinstance(elt, ast.Str) else elt.value 
                                 for elt in keyword.value.elts]
            
            return {
                "function_name": func_name,
                "path": route_path,
                "methods": methods,
                "description": docstring.split('\n')[0],  # First line of docstring
                "full_description": docstring
            }
        
        except Exception:
            return None
    
    def _write_api_docs_markdown(self, api_docs: Dict[str, Any]):
        """Write API documentation to markdown file"""
        markdown_content = f"""# {api_docs['title']}

**Version:** {api_docs['version']}  
**Generated:** {api_docs['generated_at']}

## Overview

This API provides endpoints for equipment failure prediction and maintenance management.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

All API requests require authentication. Include your API key in the request headers:

```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

"""
        
        for endpoint in api_docs['endpoints']:
            methods_str = ', '.join(endpoint['methods'])
            markdown_content += f"""### {endpoint['function_name']}

**Path:** `{endpoint['path']}`  
**Methods:** {methods_str}

{endpoint['description']}

```http
{endpoint['methods'][0]} {endpoint['path']}
```

{endpoint['full_description']}

---

"""
        
        markdown_content += f"""
## Error Responses

All endpoints return standard HTTP status codes and JSON error responses:

```json
{{
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "{datetime.now().isoformat()}"
}}
```

## Rate Limiting

API requests are limited to 1000 requests per hour per API key.

---

*Generated automatically from source code on {api_docs['generated_at']}*
"""
        
        api_docs_path = os.path.join(self.project_root, "API_DOCUMENTATION.md")
        with open(api_docs_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    def update_changelog(self, version: str, changes: List[str], change_type: str = "feature"):
        """Update changelog with new version"""
        changelog_path = os.path.join(self.project_root, "CHANGELOG.md")
        
        date = datetime.now().strftime("%Y-%m-%d")
        
        # Prepare new entry
        new_entry = f"""## Version {version} - {date}

### {change_type.title()}
"""
        
        for change in changes:
            new_entry += f"- {change}\n"
        
        new_entry += "\n"
        
        # Read existing content
        existing_content = ""
        if os.path.exists(changelog_path):
            with open(changelog_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # Create or update changelog
        if not existing_content:
            content = f"""# Changelog

All notable changes to the Equipment Failure Prediction System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{new_entry}"""
        else:
            # Insert new entry after header
            lines = existing_content.split('\n')
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith('## '):
                    header_end = i
                    break
            
            if header_end == 0:
                # No existing versions, add after header
                for i, line in enumerate(lines):
                    if line.strip() == "":
                        header_end = i + 1
                        break
            
            content = '\n'.join(lines[:header_end]) + '\n' + new_entry + '\n'.join(lines[header_end:])
        
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def sync_all_documentation(self):
        """Synchronize all documentation files"""
        print("🔄 Synchronizing documentation...")
        
        # Load current features
        features_file = os.path.join(self.project_root, "FEATURES.json")
        features = []
        if os.path.exists(features_file):
            with open(features_file, 'r') as f:
                features_data = json.load(f)
                features = features_data.get('features', [])
        
        # Update README
        self.update_readme_features(features)
        print("✅ README.md updated")
        
        # Generate API documentation
        self.generate_api_documentation()
        print("✅ API documentation generated")
        
        # Update version and timestamp
        self.docs_config["last_updated"] = datetime.now().isoformat()
        self._save_docs_config()
        
        print(f"📝 Documentation synchronized at {self.docs_config['last_updated']}")
    
    def _save_docs_config(self):
        """Save documentation configuration"""
        config_file = os.path.join(self.project_root, "docs_config.json")
        with open(config_file, 'w') as f:
            json.dump(self.docs_config, f, indent=2, default=str)

def auto_update_docs_on_change():
    """Monitor files and auto-update documentation"""
    updater = DocumentationUpdater()
    
    # Check if auto-update is enabled
    if not updater.docs_config.get("auto_update", True):
        return
    
    # Sync all documentation
    updater.sync_all_documentation()
    
    return updater

# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        updater = DocumentationUpdater()
        
        if command == "sync":
            updater.sync_all_documentation()
        elif command == "api":
            updater.generate_api_documentation()
            print("✅ API documentation generated")
        elif command == "changelog":
            if len(sys.argv) >= 4:
                version = sys.argv[2]
                changes = sys.argv[3:]
                updater.update_changelog(version, changes)
                print(f"✅ Changelog updated for version {version}")
            else:
                print("Usage: python docs_updater.py changelog <version> <change1> <change2> ...")
        else:
            print("Unknown command. Available: sync, api, changelog")
    else:
        # Default: sync all documentation
        auto_update_docs_on_change()
        print("📚 Documentation update complete!")
