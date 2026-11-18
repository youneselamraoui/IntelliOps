
import json
from pathlib import Path


class PipelineState:

    def __init__(self):

        self.file_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed_pipelines.json"
        )

        self.processed_events = []

        self.load_state()

    
    def load_state(self):
    
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump({"processed_events": []}, file, indent=4)
    
        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    
        self.processed_events = data.get("processed_events", [])

    
    def is_processed(self, project_id, pipeline_id, status):
    
        for event in self.processed_events:
    
            if (
                event["project_id"] == str(project_id)
                and event["pipeline_id"] == pipeline_id
                and event["status"] == status
            ):
                return True
    
        return False
    
    def mark_as_processed(self, project_id, pipeline_id, status):
    
        if self.is_processed(project_id, pipeline_id, status):
            return
    
        event = {
            "project_id": str(project_id),
            "pipeline_id": pipeline_id,
            "status": status
        }
    
        self.processed_events.append(event)
    
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(
                {"processed_events": self.processed_events},
                file,
                indent=4
            )
