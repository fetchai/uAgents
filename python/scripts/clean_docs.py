import os
import re


def clean_headings_remove_links(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                updated_lines = []
                for line in lines:
                    header_match = re.match(r"^(#+)\s+(.*)", line)

                    url_pattern = re.compile(r"<a id=\"(.*?)\">(.*?)</a>")
                    sub_line = re.sub(url_pattern, "", line)

                    if header_match:
                        level = len(
                            header_match.group(1)
                        )  # Number of `#` indicates header level
                        header_text = header_match.group(2).strip()
                        header_text = header_text.replace("`", "")
                        # Reconstruct the header line
                        updated_lines.append(f"{'#' * level} {header_text}\n")
                    else:
                        updated_lines.append(sub_line)

                # Write the updated content back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(updated_lines)


# clean up mds...
clean_headings_remove_links("../docs/api/uagents")
