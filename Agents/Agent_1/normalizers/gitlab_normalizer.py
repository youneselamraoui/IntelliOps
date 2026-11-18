
import re
from datetime import datetime

from models.event import Event


class GitLabNormalizer:

    def normalize(self, pipeline):

        failed_jobs = [
            job for job in pipeline.get("jobs", [])
            if job["status"] == "failed"
        ]

        events = []

        if failed_jobs:

            for job in failed_jobs:

                log = job.get("trace", "")

                # Extraire les informations de l'erreur
                error_info = self.extract_error_info(log)

                event = Event(
                    id=f"gitlab-{pipeline['id']}-job-{job['id']}",

                    timestamp=datetime.fromisoformat(
                        job["created_at"].replace("Z", "+00:00")
                    ),

                    source="GITLAB",
                    component=job["name"],
                    environment="unknown",
                    event_type="PIPELINE_FAILURE",
                    severity="HIGH",

                    message=self.build_message(
                        pipeline,
                        job,
                        error_info
                    ),

                    status="NEW",

                    details={
                        "pipeline_id": pipeline["id"],
                        "pipeline_status": pipeline["status"],
                        "branch": pipeline["ref"],
                        "commit_sha": pipeline.get("sha"),

                        "job_id": job["id"],
                        "job_name": job["name"],
                        "stage": job["stage"],
                        "job_status": job["status"],

                        "error_type": error_info["error_type"],
                        "error_message": error_info["error_message"],
                        "test_name": error_info["test_name"],
                        "file": error_info["file"],
                        "line": error_info["line"],

                        "error_log": log
                    }
                )

                events.append(event)

            return events

        # Aucun job échoué : événement général
        event = Event(
            id=f"gitlab-{pipeline['id']}-{pipeline['status']}",

            timestamp=datetime.fromisoformat(
                pipeline["created_at"].replace("Z", "+00:00")
            ),

            source="GITLAB",
            component="CI/CD",
            environment="unknown",
            event_type="PIPELINE",

            severity="INFO" if pipeline["status"] == "success" else "MEDIUM",

            message=(
                f"Pipeline {pipeline['id']} on branch "
                f"{pipeline['ref']} is {pipeline['status']}."
            ),

            status="NEW",

            details={
                "pipeline_id": pipeline["id"],
                "pipeline_status": pipeline["status"],
                "branch": pipeline["ref"],
                "commit_sha": pipeline.get("sha")
            }
        )

        return [event]

    
    def extract_error_info(self, log):
    
        error_info = {
            "error_type": "UnknownError",
            "error_message": "No error message extracted",
            "test_name": None,
            "file": None,
            "line": None
        }
    
        if not log:
            return error_info
    
        # 1. Extraire le nom d'un test en échec
        test_match = re.search(
            r"(?:FAIL|ERROR):\s+([^\s(]+)\s+\(",
            log
        )
    
        if test_match:
            error_info["test_name"] = test_match.group(1)
    
        # 2. Extraire le fichier et le numéro de ligne
        file_match = re.search(
            r'File "([^"]+)", line (\d+)',
            log
        )
    
        if file_match:
            error_info["file"] = file_match.group(1)
            error_info["line"] = int(file_match.group(2))
    
        # 3. Chercher une exception Python
        error_matches = re.findall(
            r"([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)",
            log
        )
    
        if error_matches:
            error_type, error_message = error_matches[-1]
    
            error_info["error_type"] = error_type
            error_info["error_message"] = error_message.strip()
    
            return error_info
    
        # 4. Si aucune exception n'est trouvée,
        # chercher un code de sortie non nul
        exit_match = re.search(
            r"Job failed: exit code (\d+)",
            log
        )
    
        if exit_match:
            exit_code = exit_match.group(1)
    
            error_info["error_type"] = "JobExitCode"
            error_info["error_message"] = (
                f"Job terminated with exit code {exit_code}. "
                "Underlying cause not identified."
            )
    
        return error_info
    

    def build_message(self, pipeline, job, error_info):

        message = (
            f"Pipeline {pipeline['id']} failed. "
            f"Job '{job['name']}' in stage '{job['stage']}' "
            f"failed on branch '{pipeline['ref']}'."
        )

        if error_info["error_type"] != "UnknownError":
            message += (
                f" Error: {error_info['error_type']}: "
                f"{error_info['error_message']}."
            )

        if error_info["file"]:
            message += (
                f" File: {error_info['file']}, "
                f"line: {error_info['line']}."
            )

        return message
