import os
import json
import questionary

def get_config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")

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
    if "llm_model" not in cfg:
        model = questionary.select(
            "Select LLM model:", choices=["mistral", "llama3"]
        ).ask()
        cfg["llm_model"] = model
        changed = True
    if changed:
        save_config(cfg)
    return cfg

def load_tracked_repos():
    cfg = load_config()
    return cfg.get("tracked_repos", [])

def save_tracked_repos(repos):
    cfg = load_config()
    cfg["tracked_repos"] = repos
    save_config(cfg)
