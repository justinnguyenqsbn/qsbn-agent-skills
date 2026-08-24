#!/usr/bin/env python3
"""
Create or update a wiki page, handling the ETag dance az devops wiki page
update requires (it 404s helpfully, not silently, if the page is new).

Usage:
  python publish_wiki_page.py --org https://dev.azure.com/qsbnproducts \
      --project ChatMate365 --wiki ChatMate365.wiki \
      --path "/ChatMate365/Development/Sprint Activity/Sprint Releases/Sprint Release Note - Sprint 27" \
      --file-path note.md

On Windows, pass --path through PowerShell (not Git Bash) -- Git Bash mangles
a leading "/" into a filesystem path before az ever sees it.
"""
import argparse
import json
import platform
import subprocess
import sys

IS_WINDOWS = platform.system() == "Windows"


def az(args):
    proc = subprocess.run(["az"] + args + ["-o", "json"], capture_output=True, text=True, shell=IS_WINDOWS)
    return proc.returncode, proc.stdout, proc.stderr


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--org", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--wiki", required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--file-path", required=True)
    args = p.parse_args()

    rc, out, err = az(["devops", "wiki", "page", "show",
                        "--wiki", args.wiki, "--project", args.project,
                        "--org", args.org, "--path", args.path])

    if rc == 0:
        etag = json.loads(out)["eTag"].strip('"')
        rc2, out2, err2 = az(["devops", "wiki", "page", "update",
                               "--wiki", args.wiki, "--project", args.project,
                               "--org", args.org, "--path", args.path,
                               "--file-path", args.file_path,
                               "--version", etag])
        if rc2 != 0:
            print(f"Update failed:\n{err2}", file=sys.stderr)
            sys.exit(1)
        print(f"Updated existing page: {args.path}")
    else:
        rc2, out2, err2 = az(["devops", "wiki", "page", "create",
                               "--wiki", args.wiki, "--project", args.project,
                               "--org", args.org, "--path", args.path,
                               "--file-path", args.file_path])
        if rc2 != 0:
            print(f"Create failed:\n{err2}", file=sys.stderr)
            sys.exit(1)
        print(f"Created new page: {args.path}")


if __name__ == "__main__":
    main()
