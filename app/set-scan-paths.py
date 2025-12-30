#!/usr/bin/env python3
import os
import sys
import json
import urllib.parse
import datetime

# Configuration
LOG_FILE = os.environ.get('DUC_LOG_FILE', '/var/log/duc.log')
PERSISTED_SCAN_PATHS_FILE = '/config/scan_paths'
SCAN_ROOT = '/scan'

def urldecode_path(path):
    """URL decode a path string"""
    return urllib.parse.unquote(path)

def normalize_path(path):
    """Normalize client paths to be relative to SCAN_ROOT with / prefix"""
    if path == '/' or path == '':
        return "/"  # Single slash represents /scan
    
    # Remove /scan prefix if present
    if path.startswith(SCAN_ROOT + '/'):
        return path[len(SCAN_ROOT):]  # Remove /scan prefix, keep leading /
    elif path == SCAN_ROOT:
        return "/"
    
    # Ensure path starts with /
    if not path.startswith('/'):
        path = '/' + path
    
    return path

def validate_path(path):
    """Validate a path exists and is under SCAN_ROOT"""
    # Convert relative path to absolute for validation
    if path == "/":
        abs_path = SCAN_ROOT
    else:
        abs_path = SCAN_ROOT + path  # path already starts with /
    
    # Check for path traversal
    if '..' in path:
        return False, "Invalid path (contains '..')"
    
    # Check if path exists and is a directory
    if not os.path.isdir(abs_path):
        return False, "Path does not exist or is not a directory"
    
    return True, None

def read_post_data():
    """Read POST data from stdin"""
    content_length = os.environ.get('CONTENT_LENGTH')
    if not content_length or int(content_length) == 0:
        return None, "No data received"
    
    try:
        content_length = int(content_length)
        post_data = sys.stdin.read(content_length)
        return post_data, None
    except Exception as e:
        return None, f"Failed to read POST data: {str(e)}"

def parse_paths(post_data):
    """Parse paths from POST data"""
    content_type = os.environ.get('CONTENT_TYPE', '')
    
    if 'application/json' in content_type:
        # Parse JSON input
        try:
            data = json.loads(post_data)
            paths = data.get('paths', [])
            if not isinstance(paths, list):
                return None, "Invalid JSON: paths must be an array"
            return paths, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON input: {str(e)}"
    else:
        # Fallback to form-encoded format
        try:
            # Parse form data like paths=path1,path2,path3
            for param in post_data.split('&'):
                if param.startswith('paths='):
                    encoded_paths = param[6:].split(',')
                    paths = [urllib.parse.unquote(p) for p in encoded_paths if p]
                    return paths, None
            return None, "No paths found in form data"
        except Exception as e:
            return None, f"Failed to parse form data: {str(e)}"

def log_message(message):
    """Log message to log file"""
    try:
        with open(LOG_FILE, 'a') as f:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} {message}\n")
    except Exception:
        pass

def main():
    # Read POST data
    post_data, error = read_post_data()
    if error:
        print(json.dumps({'success': False, 'error': error}))
        sys.exit(0)
    
    # Parse paths
    paths, error = parse_paths(post_data)
    if error:
        print(json.dumps({'success': False, 'error': error}))
        sys.exit(0)
    
    if not paths:
        print(json.dumps({'success': False, 'error': 'No valid paths provided in request'}))
        sys.exit(0)
    
    # Ensure config directory exists
    os.makedirs('/config', exist_ok=True)
    
    # Process and validate paths
    valid_paths = []
    for p in paths:
        # Trim whitespace
        p = p.strip()
        if not p:
            continue
        
        # URL decode if needed
        if '%' in p:
            p = urldecode_path(p)
        
        # Normalize path
        p = normalize_path(p)
        
        # Validate path
        is_valid, error_msg = validate_path(p)
        if not is_valid:
            print(json.dumps({
                'success': False,
                'error': {'error': error_msg, 'path': p}
            }))
            sys.exit(0)
        
        valid_paths.append(p)
    
    if not valid_paths:
        print(json.dumps({'success': False, 'error': {'error': 'No valid paths selected'}}))
        sys.exit(0)
    
    # Write paths to file
    try:
        with open(PERSISTED_SCAN_PATHS_FILE, 'w') as f:
            for path in valid_paths:
                f.write(path + '\n')
    except Exception as e:
        print(json.dumps({'success': False, 'error': f'Failed to save paths: {str(e)}'}))
        sys.exit(0)
    
    # Log the update
    log_message(f"Updated scan paths: {', '.join(paths)}")
    
    # Success response
    print(json.dumps({'success': True, 'message': 'Scan paths updated'}))

if __name__ == '__main__':
    main()
