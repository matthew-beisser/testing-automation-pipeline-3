#!/usr/bin/env python3
# gh_pr_summary.py
# Summarize all PRs authored by a user across GitHub using the GraphQL API.
# Outputs Markdown (grouped by repo with summary) or CSV.
# Now with repo filtering via --repos / --exclude-repos (globs supported).

import os
import sys
import time
import json
import argparse
import datetime as dt
from collections import defaultdict
from typing import Dict, Any, List, Optional
from fnmatch import fnmatch

GQL_ENDPOINT = "https://api.github.com/graphql"

QUERY = """
query($login:String!, $pageSize:Int!, $after:String, $states:[PullRequestState!]) {
  user(login: $login) {
    login
    pullRequests(first: $pageSize, after: $after, orderBy: {field: CREATED_AT, direction: DESC}, states: $states) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        title
        number
        url
        state
        createdAt
        mergedAt
        closedAt
        additions
        deletions
        changedFiles
        repository { nameWithOwner owner { login } name isPrivate }
        comments { totalCount }
        reviews(states: [APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED, PENDING]) { totalCount }
      }
    }
  }
  rateLimit { remaining resetAt }
}
"""

def http_post(url: str, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    import urllib.request
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            return json.loads(body.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"HTTP error: {e}")

def parse_date(s: Optional[str]) -> Optional[dt.datetime]:
    if not s:
        return None
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))

def within_range(created_at: str, since: Optional[dt.datetime], until: Optional[dt.datetime]) -> bool:
    t = parse_date(created_at)
    if since and t < since:
        return False
    if until and t > until:
        return False
    return True

def repo_allowed(full: str, allow_globs: List[str], deny_globs: List[str]) -> bool:
    # If allow list is provided, must match at least one.
    if allow_globs:
        if not any(fnmatch(full, g) for g in allow_globs):
            return False
    # If deny list is provided, must not match any.
    if deny_globs and any(fnmatch(full, g) for g in deny_globs):
        return False
    return True

def render_markdown(groups: Dict[str, List[Dict[str, Any]]], totals: Dict[str, int]) -> str:
    lines = []
    lines.append("# Pull Request Summary\n")
    lines.append("## Totals")
    lines.append("")
    lines.append(f"- **Total PRs:** {totals['total']}")
    lines.append(f"- **Open:** {totals['OPEN']}, **Closed:** {totals['CLOSED']}, **Merged:** {totals['MERGED']}")
    lines.append(f"- **Additions:** {totals['additions']}  |  **Deletions:** {totals['deletions']}")
    lines.append(f"- **Changed files:** {totals['changedFiles']}")
    lines.append("")

    for repo, prs in sorted(groups.items(), key=lambda x: (-len(x[1]), x[0].lower())):
        lines.append(f"## {repo}  \nPRs: {len(prs)}")
        lines.append("")
        lines.append("| # | Title | State | Created | Merged | + / - | Files | Comments | Reviews | Link |")
        lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---|")
        for pr in prs:
            created = parse_date(pr["createdAt"])
            merged = parse_date(pr["mergedAt"])
            created_s = created.strftime("%Y-%m-%d") if created else ""
            merged_s = merged.strftime("%Y-%m-%d") if merged else ""
            add_del = f"{pr['additions']} / {pr['deletions']}"
            # Escape pipes in titles
            title = pr["title"].replace("|", "\\|")
            lines.append(
                f"| {pr['number']} "
                f"| {title} "
                f"| {pr['state']} "
                f"| {created_s} "
                f"| {merged_s} "
                f"| {add_del} "
                f"| {pr['changedFiles']} "
                f"| {pr['comments']['totalCount']} "
                f"| {pr['reviews']['totalCount']} "
                f"| [link]({pr['url']}) |"
            )
        lines.append("")
    return "\n".join(lines)

def render_csv(rows: List[Dict[str, Any]]) -> str:
    import csv
    from io import StringIO
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "repo", "number", "title", "state",
        "createdAt", "mergedAt", "closedAt",
        "additions", "deletions", "changedFiles",
        "comments", "reviews", "url"
    ])
    for pr in rows:
        repo = pr["repository"]["nameWithOwner"]
        writer.writerow([
            repo,
            pr["number"],
            pr["title"],
            pr["state"],
            pr["createdAt"],
            pr["mergedAt"] or "",
            pr["closedAt"] or "",
            pr["additions"],
            pr["deletions"],
            pr["changedFiles"],
            pr["comments"]["totalCount"],
            pr["reviews"]["totalCount"],
            pr["url"]
        ])
    return out.getvalue()

