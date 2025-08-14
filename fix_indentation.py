import os

TARGET_FOLDER = "fabric_tracker_tk"
FIX_INDENTATION = True  # Set to False if you only want to check

def check_and_fix_file(filepath):
    with open(filepath, "rb") as f:
        raw = f.read()

    # Detect tabs
    has_tabs = b"\t" in raw

    # Convert to string for replacing
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        print(f"⚠ Skipping non-UTF8 file: {filepath}")
        return

    fixed_text = text
    if FIX_INDENTATION and has_tabs:
        fixed_text = text.replace("\t", "    ")

    # Check for inconsistent indentation (lines starting with spaces but not multiple of 4)
    bad_lines = []
    for i, line in enumerate(fixed_text.splitlines(), start=1):
        if line.startswith(" ") and not line.lstrip().startswith("#"):  # ignore pure comments
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 4 != 0:
                bad_lines.append((i, leading_spaces, line))

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

def main():
    for root, _, files in os.walk(TARGET_FOLDER):
        for file in files:
            if file.endswith(".py"):
                check_and_fix_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
