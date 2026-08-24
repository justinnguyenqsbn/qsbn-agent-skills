#!/usr/bin/env python3
"""
Persist per-(org, project) settings for the ado-sprint-release-note skill,
so the user is only asked "where should this go in the wiki?" (and similar
one-time setup questions) once per project instead of on every run.

Stored at ~/.claude/ado-sprint-release-note/config.json, keyed by "org|project".

Usage:
  python config.py get   --org <org> --project <project>
  python config.py set   --org <org> --project <project> \
      --wiki <wiki-identifier> --team "<team name>" \
      --wiki-path-template "/Product/Sprint Releases/Release Note - {sprint_name}" \
      [--known-clients "SLB,Sint Lucas,QSBN"]
  python config.py reset --org <org> --project <project>   # clear just this project
  python config.py reset --all                              # clear everything

`get` prints "{}" (valid, empty JSON) if nothing is stored yet -- that absence
is the signal to the skill that it needs to ask the user and then call `set`.

`--known-clients` is optional and only relevant to projects (like ChatMate365)
whose work items sometimes belong to a specific customer/client rather than
being generic product work -- it's a comma-separated roster of client names
(e.g. "SLB,Sint Lucas,QSBN") the skill uses to offer client-scoping when
drafting the email deliverable. Projects with no roster saved just skip that
question -- every item is treated as generic. Passing --known-clients on a
`set` call replaces the whole saved roster, so include existing entries too
when adding a new client, not just the new one.
"""
import argparse
import json
import os
import sys

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".claude", "ado-sprint-release-note", "config.json")


def load():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def key(org, project):
    return f"{org}|{project}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["get", "set", "reset"])
    p.add_argument("--org")
    p.add_argument("--project")
    p.add_argument("--wiki")
    p.add_argument("--team")
    p.add_argument("--wiki-path-template", dest="wiki_path_template",
                    help="Use {sprint_name} as the placeholder, e.g. 'Sprint 27'")
    p.add_argument("--known-clients", dest="known_clients",
                    help="Comma-separated client/customer roster for this project, e.g. 'SLB,Sint Lucas,QSBN'. Replaces the whole saved roster.")
    p.add_argument("--all", action="store_true", help="With reset: clear every stored project")
    args = p.parse_args()

    data = load()

    if args.action == "get":
        if not args.org or not args.project:
            print(json.dumps({"error": "get requires --org and --project"}), file=sys.stderr)
            sys.exit(1)
        print(json.dumps(data.get(key(args.org, args.project), {}), indent=2))

    elif args.action == "set":
        if not (args.org and args.project and args.wiki and args.wiki_path_template):
            print(json.dumps({"error": "set requires --org --project --wiki --wiki-path-template"}), file=sys.stderr)
            sys.exit(1)
        entry = {
            "wiki": args.wiki,
            "team": args.team,
            "wiki_path_template": args.wiki_path_template,
        }
        if args.known_clients:
            entry["known_clients"] = [c.strip() for c in args.known_clients.split(",") if c.strip()]
        data[key(args.org, args.project)] = entry
        save(data)
        print(json.dumps({"saved": data[key(args.org, args.project)]}, indent=2))

    elif args.action == "reset":
        if args.all:
            save({})
            print(json.dumps({"reset": "all"}))
        else:
            if not args.org or not args.project:
                print(json.dumps({"error": "reset requires --org and --project, or --all"}), file=sys.stderr)
                sys.exit(1)
            data.pop(key(args.org, args.project), None)
            save(data)
            print(json.dumps({"reset": key(args.org, args.project)}))


if __name__ == "__main__":
    main()
