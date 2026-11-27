import os , io
import zipfile
import json
import requests
import subprocess
from dotenv import load_dotenv
from collectors.base_collector import BaseCollector

class TrivyCollector(BaseCollector) :
    def __init__(self):
        load_dotenv()

    def collect(self , source , **kwargs) :
        if source == "file" :
            return self.collect_from_file(**kwargs)

        elif source == "docker":
            return self.collect_from_docker(**kwargs)

        elif source == "gitlab":
            return self.collect_from_gitlab(**kwargs)

        elif source == "github":
            return self.collect_from_github(**kwargs)

        elif source == "jenkins":
            return self.collect_from_jenkins(**kwargs)

        elif source == "kubernetes":
            return self.collect_from_kubernetes(**kwargs)

        elif source == "harbor":
            return self.collect_from_harbor(**kwargs)

        else:
            raise ValueError(
                f"Unsupported Trivy source: {source}"
            )
            
        
    def collect_from_file(self, file_path):

        # Vérifier que le fichier existe
        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                f"Trivy report not found: {file_path}"
            )

        # Lire et convertir le JSON en dictionnaire Python
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                report = json.load(file)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid Trivy JSON report: {error}"
            )

        # Vérifier la structure générale du rapport
        if not isinstance(report, dict):
            raise ValueError(
                "Invalid Trivy report: expected a JSON object"
            )

        return report
    
    
    
    
    def collect_from_docker(self,image_name,
                            image_source="auto",
                            registry_username=None,
                            registry_password=None ):
        if image_source not in ("auto", "docker", "remote"):
            raise ValueError(
                "image_source must be 'auto', 'docker' or 'remote'"
            )
    
        # Construction de la commande Docker
        command = ["docker", "run", "--rm"]
        # Transmettre les identifiants au conteneur Trivy
        scan_env = os.environ.copy()
        
        if registry_username and registry_password:
            scan_env["TRIVY_USERNAME"] = registry_username
            scan_env["TRIVY_PASSWORD"] = registry_password
        
            command.extend([
                "-e", "TRIVY_USERNAME",
                "-e", "TRIVY_PASSWORD"
            ])
    
        # Accès aux images Docker locales
        if image_source == "docker":
            command.extend([
                "-v",
                "/var/run/docker.sock:/var/run/docker.sock"
            ])
    
        # Cache persistant de Trivy
        command.extend([
            "-v",
            "trivy-cache:/root/.cache/"
        ])
    
        # Image contenant Trivy et ses options
        command.extend([
            "aquasec/trivy:latest",
            "--timeout", "10m",
            "image",
            "--scanners", "vuln",
            "--format", "json",
        ])
    
        if image_source == "docker":
            command.extend(["--image-src", "docker"])
    
        elif image_source == "remote":
            command.extend(["--image-src", "remote"])
    
        command.append(image_name)
    
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=720,
                env=scan_env
            )
    
        except FileNotFoundError:
            raise RuntimeError(
                "Docker is not installed or is not available in PATH"
            )
    
        except subprocess.TimeoutExpired:
            raise RuntimeError("Trivy scan timed out")
    
        if result.returncode != 0:
            raise RuntimeError(
                f"Trivy Docker scan failed: {result.stderr}"
            )
    
        try:
            report = json.loads(result.stdout)
    
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Trivy returned invalid JSON: {error}"
            )
    
        if not isinstance(report, dict):
            raise ValueError("Invalid Trivy report format")
    
        return report

    
    
    # def discover_docker_images(self):
    #     command = [
    #         "docker",
    #         "images",
    #         "--format",
    #         "{{json .}}"
    #     ]
    
    #     try:
    #         result = subprocess.run(
    #             command,
    #             capture_output=True,
    #             text=True,
    #             timeout=60,
    #             check=True
    #         )
    
    #     except FileNotFoundError:
    #         raise RuntimeError(
    #             "Docker is not installed or not available in PATH"
    #         )
    
    #     except subprocess.CalledProcessError as error:
    #         raise RuntimeError(
    #             f"Unable to discover Docker images: {error.stderr}"
    #         )
    
    #     except subprocess.TimeoutExpired:
    #         raise RuntimeError(
    #             "Docker image discovery timed out"
    #         )
    
    #     images = []
    
    #     for line in result.stdout.splitlines():
    #         if not line.strip():
    #             continue
    
    #         try:
    #             image = json.loads(line)
    #             images.append(image)
    
    #         except json.JSONDecodeError:
    #             continue
    
    #     return images  
    
    
    
    def discover_running_containers(self, project_name):
        command = [
            "docker",
            "ps",
            "--filter",
            f"label=com.docker.compose.project={project_name}",
            "--format",
            "{{json .}}"
        ]
    
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=True
            )
    
        except FileNotFoundError:
            raise RuntimeError(
                "Docker is not installed or not available in PATH"
            )
    
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                f"Unable to discover running containers: {error.stderr}"
            )
    
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "Docker container discovery timed out"
            )
    
        containers = []
    
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
    
            try:
                container = json.loads(line)
    
                inspect_result = subprocess.run(
                    ["docker","inspect",container["ID"]],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                    check=True
                )
                inspect_data = json.loads(inspect_result.stdout)[0]
                
                container["ImageID"] = inspect_data.get("Image")
                container["Labels"] = (
                    inspect_data.get("Config", {}).get("Labels") or {}
                )
    
                if container.get("Image") and container["ImageID"]:
                    containers.append(container)
    
            except (json.JSONDecodeError, KeyError ,IndexError):
                continue
    
            except subprocess.CalledProcessError as error:
                print(
                    f"Unable to inspect container: {error.stderr}"
                )
                continue
            except subprocess.TimeoutExpired:
                print(f"Timeout while inspecting container: {container.get('ID', 'unknown')}")
                continue
    
        return containers

  
        
    def collect_from_gitlab(
        self,
        project_id,
        job_id,
        artifact_path="trivy-report.json"
        ):       
        # 1. Récupérer la configuration GitLab
        gitlab_url = os.getenv("GITLAB_URL")
        token = os.getenv("GITLAB_TOKEN")
    
        if not gitlab_url or not token:
            raise ValueError("GitLab configuration is incomplete")
    
        # 2. Construire l'URL de téléchargement de l'artifact
        url = (
            f"{gitlab_url.rstrip('/')}/api/v4/projects/{project_id}"
            f"/jobs/{job_id}/artifacts/{artifact_path}"
        )
    
        # 3. Envoyer la requête à l'API GitLab
        response = requests.get(
            url,
            headers={"PRIVATE-TOKEN": token},
            timeout=60
        )
    
        # 4. Vérifier si GitLab a répondu avec succès
        response.raise_for_status()
    
        # 5. Convertir le contenu JSON en dictionnaire Python
        try:
            report = response.json()
        except ValueError as error:
            raise ValueError(
                "The GitLab artifact is not a valid JSON report"
            ) from error
    
        # 6. Vérifier la structure générale
        if not isinstance(report, dict):
            raise ValueError("Invalid Trivy report structure")
    
        return report

    
    
    def collect_from_github(
        self, owner, repo, run_id,
        artifact_name="trivy-report"
    ):

        token = os.getenv("GITHUB_TOKEN")

        if not token:
            raise ValueError("GITHUB_TOKEN is missing")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        artifacts_url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/actions/runs/{run_id}/artifacts"
        )

        response = requests.get(
            artifacts_url,
            headers=headers,
            timeout=60
        )

        response.raise_for_status()

        artifacts = response.json().get("artifacts", [])

        artifact = next(
            (
                item for item in artifacts
                if item["name"] == artifact_name
            ),
            None
        )

        if artifact is None:
            raise FileNotFoundError(
                f"Artifact '{artifact_name}' not found"
            )

        download = requests.get(
            artifact["archive_download_url"],
            headers=headers,
            timeout=120
        )

        download.raise_for_status()

        try:
            with zipfile.ZipFile(
                io.BytesIO(download.content)
            ) as archive:

                json_files = [
                    name for name in archive.namelist()
                    if name.endswith(".json")
                ]

                if not json_files:
                    raise FileNotFoundError(
                        "No JSON report found in GitHub artifact"
                    )

                with archive.open(json_files[0]) as file:
                    report = json.load(file)

        except zipfile.BadZipFile as error:
            raise ValueError(
                "GitHub artifact is not a valid ZIP archive"
            ) from error

        if not isinstance(report, dict):
            raise ValueError("Invalid Trivy report structure")

        return report


    def discover_github_runs(
        self,
        owner,
        repo,
        last_seen_run_id=0,
        pending_run_ids=None,
        workflow=None,
        max_pages=5
    ):
        """Équivalent de discover_gitlab_jobs pour GitHub Actions.

        workflow : nom du fichier du workflow Trivy (ex. "trivy.yml").
        Retourne (runs prêts, ids encore en attente, plus grand id vu).
        """

        token = os.getenv("GITHUB_TOKEN")

        if not token:
            raise ValueError("GITHUB_TOKEN is missing")

        api_base = os.getenv(
            "GITHUB_API_URL", "https://api.github.com"
        ).rstrip("/")

        repo_url = f"{api_base}/repos/{owner}/{repo}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        ready_runs = []
        still_pending = []
        max_seen_run_id = int(last_seen_run_id)

        # 1. Vérifier les runs précédemment en attente
        for run_id in pending_run_ids or []:

            response = requests.get(
                f"{repo_url}/actions/runs/{run_id}",
                headers=headers,
                timeout=60
            )

            response.raise_for_status()

            run = response.json()

            if run.get("status") != "completed":
                still_pending.append(str(run_id))

            elif run.get("conclusion") == "success":
                ready_runs.append(run)

            # Les runs failure, cancelled, skipped... ne sont pas conservés.

        # 2. Découvrir les nouveaux runs (du plus récent au plus ancien)
        if workflow:
            url = f"{repo_url}/actions/workflows/{workflow}/runs"
        else:
            url = f"{repo_url}/actions/runs"

        stop_search = False

        for page in range(1, max_pages + 1):

            response = requests.get(
                url,
                headers=headers,
                params={"per_page": 100, "page": page},
                timeout=60
            )

            response.raise_for_status()

            runs = response.json().get("workflow_runs", [])

            if not runs:
                break

            for run in runs:

                run_id = int(run["id"])

                # Les runs plus anciens ont déjà été observés
                if run_id <= int(last_seen_run_id):
                    stop_search = True
                    break

                max_seen_run_id = max(max_seen_run_id, run_id)

                if run.get("status") != "completed":
                    still_pending.append(str(run_id))

                elif run.get("conclusion") == "success":
                    ready_runs.append(run)

            if stop_search or len(runs) < 100:
                break

        # 3. Éviter les doublons
        unique_runs = {str(run["id"]): run for run in ready_runs}
        unique_pending = list(set(still_pending))

        return (
            list(unique_runs.values()),
            unique_pending,
            max_seen_run_id
        )
    
    def discover_gitlab_jobs(
        self,
        project_id,
        last_seen_job_id=0,
        pending_job_ids=None,
        job_name="trivy_scan"
    ):
    
        gitlab_url = os.getenv("GITLAB_URL")
        token = os.getenv("GITLAB_TOKEN")
    
        if not gitlab_url or not token:
            raise ValueError("GitLab configuration is incomplete")
    
        base_url = (
            f"{gitlab_url.rstrip('/')}/api/v4/projects/{project_id}/jobs"
        )
    
        headers = {"PRIVATE-TOKEN": token}
    
        ready_jobs = []
        still_pending = []
        max_seen_job_id = int(last_seen_job_id)
    
        # Statuts qui indiquent que le job n'est pas encore terminé
        pending_statuses = {
            "created",
            "waiting_for_resource",
            "preparing",
            "pending",
            "running",
            "scheduled",
            "manual",
            "waiting_for_callback",
            "canceling"
        }
    
        # 1. Vérifier les jobs précédemment en attente
    
        for job_id in pending_job_ids or []:
    
            job_url = f"{base_url}/{job_id}"
    
            response = requests.get(
                job_url,
                headers=headers,
                timeout=60
            )
    
            response.raise_for_status()
    
            job = response.json()
    
            status = job.get("status")
    
            if status == "success":
    
                if job.get("artifacts_file"):
                    ready_jobs.append(job)
                else:
                    still_pending.append(str(job_id))
    
            elif status in pending_statuses:
                still_pending.append(str(job_id))
    
            # Les jobs failed, canceled et skipped ne sont pas conservés.
    
        # 2. Découvrir les nouveaux jobs avec la pagination keyset
    
        url = base_url
    
        params = {
            "per_page": 100,
            "pagination": "keyset",
            "order_by": "id",
            "sort": "desc"
        }
    
        stop_search = False
    
        while url:
    
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=60
            )
    
            response.raise_for_status()
    
            jobs = response.json()
    
            if not isinstance(jobs, list):
                raise ValueError("Invalid GitLab jobs response")
    
            if not jobs:
                break
    
            for job in jobs:
    
                job_id = int(job["id"])
    
                # Les jobs plus anciens ont déjà été observés
                if job_id <= int(last_seen_job_id):
                    stop_search = True
                    break
    
                max_seen_job_id = max(max_seen_job_id, job_id)
    
                # Garder uniquement les jobs Trivy
                if job.get("name") != job_name:
                    continue
    
                status = job.get("status")
    
                if status == "success":
    
                    if job.get("artifacts_file"):
                        ready_jobs.append(job)
                    else:
                        still_pending.append(str(job_id))
    
                elif status in pending_statuses:
                    still_pending.append(str(job_id))
    
                # Les jobs failed, canceled et skipped sont ignorés.
    
            if stop_search:
                break
    
            # Récupérer le lien de la page suivante fourni par GitLab
            next_link = response.links.get("next")
            url = next_link["url"] if next_link else None
    
            # Les paramètres sont déjà présents dans le lien suivant
            params = None
    
        # 3. Éviter les doublons dans les jobs prêts
    
        unique_jobs = {
            str(job["id"]): job
            for job in ready_jobs
        }
    
        # 4. Éviter les doublons dans les jobs en attente
    
        unique_pending = list(set(still_pending))
    
        return (
            list(unique_jobs.values()),
            unique_pending,
            max_seen_job_id
        )
    