"""
CLI script to build the local database.
"""
import sys
from pathlib import Path

# Add project root to path so we can import modules
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.ingest import ingest_data

if __name__ == "__main__":
    ingest_data()
