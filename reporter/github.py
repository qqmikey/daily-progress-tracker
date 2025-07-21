import os
import sys
import requests
import questionary
from dotenv import load_dotenv
from .config import load_tracked_repos, save_tracked_repos

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
    choices = [f"{r['owner']['login']}/{r['name']}" for r in repos]
    selected = questionary.checkbox(
        "Select repositories to track:", choices=choices
    ).ask()
    if not selected:
        sys.exit("No repositories selected.")
    save_tracked_repos(selected)
    return selected

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
