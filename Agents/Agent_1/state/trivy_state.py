
import json
from pathlib import Path


class TrivyState:

    def __init__(self):

        self.file_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed_trivy.json"
        )

        self.projects = {}
        self.docker_images = {}
        self.registry_images = {}

        self.load_state()

    def load_state(self):

        if not self.file_path.exists():

            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            self.save_state()
            return

        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.projects = data.get("projects", {})
        self.docker_images = data.get("docker_images", {})
        self.registry_images = data.get("registry_images", {})

    def save_state(self):

        data = {
            "projects": self.projects,
            "docker_images": self.docker_images,
            "registry_images": self.registry_images
        }

        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def _get_project_state(self, project_id):

        project_id = str(project_id)

        if project_id not in self.projects:

            self.projects[project_id] = {
                "last_seen_job_id": 0,
                "pending_jobs": [],
                "processed_jobs": []
            }

        return self.projects[project_id]

    def is_processed(self, project_id, job_id):

        project_state = self._get_project_state(project_id)

        return str(job_id) in project_state["processed_jobs"]

    def add_pending(self, project_id, job_id):

        project_state = self._get_project_state(project_id)

        job_id = str(job_id)

        if job_id not in project_state["pending_jobs"]:
            project_state["pending_jobs"].append(job_id)
            self.save_state()

    def get_pending_jobs(self, project_id):

        project_state = self._get_project_state(project_id)

        return project_state["pending_jobs"]

    def remove_pending(self, project_id, job_id):

        project_state = self._get_project_state(project_id)

        job_id = str(job_id)

        project_state["pending_jobs"] = [
            pending_id
            for pending_id in project_state["pending_jobs"]
            if pending_id != job_id
        ]

        self.save_state()

    def update_watermark(self, project_id, job_id):

        project_state = self._get_project_state(project_id)

        project_state["last_seen_job_id"] = max(
            project_state["last_seen_job_id"],
            int(job_id)
        )

        self.save_state()

    def get_last_seen_job_id(self, project_id):

        project_state = self._get_project_state(project_id)

        return project_state["last_seen_job_id"]

    def mark_as_processed(self, project_id, job_id):

        project_state = self._get_project_state(project_id)

        job_id = str(job_id)

        if job_id in project_state["processed_jobs"]:
            return

        project_state["processed_jobs"].append(job_id)

        project_state["pending_jobs"] = [
            pending_id
            for pending_id in project_state["pending_jobs"]
            if pending_id != job_id
        ]

        self.save_state()
        
    
    def is_image_processed(self, image_name, image_id):
        image_state = self.docker_images.get(image_name)
    
        if not image_state:
            return False
    
        return (
            image_state.get("image_id") == image_id
            and image_state.get("processed") is True
        )
    
    
    def mark_image_as_processed(self, image_name, image_id):
        self.docker_images[image_name] = {
            "image_id": image_id,
            "processed": True
        }
    
        self.save_state()
    
    
    def get_image_id(self, image_name):
        image_state = self.docker_images.get(image_name)
    
        if not image_state:
            return None
    
        return image_state.get("image_id")
    
    def is_registry_image_processed(
        self, client_id, project_id, image_name, digest
    ):
        image_key = f"{client_id}:{project_id}:{image_name}"
    
        image_state = self.registry_images.get(image_key)
    
        return (
            image_state is not None
            and image_state.get("digest") == digest
            and image_state.get("processed") is True
        )


    def mark_registry_image_as_processed(
        self, client_id, project_id, image_name, digest
    ):
        image_key = f"{client_id}:{project_id}:{image_name}"
    
        self.registry_images[image_key] = {
            "digest": digest,
            "processed": True
        }
    
        self.save_state()