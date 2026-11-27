import re
from datetime import datetime

from models.event import Event


FAILED_CONCLUSIONS = ("failure", "timed_out")

# Préfixe d'horodatage ajouté par GitHub à chaque ligne de log
TIMESTAMP_PREFIX = re.compile(
    r"^\ufeff?\d{4}-\d{2}-\d{2}T[\d:.]+Z ", re.MULTILINE
)
ANSI_CODES = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def parse_date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class GitHubNormalizer:

    def normalize(self, run):

        failed_jobs = [
            job for job in run.get("jobs", [])
            if job.get("conclusion") in FAILED_CONCLUSIONS
        ]

        # Run sans job en échec exploitable : événement général
        if not failed_jobs:
            return [self.build_run_event(run)]

        return [self.build_job_event(run, job) for job in failed_jobs]

    def build_run_event(self, run):

        conclusion = run.get("conclusion") or run.get("status")

        return Event(
            id=f"github-{run['id']}-{conclusion}",
            timestamp=parse_date(run["created_at"]),
            source="GITHUB",
            component="CI/CD",
            environment="unknown",
            event_type="PIPELINE",
            severity="INFO" if conclusion == "success" else "MEDIUM",
            message=(
                f"Workflow run {run['id']} ('{run.get('name')}') on branch "
                f"{run.get('head_branch')} is {conclusion}."
            ),
            status="NEW",
            details={
                "run_id": run["id"],
                "run_number": run.get("run_number"),
                "run_attempt": run.get("run_attempt"),
                "workflow_name": run.get("name"),
                "trigger_event": run.get("event"),
                "pipeline_status": conclusion,
                "branch": run.get("head_branch"),
                "commit_sha": run.get("head_sha"),
                "url": run.get("html_url")
            }
        )

    def build_job_event(self, run, job):

        log = self.clean_log(job.get("trace", ""))
        error_info = self.extract_error_info(log)
        failed_step = self.get_failed_step(job)

        return Event(
            id=f"github-{run['id']}-job-{job['id']}",
            timestamp=parse_date(job.get("created_at") or run["created_at"]),
            source="GITHUB",
            component=job["name"],
            environment="unknown",
            event_type="PIPELINE_FAILURE",
            severity="HIGH",
            message=self.build_message(run, job, failed_step, error_info),
            status="NEW",
            details={
                "run_id": run["id"],
                "run_number": run.get("run_number"),
                "run_attempt": run.get("run_attempt"),
                "workflow_name": run.get("name"),
                "trigger_event": run.get("event"),
                "pipeline_status": run.get("conclusion"),
                "branch": run.get("head_branch"),
                "commit_sha": run.get("head_sha"),
                "url": run.get("html_url"),

                "job_id": job["id"],
                "job_name": job["name"],
                "job_status": job.get("conclusion"),
                "failed_step": failed_step,

                "error_type": error_info["error_type"],
                "error_message": error_info["error_message"],
                "test_name": error_info["test_name"],
                "file": error_info["file"],
                "line": error_info["line"],

                "error_log": log
            }
        )

    def get_failed_step(self, job):

        for step in job.get("steps", []):
            if step.get("conclusion") in FAILED_CONCLUSIONS:
                return step.get("name")

        return None

    def clean_log(self, log):

        if not log:
            return ""

        log = ANSI_CODES.sub("", log)
        return TIMESTAMP_PREFIX.sub("", log)

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

        # 1. Nom d'un test en échec (unittest / pytest)
        test_match = re.search(
            r"(?:FAIL|ERROR|FAILED):?\s+([^\s(]+)\s*\(", log
        )
        if test_match:
            error_info["test_name"] = test_match.group(1)
        else:
            pytest_match = re.search(r"FAILED\s+(\S+::\S+)", log)
            if pytest_match:
                error_info["test_name"] = pytest_match.group(1)

        # 2. Fichier et ligne (traceback Python)
        file_match = re.search(r'File "([^"]+)", line (\d+)', log)
        if file_match:
            error_info["file"] = file_match.group(1)
            error_info["line"] = int(file_match.group(2))

        # 3. Exception Python
        error_matches = re.findall(
            r"([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)", log
        )
        if error_matches:
            error_type, error_message = error_matches[-1]
            error_info["error_type"] = error_type
            error_info["error_message"] = error_message.strip()
            return error_info

        # 4. Annotation d'erreur GitHub Actions (##[error]...)
        annotations = re.findall(r"##\[error\](.+)", log)
        if annotations:
            message = annotations[-1].strip()
            error_info["error_message"] = message

            exit_match = re.search(r"exit code (\d+)", message)
            error_info["error_type"] = (
                "JobExitCode" if exit_match else "WorkflowError"
            )
            if exit_match:
                error_info["error_message"] = (
                    f"Job terminated with exit code {exit_match.group(1)}. "
                    "Underlying cause not identified."
                )

        return error_info

    def build_message(self, run, job, failed_step, error_info):

        message = (
            f"Workflow run {run['id']} failed. "
            f"Job '{job['name']}' failed on branch "
            f"'{run.get('head_branch')}'."
        )

        if failed_step:
            message += f" Failed step: '{failed_step}'."

        if error_info["error_type"] != "UnknownError":
            message += (
                f" Error: {error_info['error_type']}: "
                f"{error_info['error_message'].rstrip('.')}."
            )

        if error_info["file"]:
            message += (
                f" File: {error_info['file']}, "
                f"line: {error_info['line']}."
            )

        return message