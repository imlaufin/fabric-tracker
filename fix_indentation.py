import os
import sys

TARGET_FOLDER = "fabric_tracker_tk"

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
            line = line.replace("\t", "    ")  # Convert tabs to 4 spaces
        fixed_lines.append(line)

    # Try compiling to detect indentation errors
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

def main():
    if not os.path.exists(TARGET_FOLDER):
        print(f"[ERROR] Folder '{TARGET_FOLDER}' not found.")
        sys.exit(1)

    total_fixed = 0
    for root, _, files in os.walk(TARGET_FOLDER):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                if fix_file(path):
                    total_fixed += 1

    print(f"\nScan complete. Files fixed: {total_fixed}")
    # Exit 0 even if fixed, so build continues
    sys.exit(0)

if __name__ == "__main__":
    main()
