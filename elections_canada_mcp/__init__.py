"""
Elections Canada MCP Package

This package provides access to Canadian federal election data from 2021 via a Model Context Protocol (MCP) server.
"""

import os
import re
from pathlib import Path

def _get_version_from_pyproject():
    """Get the package version from pyproject.toml."""
    try:
        # Find the pyproject.toml file
        package_dir = Path(__file__).resolve().parent
        project_root = package_dir.parent
        pyproject_path = project_root / 'pyproject.toml'
        
        # If not found in development mode, try to find it in installed package
        if not pyproject_path.exists():
            return '0.0.0'  # Fallback version
            
        # Read the pyproject.toml file
        with open(pyproject_path, 'r') as f:
            content = f.read()
            
        # Extract the version using regex
        version_match = re.search(r'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"', content)
        if version_match:
            return version_match.group(1)
        return '0.0.0'  # Fallback version
    except Exception:
        return '0.0.0'  # Fallback version in case of any errors

__version__ = _get_version_from_pyproject()
