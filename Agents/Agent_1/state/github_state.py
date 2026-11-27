import json
from pathlib import Path


class GitHubState:
    """Mémorise les workflow runs GitHub déjà transformés en événements."""

    def __init__(self):

        self.file_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed_github_runs.json"
        )

        self.processed_events = []

        self.load_state()

    def load_state(self):

        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.save_state()
            return

        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.processed_events = data.get("processed_events", [])

    def save_state(self):

        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(
                {"processed_events": self.processed_events},
                file,
                indent=4
            )

    def is_processed(self, repository, run_id, status):

        for event in self.processed_events:

            if (
                event["repository"] == str(repository)
                and event["run_id"] == run_id
                and event["status"] == status
            ):
                return True

        return False

    def mark_as_processed(self, repository, run_id, status):

        if self.is_processed(repository, run_id, status):
            return

        self.processed_events.append({
            "repository": str(repository),
            "run_id": run_id,
            "status": status
        })

        self.save_state()