import json
from pathlib import Path

class RuleEngine:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.reload_config()

    def reload_config(self):
        """Forces the engine to read the freshest rules from the JSON file."""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        self.rules = self.config.get('rules', {})
        self.destinations = self.config.get('destinations', {})

    def make_universal_path(self, raw_path: str) -> Path:
        """Automatically converts your LENOVO paths into universal paths for any PC."""
        # Swap out your specific username for the universal '~' (Home Directory) symbol
        if "C:/Users/LENOVO" in raw_path:
            raw_path = raw_path.replace("C:/Users/LENOVO", "~")
        
        # expanduser() translates '~' into whatever the current user's actual path is!
        return Path(raw_path).expanduser()

    def resolve_destination(self, file_path: str) -> Path:
        # HOT RELOAD: Always fetch the latest rules right before sorting!
        self.reload_config()

        path_obj = Path(file_path)
        ext = path_obj.suffix.lower()
        filename = path_obj.stem.lower()

        # PASS 1: Strict Mode. Check rules that have KEYWORDS first.
        for category, criteria in self.rules.items():
            valid_exts = criteria.get("extensions", [])
            keywords = criteria.get("keywords", [])

            if keywords:
                if valid_exts and ext not in valid_exts:
                    continue
                if any(keyword.lower() in filename for keyword in keywords):
                    raw_dest = self.destinations.get(category, self.destinations['Others'])
                    return self.make_universal_path(raw_dest)

        # PASS 2: General Mode. Check rules that only rely on EXTENSIONS.
        for category, criteria in self.rules.items():
            valid_exts = criteria.get("extensions", [])
            keywords = criteria.get("keywords", [])

            if not keywords:
                if valid_exts and ext in valid_exts:
                    raw_dest = self.destinations.get(category, self.destinations['Others'])
                    return self.make_universal_path(raw_dest)

        # Fallback if nothing matches
        raw_dest = self.destinations.get('Others')
        return self.make_universal_path(raw_dest)

    @property
    def watch_dir(self) -> Path:
        self.reload_config()
        raw_watch = self.config.get('watch_directory', '~/Downloads')
        return self.make_universal_path(raw_watch)

    @property
    def settle_time(self) -> int:
        self.reload_config()
        return self.config.get('settle_seconds', 3)