#!/usr/bin/env python3
"""
Debug script to test GitHub service import in Windows environment
"""
import sys
import os
from pathlib import Path

print("=== PJINIT v1.2 Import Debug ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {__file__}")
print()

# Setup paths like service_adapter.py does
techbridge_root = Path(__file__).parent.parent.parent.parent
app_services_path = techbridge_root / "app"

print("Path setup:")
print(f"  techbridge_root: {techbridge_root}")
print(f"  app_services_path: {app_services_path}")
print(f"  techbridge_root exists: {techbridge_root.exists()}")
print(f"  app_services_path exists: {app_services_path.exists()}")
print()

# Add paths to sys.path
paths_to_add = [
    str(techbridge_root),
    str(app_services_path),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f"  Added to sys.path: {path}")
    else:
        print(f"  Already in sys.path: {path}")
print()

# Check if GitHub service file exists
github_service_file = techbridge_root / "app" / "services" / "github.py"
print(f"GitHub service file: {github_service_file}")
print(f"  Exists: {github_service_file.exists()}")
print()

# Try to import GitHub service
print("Attempting imports:")
try:
    print("  Trying: from app.services.github import GitHubService")
    from app.services.github import GitHubService as RealGitHubService
    print("  SUCCESS: GitHub service imported!")
    print(f"  GitHubService class: {RealGitHubService}")
except ImportError as e:
    print(f"  FAILED: {e}")
    print()
    print("  Detailed error information:")
    import traceback
    traceback.print_exc()
    print()
    
    # Try alternative import
    print("  Trying alternative: from services.github import GitHubService")
    try:
        from services.github import GitHubService as RealGitHubService
        print("  SUCCESS with alternative import!")
    except ImportError as e2:
        print(f"  Alternative also failed: {e2}")

print()
print("sys.path contents:")
for i, path in enumerate(sys.path[:10]):  # Show first 10 paths
    print(f"  {i}: {path}")