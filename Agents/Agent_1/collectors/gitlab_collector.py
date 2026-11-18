
import os
import requests
from dotenv import load_dotenv

from collectors.base_collector import BaseCollector


class GitLabCollector(BaseCollector):

    def __init__(self):
        load_dotenv()

        self.gitlab_url = os.getenv("GITLAB_URL")
        self.project_id = os.getenv("GITLAB_PROJECT_ID")
        self.token = os.getenv("GITLAB_TOKEN")

        if not all([self.gitlab_url, self.project_id, self.token]):
            raise ValueError("GitLab configuration is incomplete")

        self.api_url = (
            f"{self.gitlab_url}/api/v4/projects/"
            f"{self.project_id}"
        )

        self.headers = {
            "PRIVATE-TOKEN": self.token
        }

    def collect(self):

        # 1. Récupérer les pipelines
        response = requests.get(
            f"{self.api_url}/pipelines",
            headers=self.headers,
            params={
                "per_page": 100,
                "order_by": "id",
                "sort": "desc"
            },
            timeout=15
        )

        response.raise_for_status()

        pipelines = response.json()

        # 2. Enrichir chaque pipeline avec ses jobs
        for pipeline in pipelines:

            pipeline_id = pipeline["id"]

            jobs = self.get_pipeline_jobs(pipeline_id)

            pipeline["jobs"] = jobs

            # 3. Récupérer les logs des jobs échoués
            for job in jobs:

                if job["status"] == "failed":

                    trace = self.get_job_trace(job["id"])

                    # Garder les derniers caractères du log
                    job["trace"] = trace[-12000:] if trace else ""

        return pipelines

    def get_pipeline_jobs(self, pipeline_id):

        url = (
            f"{self.api_url}/pipelines/"
            f"{pipeline_id}/jobs"
        )

        response = requests.get(
            url,
            headers=self.headers,
            params={
                "per_page": 100,
                "include_retried": True
            },
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    def get_job_trace(self, job_id):

        url = (
            f"{self.api_url}/jobs/"
            f"{job_id}/trace"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=30
        )

        if response.status_code == 404:
            return ""

        response.raise_for_status()

        return response.text
