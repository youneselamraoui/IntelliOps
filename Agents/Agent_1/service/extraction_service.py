
import os
import requests
from collectors.gitlab_collector import GitLabCollector
from collectors.trivy_collector import TrivyCollector
from normalizers.gitlab_normalizer import GitLabNormalizer
from normalizers.trivy_normalizer import TrivyNormalizer
from state.pipeline_state import PipelineState
from state.trivy_state import TrivyState
class ExtractionService:

    def __init__(self):
        # Composants GitLab
        self.collector = GitLabCollector()
        self.normalizer = GitLabNormalizer()
        self.state = PipelineState()

        # Composants Trivy
        self.trivy_collector = TrivyCollector()
        self.trivy_normalizer = TrivyNormalizer()
        self.trivy_state = TrivyState()

    def extract(self):
        # Liste commune pour toutes les sources
        events = []
        # Extraction GitLab
        gitlab_events = self.extract_gitlab()
        events.extend(gitlab_events)
        # Extraction Trivy
        trivy_events = self.extract_trivy()
        events.extend(trivy_events)
        
        file_events = self.extract_trivy_file()
        events.extend(file_events)
        
        docker_events = self.extract_trivy_docker()
        events.extend(docker_events)

        return events

    def extract_gitlab(self):

        pipelines = self.collector.collect()
        events = []
        for pipeline in pipelines:
            project_id = self.collector.project_id
            pipeline_id = pipeline["id"]
            pipeline_status = pipeline["status"]

            if self.state.is_processed(
                project_id,
                pipeline_id,
                pipeline_status
            ):
                continue
            normalized_events = self.normalizer.normalize(pipeline)
            events.extend(normalized_events)

            self.state.mark_as_processed(
                project_id,
                pipeline_id,
                pipeline_status
            )

        return events
    
    def extract_trivy(self):
        # 1. Récupérer la configuration depuis .env    
        project_id = os.getenv("TRIVY_GITLAB_PROJECT_ID")
    
        artifact_path = os.getenv(
            "TRIVY_GITLAB_ARTIFACT_PATH",
            "trivy-report.json"
        )
    
        environment = os.getenv("TRIVY_ENVIRONMENT", "unknown")
    
        if not project_id:
            raise ValueError("Trivy GitLab project ID is missing")
    
        # 2. Récupérer le watermark et les jobs en attente
    
        last_seen_job_id = self.trivy_state.get_last_seen_job_id(
            project_id
        )
        pending_job_ids = self.trivy_state.get_pending_jobs(
            project_id
        )
    
        # 3. Découvrir les nouveaux jobs Trivy    
        ready_jobs, still_pending, max_seen_job_id = (
            self.trivy_collector.discover_gitlab_jobs(
                project_id=project_id,
                last_seen_job_id=last_seen_job_id,
                pending_job_ids=pending_job_ids
            )
        )
        # 4. Identifier les jobs qui doivent encore être suivis

        ready_job_ids = {
            str(job["id"])
            for job in ready_jobs
        }
        
        active_job_ids = set(still_pending) | ready_job_ids
        
        # 5. Retirer les anciens jobs qui sont maintenant terminés
        # sans rapport exploitable
        
        for job_id in pending_job_ids:
        
            if str(job_id) not in active_job_ids:
        
                self.trivy_state.remove_pending(
                    project_id,
                    job_id
                )
    
        # 4. Sauvegarder tous les jobs qui doivent être suivis
    
        for job_id in still_pending:
            self.trivy_state.add_pending(project_id, job_id)
    
        for job in ready_jobs:
            self.trivy_state.add_pending(project_id, job["id"])
    
        # 5. Mettre à jour le watermark
        self.trivy_state.update_watermark(
            project_id,
            max_seen_job_id
        )
        # 6. Télécharger et normaliser les rapports disponibles    
        events = []
    
        for job in ready_jobs:
    
            job_id = str(job["id"])
            # Éviter de retraiter un job déjà traité    
            if self.trivy_state.is_processed(project_id, job_id):

                self.trivy_state.remove_pending(
                    project_id,
                    job_id
                )
            
                continue
            try:
                # Récupérer le rapport Trivy
    
                report = self.trivy_collector.collect_from_gitlab(
                    project_id=project_id,
                    job_id=job_id,
                    artifact_path=artifact_path
                )
    
                # Transformer le rapport en événements
                normalized_events = self.trivy_normalizer.normalize(
                    report,
                    environment=environment
                )
                events.extend(normalized_events)
                # Marquer le job comme traité uniquement après succès
    
                self.trivy_state.mark_as_processed(
                    project_id,
                    job_id
                )
            except requests.exceptions.RequestException as error:
                # Le job reste en attente pour une prochaine tentative
    
                print(
                    f"Unable to download Trivy report for job {job_id}: {error}"
                )
    
        return events
    
    
    
    def extract_trivy_file(self):
        file_path = os.getenv("TRIVY_REPORT_PATH")
        environment = os.getenv("TRIVY_ENVIRONMENT", "unknown")
    
        if not file_path:
            return []
    
        try:
            report = self.trivy_collector.collect(
                source="file",
                file_path=file_path
            )
    
            events = self.trivy_normalizer.normalize(
                report,
                environment=environment
            )
    
            return events
    
        except (FileNotFoundError, ValueError, OSError) as error:
            print(f"Unable to process local Trivy report: {error}")
            return []
    
    
    def extract_trivy_docker(self):
        environment = os.getenv("TRIVY_ENVIRONMENT", "unknown")
        events = []
    
        try:
            images = self.trivy_collector.discover_docker_images()
    
        except (RuntimeError, OSError) as error:
            print(f"Unable to discover Docker images: {error}")
            return []
    
        for image in images:
            repository = image.get("Repository")
            tag = image.get("Tag")
            image_id = image.get("ID")
    
            # Ignorer les images sans nom ou sans tag
            if not repository or not tag:
                continue
    
            if repository == "<none>" or tag == "<none>":
                continue
    
            image_name = f"{repository}:{tag}"
            
            if self.trivy_state.is_image_processed(image_name, image_id):
                print(f"Skipping already processed image: {image_name}")
                continue
    
            try:
                report = self.trivy_collector.collect(
                    source="docker",
                    image_name=image_name,
                    image_source="docker"
                )
    
                image_events = self.trivy_normalizer.normalize(
                    report,
                    environment=environment
                )
    
                events.extend(image_events)
                
                self.trivy_state.mark_image_as_processed(
                    image_name,
                    image_id
                )
                print(f"Successfully scanned image: {image_name}")
    
            except (RuntimeError, ValueError, OSError) as error:
                print(
                    f"Unable to scan Docker image {image_name}: {error}"
                )
                continue
    
        return events
    