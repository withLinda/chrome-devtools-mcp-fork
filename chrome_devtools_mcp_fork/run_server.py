#!/usr/bin/env python3
"""
Standalone entry point for Claude Code execution.
This file can be executed directly without import issues.
"""

import sys
import os
from pathlib import Path

# Add package directory to path
package_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(package_dir))
sys.path.insert(0, str(package_dir.parent))

# Import and run main
from main import main

if __name__ == "__main__":
    main()