def main():
    ap = argparse.ArgumentParser(description="Summarize authored GitHub PRs across all repos.")
    ap.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    ap.add_argument("--author", help="GitHub login to summarize (default: token's user)")
    ap.add_argument("--state", choices=["OPEN", "CLOSED", "MERGED", "ALL"], default="ALL",
                    help="Filter PR state (default: ALL)")
    ap.add_argument("--since", help="ISO date (YYYY-MM-DD) lower bound on createdAt")
    ap.add_argument("--until", help="ISO date (YYYY-MM-DD) upper bound on createdAt")
    ap.add_argument("--org", help="Only include PRs where repository owner matches this org/user")
    ap.add_argument("--repos", nargs="+",
                    help="Only include these repos (nameWithOwner). Supports globs like ORG/*.")
    ap.add_argument("--exclude-repos", nargs="+",
                    help="Exclude these repos. Supports globs like ORG/exp-*.")
    ap.add_argument("--format", choices=["markdown", "csv"], default="markdown")
    ap.add_argument("--out", help="Write to file instead of stdout")
    ap.add_argument("--page-size", type=int, default=100, help="GraphQL page size (max 100)")
    ap.add_argument("--sleep", type=float, default=0.2, help="Sleep between requests (seconds)")
    args = ap.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: Provide a GitHub token via --token or GITHUB_TOKEN env var.", file=sys.stderr)
        sys.exit(1)

    # Determine author login if not provided
    author = args.author
    if not author:
        q = {"query": "query{ viewer { login } }"}
        r = http_post(GQL_ENDPOINT, token, q)
        try:
            author = r["data"]["viewer"]["login"]
        except Exception:
            print("ERROR: Could not determine viewer login; pass --author.", file=sys.stderr)
            sys.exit(1)

    states = None
    if args.state != "ALL":
        states = [args.state]

    since = dt.datetime.fromisoformat(args.since) if args.since else None
    until = dt.datetime.fromisoformat(args.until) if args.until else None
    if since and since.tzinfo is None:
        since = since.replace(tzinfo=dt.timezone.utc)
    if until and until.tzinfo is None:
        until = until.replace(tzinfo=dt.timezone.utc)

    after = None
    all_prs: List[Dict[str, Any]] = []
    total_reported = None

    while True:
        variables = {
            "login": author,
            "pageSize": min(max(args.page_size, 1), 100),
            "after": after,
            "states": states
        }
        payload = {"query": QUERY, "variables": variables}
        data = http_post(GQL_ENDPOINT, token, payload)

        if "errors" in data:
            msg = json.dumps(data["errors"], indent=2)
            print(f"GraphQL error(s):\n{msg}", file=sys.stderr)
            rl = data.get("data", {}).get("rateLimit", {})
            reset_at = rl.get("resetAt")
            if reset_at:
                reset_ts = parse_date(reset_at)
                if reset_ts:
                    wait_s = max(0, (reset_ts - dt.datetime.now(dt.timezone.utc)).total_seconds()) + 1
                    print(f"Waiting until rate limit reset ({wait_s:.0f}s)…", file=sys.stderr)
                    time.sleep(wait_s)
                    continue
            sys.exit(2)

        user = data.get("data", {}).get("user")
        if not user:
            print(f"ERROR: User '{author}' not found or token lacks scope.", file=sys.stderr)
            sys.exit(3)

        pr_conn = user["pullRequests"]
        if total_reported is None:
            total_reported = pr_conn["totalCount"]

        nodes = pr_conn["nodes"] or []
        all_prs.extend(nodes)

        page = pr_conn["pageInfo"]
        if page["hasNextPage"]:
            after = page["endCursor"]
            time.sleep(args.sleep)
        else:
            break

        rl = data.get("data", {}).get("rateLimit")
        if rl and rl.get("remaining", 1) <= 1:
            reset_ts = parse_date(rl.get("resetAt"))
            if reset_ts:
                wait_s = max(0, (reset_ts - dt.datetime.now(dt.timezone.utc)).total_seconds()) + 1
                time.sleep(wait_s)

    # Post-filtering by org, repo globs, and date range
    allow = args.repos or []
    deny = args.exclude_repos or []

    filtered: List[Dict[str, Any]] = []
    for pr in all_prs:
        repo_full = pr["repository"]["nameWithOwner"]

        if args.org:
            owner = repo_full.split("/")[0]
            if owner.lower() != args.org.lower():
                continue

        if not repo_allowed(repo_full, allow, deny):
            continue

        if not within_range(pr["createdAt"], since, until):
            continue

        filtered.append(pr)

    totals = {
        "total": len(filtered),
        "OPEN": sum(1 for p in filtered if p["state"] == "OPEN"),
        "CLOSED": sum(1 for p in filtered if p["state"] == "CLOSED"),
        "MERGED": sum(1 for p in filtered if p["state"] == "MERGED"),
        "additions": sum(p["additions"] for p in filtered),
        "deletions": sum(p["deletions"] for p in filtered),
        "changedFiles": sum(p["changedFiles"] for p in filtered),
    }

    if args.format == "csv":
        out_text = render_csv(filtered)
    else:
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for pr in filtered:
            groups[pr["repository"]["nameWithOwner"]].append(pr)
        out_text = render_markdown(groups, totals)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_text)
    else:
        sys.stdout.write(out_text)

if __name__ == "__main__":
    main()
