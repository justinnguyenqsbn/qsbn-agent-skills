#!/usr/bin/env python3
"""
Fetch everything needed to draft a non-technical Sprint Release Note:
the sprint's work items, each one's owning Feature/Epic (walking up the
parent chain even when the Feature/Epic itself isn't in this sprint), and
the description text of Features and top-level stories to summarize from.

Handles the same fiddly bits as the sibling ado-sprint-release-report skill's
fetch script (team iteration path vs. classification-node path for WIQL),
plus:
  - Defaulting to the most recently COMPLETED sprint when --sprint is
    omitted, using the `timeFrame` attribute Azure Boards already computes
    (past/current/future) rather than hand-rolling date math. A release note
    describes what shipped, so the default is the last finished sprint, not
    the one still in progress.
  - Grouping items by their nearest ancestor of type "Feature" (or "Epic" if
    no Feature exists in the chain), so the note can be organized by
    capability instead of by work-item category.
  - Pulling System.Description for every Feature and every grouped item, with
    HTML tags stripped to plain text, since that's usually where the "why
    are we building this" context lives that a title alone won't give you.

Usage:
  python fetch_release_data.py --org https://dev.azure.com/qsbnproducts \
      --project ChatMate365 [--sprint 27] \
      [--team "ChatMate365 Team"]

Prints a single JSON object to stdout. Omit --sprint to get the most
recently completed sprint for that team.
"""
import argparse
import html
import json
import platform
import re
import subprocess
import sys

IS_WINDOWS = platform.system() == "Windows"

GROUPING_TYPES = {"Feature", "Epic"}


def az(args):
    proc = subprocess.run(
        ["az"] + args + ["-o", "json"],
        capture_output=True, text=True, shell=IS_WINDOWS
    )
    if proc.returncode != 0:
        raise RuntimeError(f"az {' '.join(args)} failed:\n{proc.stderr}")
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def strip_html(raw):
    if not raw:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", raw)
    text = re.sub(r"</(p|div|li)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def list_iterations(org, project, team):
    return az(["boards", "iteration", "team", "list",
               "--team", team, "--project", project, "--org", org])


def pick_iteration(iterations, sprint_label):
    if sprint_label:
        for it in iterations:
            if it["name"].lower() == sprint_label.lower():
                return it
        names = ", ".join(i["name"] for i in iterations)
        raise RuntimeError(f"No iteration named '{sprint_label}' found. Available: {names}")

    past = [it for it in iterations if it["attributes"].get("timeFrame") == "past"
            and it["attributes"].get("finishDate")]
    if past:
        return max(past, key=lambda it: it["attributes"]["finishDate"])

    current = [it for it in iterations if it["attributes"].get("timeFrame") == "current"]
    if current:
        return current[0]

    raise RuntimeError("No past or current iteration found for this team.")


def query_ids(org, project, iteration_path):
    wiql = (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE [System.IterationPath] = '{iteration_path}'"
    )
    result = az(["boards", "query", "--wiql", wiql, "--project", project, "--org", org])
    return [str(r["fields"]["System.Id"]) for r in result]


def fetch_item(org, wid, cache):
    wid = int(wid)
    if wid in cache:
        return cache[wid]
    wi = az(["boards", "work-item", "show", "--id", str(wid), "--org", org])
    f = wi["fields"]
    item = {
        "id": wid,
        "type": f.get("System.WorkItemType"),
        "title": f.get("System.Title"),
        "state": f.get("System.State"),
        "tags": f.get("System.Tags"),
        "parent": f.get("System.Parent"),
        "description": strip_html(f.get("System.Description")),
    }
    cache[wid] = item
    return item


def find_group(org, item, cache):
    """Walk the parent chain looking for the nearest Feature (or Epic if no
    Feature exists above this item). Ancestors are fetched (and cached) even
    if they're outside the sprint, since Features/Epics rarely land in the
    same sprint as their children."""
    seen = set()
    current = item
    while current.get("parent") and current["id"] not in seen:
        seen.add(current["id"])
        parent = fetch_item(org, current["parent"], cache)
        if parent["type"] in GROUPING_TYPES:
            return {"id": parent["id"], "type": parent["type"],
                    "title": parent["title"], "description": parent["description"]}
        current = parent
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--org", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--sprint", default=None, help="Sprint number or full name, e.g. 27 or 'Sprint 27'. Omit for the most recently completed sprint.")
    p.add_argument("--team", default=None, help="Defaults to '<project> Team'")
    args = p.parse_args()

    team = args.team or f"{args.project} Team"
    sprint_label = None
    if args.sprint:
        sprint_label = args.sprint if args.sprint.lower().startswith("sprint") else f"Sprint {args.sprint}"

    iterations = list_iterations(args.org, args.project, team)
    iteration = pick_iteration(iterations, sprint_label)
    iteration_path = f"{args.project}\\{iteration['name']}"

    ids = query_ids(args.org, args.project, iteration_path)
    cache = {}
    items = [fetch_item(args.org, wid, cache) for wid in ids]
    in_sprint_ids = {it["id"] for it in items}

    for it in items:
        parent_id = it.get("parent")
        it["parent_in_sprint"] = bool(parent_id and int(parent_id) in in_sprint_ids)
        it["group"] = None if it["type"] == "Task" else find_group(args.org, it, cache)

    print(json.dumps({
        "org": args.org,
        "project": args.project,
        "team": team,
        "sprint_name": iteration["name"],
        "iteration_path": iteration_path,
        "start_date": iteration["attributes"].get("startDate"),
        "finish_date": iteration["attributes"].get("finishDate"),
        "time_frame": iteration["attributes"].get("timeFrame"),
        "items": items,
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
