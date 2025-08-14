import os
import re
import sys

TARGET_FOLDER = "fabric_tracker_tk"

# === 1. Indentation Fixer ===
def fix_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print(f"[WARN] Skipping non-UTF8 file: {filepath}")
        return False

    changed = False
    fixed_lines = []

    for line in lines:
        if "\t" in line:
            changed = True
            line = line.replace("\t", "    ")
        fixed_lines.append(line)

    try:
        compile("".join(fixed_lines), filepath, "exec")
    except IndentationError:
        print(f"[WARN] IndentationError found in {filepath}, attempting auto-fix.")
        changed = True
        uniform_lines = []
        for line in fixed_lines:
            stripped = line.lstrip()
            indent_level = (len(line) - len(stripped)) // 4
            uniform_lines.append((" " * 4 * indent_level) + stripped)
        fixed_lines = uniform_lines

    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)
        print(f"[FIXED] {filepath}")
        return True
    else:
        print(f"[OK] {filepath} is clean.")
        return False

# === 2. Bad Import Checker ===
def check_bad_imports():
    bad_imports = []
    patterns = [
        re.compile(r"^\s*import\s+db\b"),
        re.compile(r"^\s*from\s+db\s+import\b")
    ]
    for root, _, files in os.walk(TARGET_FOLDER):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, start=1):
                        for pat in patterns:
                            if pat.search(line):
                                bad_imports.append((path, lineno, line.strip()))
    return bad_imports

# === Main ===
def main():
    if not os.path.exists(TARGET_FOLDER):
        print(f"[ERROR] Folder '{TARGET_FOLDER}' not found.")
        sys.exit(1)

    # Fix indentation
    total_fixed = 0
    for root, _, files in os.walk(TARGET_FOLDER):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                if fix_file(path):
                    total_fixed += 1
    print(f"\nIndentation scan complete. Files fixed: {total_fixed}\n")

    # Check imports
    bad_imports = check_bad_imports()
    if bad_imports:
        print("\n[ERROR] Found bad imports that will break in PyInstaller:")
        for path, lineno, line in bad_imports:
            print(f"  {path}:{lineno}  {line}")
        print("\nPlease change them to 'from fabric_tracker_tk import db'.")
        sys.exit(1)

    print("[OK] No bad imports found.")
    sys.exit(0)

if __name__ == "__main__":
    main()
