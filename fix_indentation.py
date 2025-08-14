import os

TARGET_FOLDER = "fabric_tracker_tk"
FILES_TO_FIX_FIRST = ["main.py", "ui_masters.py"]
FIX_INDENTATION = True  # True = fix automatically, False = just report

def fix_file(filepath):
    with open(filepath, "rb") as f:
        raw = f.read()

    # Skip non-UTF8 files
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        print(f"⚠ Skipping non-UTF8 file: {filepath}")
        return

    has_tabs = "\t" in text
    fixed_text = text.replace("\t", "    ") if FIX_INDENTATION else text

    bad_lines = []
    for i, line in enumerate(fixed_text.splitlines(), start=1):
        if line.strip() and not line.lstrip().startswith("#"):
            spaces = len(line) - len(line.lstrip())
            if spaces % 4 != 0:
                bad_lines.append((i, spaces, line))

    if has_tabs or bad_lines:
        print(f"\n--- {filepath} ---")
        if has_tabs:
            print("Tabs found.")
        if bad_lines:
            for lineno, spaces, content in bad_lines:
                print(f"Line {lineno}: {spaces} spaces → {content}")

        if FIX_INDENTATION:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed_text)
            print("✅ Fixed indentation.")
    else:
        print(f"[OK] {filepath} is clean.")

def main():
    # Step 1: Fix specific files first
    for fname in FILES_TO_FIX_FIRST:
        path = os.path.join(TARGET_FOLDER, fname)
        if os.path.exists(path):
            fix_file(path)
        else:
            print(f"⚠ {fname} not found in {TARGET_FOLDER}")

    # Step 2: Scan all .py files in TARGET_FOLDER
    for root, _, files in os.walk(TARGET_FOLDER):
        for file in files:
            if file.endswith(".py") and file not in FILES_TO_FIX_FIRST:
                fix_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
