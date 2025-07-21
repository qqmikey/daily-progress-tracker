# daily-progress-tracker

## Overview
CLI tool for generating daily/periodic summaries of GitHub repository changes with LLM-powered analysis (Ollama + mistral model). Output is a concise, human-friendly Markdown report per day.

## Features
- GitHub authentication via [`Personal Access Token`](https://github.com/settings/tokens)
- Interactive repository selection
- Customizable date range (today, yesterday, last month, custom)
- LLM-based (Ollama, mistral) project change summaries per repo
- Configurable output (include/exclude raw commit messages)
- All settings stored in `config.json` in project root

## Requirements
- Python 3.10+
- [Ollama](https://ollama.com/) (local LLM runner)
- Mistral model for Ollama

## GitHub Personal Access Token
To use this tool, you need a **GitHub Personal Access Token**: [Create one here](https://github.com/settings/tokens)

- Go to **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
- Click **Generate new token**
- Set a name, expiration, and select at minimum these scopes:
  - `repo` (for private repositories)
  - `read:user`
- Copy and save your token securely. You will need to enter it on first run.

## Quickstart

### 1. Clone and install dependencies
```bash
git clone <repo-url>
cd daily-progress-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Ollama and Mistral model
- Download and install Ollama: https://ollama.com/download
- Start Ollama in the background:
```bash
ollama serve &
```
- Pull the mistral model:
```bash
ollama pull mistral
```

### 3. Run the tracker
```bash
./daily-progress-tracker
```
или
```bash
python reporter.py
```
- On first launch, select report language and authenticate with your GitHub Personal Access Token.
- Select repositories to track and date range.
- The tool will generate a Markdown report in `output/YYYY-MM-DD.md`.

### 4. Configuration
- All settings (language, tracked repositories, output options) are stored in `config.json` in the project root.
- To include raw commit messages in reports, set `"include_commits": true` in `config.json`.
- To change language, edit the `language` field in `config.json`.

## Example config.json
```json
{
  "language": "English",
  "tracked_repos": ["yourusername/repo1", "yourusername/repo2"],
  "include_commits": false
}
```

## Notes
- Ollama must be running and the mistral model must be available for LLM summaries to work.
- The tool is cross-platform (Linux/macOS).
- No comments are present in the codebase by design.

---

If you have questions or need to reset your configuration, just delete `config.json` and restart the CLI.
