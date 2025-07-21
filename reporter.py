import os
import sys
import json
import datetime
import requests
import questionary
from dotenv import load_dotenv

def get_config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg):
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(cfg, f, indent=2)


def get_github_token():
    token = None
    if os.path.exists(".env"):
        load_dotenv()
        token = os.getenv("GITHUB_TOKEN")
    if not token:
        token = questionary.text("Enter your GitHub Personal Access Token:").ask()
        save_choice = questionary.select(
            "Where to save the token?",
            choices=[".env (project-local)", "~/.gitreporter/config.json (user-global)"]
        ).ask()
        if save_choice.startswith(".env"):
            with open(".env", "w") as f:
                f.write(f"GITHUB_TOKEN={token}\n")
        else:
            config_path = os.path.expanduser("~/.gitreporter/config.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                json.dump({"github_token": token}, f)
    return token


def get_settings():
    cfg = load_config()
    changed = False
    if "language" not in cfg:
        lang = questionary.select(
            "Select report language:", choices=["English", "Русский"]
        ).ask()
        cfg["language"] = lang
        changed = True
    if "include_commits" not in cfg:
        cfg["include_commits"] = False
        changed = True
    if changed:
        save_config(cfg)
    return cfg


def fetch_repos(token):
    url = "https://api.github.com/user/repos?per_page=100&type=all&sort=full_name"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    repos = []
    page = 1
    while True:
        resp = requests.get(url + f"&page={page}", headers=headers)
        if resp.status_code != 200:
            sys.exit("GitHub API error: " + str(resp.status_code))
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def select_repos(repos):
    cfg = load_config()
    choices = [f"{r['owner']['login']}/{r['name']}" for r in repos]
    selected = questionary.checkbox(
        "Select repositories to track:", choices=choices
    ).ask()
    if not selected:
        sys.exit("No repositories selected.")
    cfg["tracked_repos"] = selected
    save_config(cfg)
    return selected


def load_tracked_repos():
    cfg = load_config()
    return cfg.get("tracked_repos", [])


def prompt_date_range():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    first_of_month = today.replace(day=1)
    choice = questionary.select(
        "Select commit range:",
        choices=["Today", "Yesterday", "Last month", "Custom"]
    ).ask()
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
        since = questionary.text("Start date (YYYY-MM-DD):").ask()
        until = questionary.text("End date (YYYY-MM-DD):").ask()
    return since, until


def fetch_commits(token, repo, since, until):
    owner, name = repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{name}/commits"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    params = {"since": since + "T00:00:00Z", "until": until + "T00:00:00Z", "per_page": 100}
    commits = []
    page = 1
    while True:
        p = params.copy()
        p["page"] = page
        resp = requests.get(url, headers=headers, params=p)
        if resp.status_code == 409:
            break
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        commits.extend(data)
        page += 1
    return commits


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


def ollama_summarize_repo(repo, commits, language):
    if not commits:
        return "No significant changes."
    text = "\n".join([
        c["commit"]["message"].splitlines()[0]
        for c in commits
    ])
    prompt = (
        f"For repository '{repo}', analyze the following project changes. "
        f"Output ONLY a numbered list of meaningful, user-facing or business-relevant changes. "
        f"EXCLUDE any points about Dockerfile, docker, yaml, yml, config, workflow, CI/CD, documentation, readme, version bumps, or other technical/configuration-only changes. "
        f"Each item must be a clear, concise sentence describing what was actually improved, fixed, or added for the end user or business logic. "
        f"No intro, no conclusion, no commit hashes, no word 'commit'. Output in {language}.\n{text}"
    )
    url = "http://localhost:11434/api/generate"
    payload = {"model": "mistral", "prompt": prompt, "stream": False}
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", "")
    except Exception:
        pass
    return "[LLM summary unavailable]"


def main():
    settings = get_settings()
    language = settings.get("language", "English")
    include_commits = settings.get("include_commits", False)
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
    today = datetime.date.today().isoformat()
    repo_count = len(tracked)
    heading = f"{today} ({repo_count} repositories)\n"
    print(f"\n{heading}")
    summaries = []
    for repo, commits in commits_by_repo.items():
        summary = ollama_summarize_repo(repo, commits, language)
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


if __name__ == "__main__":
    main()
