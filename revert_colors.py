from pathlib import Path

ui_dir = Path(r"z:\Projects\Working\Desktop-app-Stock\ui")

replacements = {
    "#2563EB": "#8B5E3C",
    "#2563eb": "#8b5e3c",
    "rgba(37, 99, 235,": "rgba(139, 94, 60,",
    "#1D4ED8": "#734D31",
    "#1d4ed8": "#734d31",
    "#3B82F6": "#8B5E3C",
    "#3b82f6": "#8b5e3c",
    "rgba(59, 130, 246,": "rgba(139, 94, 60,",
}

count = 0
for py_file in ui_dir.rglob("*.*"):
    if py_file.suffix not in ['.py', '.qss']:
        continue
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = content
    for old, new in replacements.items():
        modified = modified.replace(old, new)
        
    if modified != content:
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(modified)
        print(f"Updated {py_file.name}")
        count += 1

print(f"Total files updated: {count}")
