import sys
import questionary
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
from .config import get_settings, load_tracked_repos
from .github import get_github_token, fetch_repos, select_repos, fetch_commits
from .llm import ollama_summarize_repo
from .report import generate_report, report_heading
import os

def prompt_date_range():
    import datetime
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    try:
        choice = questionary.select(
            "Select commit range:",
            choices=["Today", "Yesterday", "Last month", "Custom"]
        ).ask()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled by user.")
        sys.exit(0)
    if choice is None:
        print("Cancelled by user.")
        sys.exit(0)
    if choice == "Today":
        since = today.isoformat()
        until = (today + datetime.timedelta(days=1)).isoformat()
    elif choice == "Yesterday":
        since = yesterday.isoformat()
        until = today.isoformat()
    elif choice == "Last month":
        since = (today - datetime.timedelta(days=30)).isoformat()
        until = (today + datetime.timedelta(days=1)).isoformat()
    else:
        try:
            since = questionary.text("Start date (YYYY-MM-DD):").ask()
            if since is None:
                print("Cancelled by user.")
                sys.exit(0)
            until = questionary.text("End date (YYYY-MM-DD):").ask()
            if until is None:
                print("Cancelled by user.")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled by user.")
            sys.exit(0)
    return since, until

def main():
    settings = get_settings()
    language = settings.get("language", "English")
    include_commits = settings.get("include_commits", False)
    llm_model = settings.get("llm_model", "mistral")
    token = get_github_token()
    if not token:
        sys.exit(1)
    tracked = load_tracked_repos()
    if not tracked:
        repos = fetch_repos(token)
        tracked = select_repos(repos)
    since, until = prompt_date_range()
    commits_by_repo = {}
    for repo in tracked:
        commits_by_repo[repo] = fetch_commits(token, repo, since, until)
    report = generate_report(commits_by_repo, since, until, include_commits)
    if include_commits:
        print(report)
    heading = report_heading(tracked)
    print(f"\n{heading}")
    summaries = []
    for repo, commits in commits_by_repo.items():
        summary = ollama_summarize_repo(repo, commits, language, llm_model)
        summaries.append(f"REPO: {repo}\n{summary.strip()}\n")
        print(f"REPO: {repo}\n{summary.strip()}\n")
    os.makedirs("output", exist_ok=True)
    out_path = f"output/{since}.md"
    with open(out_path, "w") as f:
        if include_commits:
            f.write(report)
        f.write(f"\n{heading}\n")
        for s in summaries:
            f.write(s + "\n")
