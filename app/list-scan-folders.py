#!/usr/bin/env python3
import os
import sys
import urllib.parse
import json
import subprocess

SCAN_ROOT = "/scan"
MAX_DEPTH = 2
MAX_FOLDERS = 500
EXCLUDE_FILE = "/config/exclude"

def read_exclude_patterns():
    """Read exclude patterns from file or environment variable"""
    patterns = []
    
    # Read from exclude file
    if os.path.exists(EXCLUDE_FILE):
        try:
            with open(EXCLUDE_FILE, 'r') as f:
                for line in f:
                    line = line.strip().rstrip('\r')
                    if line and not line.startswith('#'):
                        line = line.lstrip('/')
                        if line:
                            patterns.append(line)
        except Exception:
            pass
    
    # Read from EXCLUDE environment variable
    exclude_raw = os.environ.get('EXCLUDE', '')
    if exclude_raw:
        for line in exclude_raw.split('\n'):
            line = line.strip().rstrip('\r')
            if line and not line.startswith('#'):
                line = line.lstrip('/')
                if line:
                    patterns.append(line)
    
    return patterns

def find_folders():
    """Find folders under SCAN_ROOT with exclude patterns"""
    exclude_patterns = read_exclude_patterns()
    
    # Build find command
    find_cmd = ['find', SCAN_ROOT, '-mindepth', '1', '-maxdepth', str(MAX_DEPTH)]
    
    # Add exclude patterns
    if exclude_patterns:
        find_cmd.extend(['('])
        for i, pattern in enumerate(exclude_patterns):
            if i > 0:
                find_cmd.extend(['-o'])
            find_cmd.extend(['-path', f'*/{pattern}', '-o', '-path', f'*/{pattern}/*'])
        find_cmd.extend([')', '-prune', '-o'])
    
    find_cmd.extend(['-type', 'd', '-print0'])
    
    # Execute find command
    try:
        result = subprocess.run(find_cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return []
        
        # Split null-separated output
        folders = []
        for path in result.stdout.split('\0'):
            if not path:
                continue
            
            # Get relative path
            rel_path = path[len(SCAN_ROOT):]
            if not rel_path:
                continue
            
            # Calculate depth
            depth = rel_path.count('/')
            
            # URL-encode the path
            encoded_path = urllib.parse.quote(rel_path, safe="/")
            
            folders.append({
                'path': encoded_path,
                'depth': depth
            })
            
            if len(folders) >= MAX_FOLDERS:
                break
        
        # Sort by path
        folders.sort(key=lambda x: x['path'])
        return folders
        
    except Exception:
        return []

def main():
    # Ensure scan root exists
    os.makedirs(SCAN_ROOT, exist_ok=True)
    
    # Find folders
    folders = find_folders()
    
    # Output JSON
    result = {
        'success': True,
        'folders': folders
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()
