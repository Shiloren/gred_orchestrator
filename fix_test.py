import re

with open('tests/test_storage_service.py', 'r') as f:
    content = f.read()

mock_gics = """
class MockGics:
    def __init__(self):
        self.data = {}
    
    def put(self, key, value):
        self.data[key] = value
        
    def get(self, key):
        if key in self.data:
            return {"key": key, "fields": self.data[key], "timestamp": "2026-01-01T00:00:00Z"}
        return None
        
    def scan(self, prefix="", include_fields=False):
        results = []
        for k, v in self.data.items():
            if k.startswith(prefix):
                if include_fields:
                    results.append({"key": k, "fields": v, "timestamp": "2026-01-01T00:00:00Z"})
                else:
                    results.append({"key": k, "timestamp": "2026-01-01T00:00:00Z"})
        return results

"""

if 'class MockGics' not in content:
    content = content.replace("from tools.gimo_server.services.storage_service import StorageService", 
                              "from tools.gimo_server.services.storage_service import StorageService\n" + mock_gics)

# Replace the test body
def replacer(match):
    body = match.group(1)
    
    # Remove try block and finally block
    body = re.sub(r'    original_db_path = StorageService\.DB_PATH\n', '', body)
    body = re.sub(r'    StorageService\.DB_PATH = db_path\n', '', body)
    body = re.sub(r'    db_path = tmp_path / "gimo_test\.db"\n', '', body)
    body = re.sub(r'    try:\n', '', body)
    
    lines = body.split('\n')
    new_lines = []
    for line in lines:
        if line == '        storage = StorageService()':
            new_lines.append('    storage = StorageService(gics=MockGics())')
        elif line.startswith('        '):
            new_lines.append(line[4:])
        elif line.startswith('    finally:'):
            break
        else:
            new_lines.append(line)
            
    return '\n'.join(new_lines) + '\n'

pattern = r'(    db_path = tmp_path / "gimo_test\.db".*?    finally:\n        StorageService\.DB_PATH = original_db_path\n)'
content = re.sub(pattern, replacer, content, flags=re.DOTALL)

with open('tests/test_storage_service.py', 'w') as f:
    f.write(content)
