import os

import requests
from dotenv import load_dotenv

from collectors.base_collector import BaseCollector


class GitHubCollector(BaseCollector):
    """Collecte les workflow runs GitHub Actions (équivalent de GitLabCollector)."""

    def __init__(self):
        load_dotenv()

        self.owner = os.getenv("GITHUB_OWNER")
        self.repo = os.getenv("GITHUB_REPO")
        self.token = os.getenv("GITHUB_TOKEN")
        self.api_base = os.getenv(
            "GITHUB_API_URL", "https://api.github.com"
        ).rstrip("/")

        if not all([self.owner, self.repo, self.token]):
            raise ValueError("GitHub configuration is incomplete")

        # Identifiant du dépôt, utilisé comme "project_id" dans l'état
        self.project_id = f"{self.owner}/{self.repo}"

        self.repo_url = f"{self.api_base}/repos/{self.owner}/{self.repo}"

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def collect(self):
        """Retourne les derniers runs (sans les jobs).

        Les jobs et les logs sont récupérés ensuite avec enrich_run(),
        uniquement pour les runs pas encore traités.
        """

        response = requests.get(
            f"{self.repo_url}/actions/runs",
            headers=self.headers,
            params={"per_page": 10},
            timeout=15
        )

        response.raise_for_status()

        return response.json().get("workflow_runs", [])

    def enrich_run(self, run):
        """Ajoute les jobs au run, et le log des jobs en échec."""

        jobs = self.get_run_jobs(run["id"])
        run["jobs"] = jobs

        for job in jobs:
            if job.get("conclusion") in ("failure", "timed_out"):
                trace = self.get_job_trace(job["id"])

                # Garder les derniers caractères du log
                job["trace"] = trace[-12000:] if trace else ""

        return run

    def get_run_jobs(self, run_id):

        response = requests.get(
            f"{self.repo_url}/actions/runs/{run_id}/jobs",
            headers=self.headers,
            params={"per_page": 100, "filter": "latest"},
            timeout=15
        )

        response.raise_for_status()

        return response.json().get("jobs", [])

    def get_job_trace(self, job_id):

        # GitHub répond par une redirection (302) vers le log en texte brut
        response = requests.get(
            f"{self.repo_url}/actions/jobs/{job_id}/logs",
            headers=self.headers,
            timeout=30
        )

        # 404 : job introuvable, 410 : logs expirés
        if response.status_code in (404, 410):
            return ""

        response.raise_for_status()

        return response.text