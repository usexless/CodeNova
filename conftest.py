import sys
from pathlib import Path

# Ensure project root is in sys.path so tests can be run from any directory
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
