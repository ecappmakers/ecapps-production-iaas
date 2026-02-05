import json
import sys
import os

def format_backups():
    try:
        # Read the JSON passed from rclone via pipe
        raw_data = sys.stdin.read()
        if not raw_data.strip():
            # Fallback if no files are found
            with open(os.environ["GITHUB_ENV"], "a") as env_file:
                env_file.write("HISTORICAL_HTML=<li>No backups found</li>\n")
                env_file.write("HISTORICAL_TEXT=No backups found.\n")
            return

        files = json.loads(raw_data)
        
        # Sort files by ModTime descending (newest first)
        files.sort(key=lambda x: x.get("ModTime", ""), reverse=True)

        html_lines = []
        text_lines = []

        for f in files:
            name = f.get("Name", "Unknown")
            f_id = f.get("ID", "")
            size_mb = round(f.get("Size", 0) / (1024 * 1024), 2)
            # Standardizing date format
            date_raw = f.get("ModTime", "Unknown")
            date = date_raw.split("T")[0] if "T" in date_raw else date_raw
            url = f"https://drive.google.com/open?id={f_id}"

            html_lines.append(f'<li><a href="{url}">{name}</a> - {size_mb} MB (Uploaded: {date})</li>')
            text_lines.append(f'📄 <a href="{url}">{name}</a>\n📅 {date}\n⚖️ {size_mb} MB\n')

        # Write to GITHUB_ENV using HEREDOC for safety
        with open(os.environ["GITHUB_ENV"], "a") as env_file:
            env_file.write("HISTORICAL_HTML<<EOF\n")
            env_file.write("".join(html_lines) + "\n")
            env_file.write("EOF\n")

            env_file.write("HISTORICAL_TEXT<<EOF\n")
            env_file.write("\n".join(text_lines) + "\n")
            env_file.write("EOF\n")

    except Exception as e:
        print(f"Error processing metadata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    format_backups()