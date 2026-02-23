import ast
import os

services_dir = r"c:\Users\shilo\Documents\Github\gred_in_multiagent_orchestrator\tools\gimo_server\services"

count = 0
for root, _, files in os.walk(services_dir):
    for filename in files:
        if filename.endswith(".py"):
            filepath = os.path.join(root, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            
            try:
                tree = ast.parse(source)
            except Exception as e:
                print(f"Skipping {filename}: {e}")
                continue

            lines = source.split('\n')
            inserts = []
            
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        # Start from node.lineno - 1 and find the first line that ends the class declaration (contains colon)
                        # More reliably, we just look forward from lineno-1 until we see a line ending with ':' or containing ':' inside it at the end of declaration.
                        colon_line = node.lineno - 1
                        # While not found, advance
                        # To handle multi-line base classes
                        # a simple heuristic is: find the first ':' after the class definition line
                        # Actually, just use ast node properties if possible, but ast doesn't store the exact char position in Python < 3.8 easily.
                        # We can just iterate until we find ':' not inside a string
                        # For simplicity, let's just find the first line with ':' after lineno-1
                        temp_line = colon_line
                        while temp_line <= len(lines):
                            if ':' in lines[temp_line]:
                                colon_line = temp_line
                                break
                            temp_line += 1
                        
                        class_name = node.name
                        indent = len(lines[node.lineno-1]) - len(lines[node.lineno-1].lstrip())
                        doc_indent = " " * (indent + 4)
                        
                        inserts.append((colon_line, f'{doc_indent}"""Provee logica de negocio para {class_name}."""'))
            
            if inserts:
                inserts.sort(key=lambda x: x[0], reverse=True)
                for line_idx, docstring in inserts:
                    lines.insert(line_idx + 1, docstring)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write('\n'.join(lines))
                    count += 1
                    print(f"Added docstrings to {filename}")

print(f"Done. Modified {count} files.")
