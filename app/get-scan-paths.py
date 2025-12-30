#!/usr/bin/env python3
import os
import sys
import urllib.parse
import json

persisted_file = "/config/scan_paths"
paths = []

# Read paths from file
if os.path.exists(persisted_file):
    try:
        with open(persisted_file, 'r') as f:
            for line in f:
                line = line.strip().rstrip('\r')
                if line:
                    paths.append(line)
    except Exception:
        pass

# Default to /scan if no paths found
if not paths:
    paths = ["/"]  # Single slash represents /scan

# Check which paths exist and which don't
valid_paths = []
invalid_paths = []

for path in paths:
    # Convert relative path to absolute for checking existence
    if path == "/":
        abs_path = "/scan"
    else:
        abs_path = "/scan" + path  # path already starts with /
    
    if os.path.isdir(abs_path):
        valid_paths.append(path)
    else:
        invalid_paths.append(path)

# URL-encode each path
encoded_valid_paths = [urllib.parse.quote(p, safe="/") for p in valid_paths]
encoded_invalid_paths = [urllib.parse.quote(p, safe="/") for p in invalid_paths]

# Output JSON
result = {
    "success": True,
    "paths": encoded_valid_paths,
    "invalid_paths": encoded_invalid_paths
}

print(json.dumps(result))
