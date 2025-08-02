#!/usr/bin/env python3
"""
Standalone entry point for Claude Code execution.
This file can be executed directly without import issues.
"""

import sys
from pathlib import Path

# Add package directory to path
package_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(package_dir))
sys.path.insert(0, str(package_dir.parent))

# Import and run main - after path setup to avoid E402
from main import main  # noqa: E402

if __name__ == "__main__":
    main()
