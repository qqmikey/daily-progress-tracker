import requests
import re

def deduplicate_numbered_list(text):
    lines = text.strip().split("\n")
    seen = set()
    result = []
    for line in lines:
        m = re.match(r"\s*\d+\.\s*(.*)", line)
        item = m.group(1).strip() if m else line.strip()
        if item and item not in seen:
            seen.add(item)
            result.append(line)
    return "\n".join(result)

def ollama_summarize_repo(repo, commits, language, model="mistral"):
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
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get("response", "")
            return deduplicate_numbered_list(summary)
    except Exception:
        pass
    return "[LLM summary unavailable]"
