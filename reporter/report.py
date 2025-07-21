import datetime

def generate_report(commits_by_repo, since, until, include_commits):
    lines = []
    if include_commits:
        lines.append(f"# Commit List: {since} — {until}\n")
        for repo, commits in commits_by_repo.items():
            lines.append(f"## {repo}")
            if not commits:
                lines.append("- No commits")
                continue
            for c in commits:
                msg = c["commit"]["message"].split("\n")[0]
                lines.append(f"- {msg}")
            lines.append("")
    return "\n".join(lines)

def report_heading(tracked):
    today = datetime.date.today().isoformat()
    repo_count = len(tracked)
    return f"{today} ({repo_count} repositories)\n"
