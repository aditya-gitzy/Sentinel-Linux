import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .rules import RuleEngine
from .mover import is_file_ready, safe_move

class SortHandler(FileSystemEventHandler):
    def __init__(self, rule_engine: RuleEngine):
        self.rules = rule_engine

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.process_file(event.dest_path)

    def process_file(self, file_path: str):
        # Stop infinite loops if destination is inside the watch folder
        if "Sorted" in file_path or "Others" in file_path or "College" in file_path:
            return

        if is_file_ready(file_path, self.rules.settle_time):
            dest = self.rules.resolve_destination(file_path)
            from pathlib import Path
            safe_move(Path(file_path), dest)

class SentinelWatcher:
    def __init__(self, config_path: str):
        self.rules = RuleEngine(config_path)
        self.observer = Observer()

    def start(self):
        handler = SortHandler(self.rules)
        self.observer.schedule(handler, str(self.rules.watch_dir), recursive=False)
        self.observer.start()
        logging.info(f"Sentinel started watching: {self.rules.watch_dir}")
        try:
            while self.observer.is_alive():
                self.observer.join(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()