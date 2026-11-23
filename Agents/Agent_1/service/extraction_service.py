
import os
from collectors.gitlab_registry_collector import GitLabRegistryCollector
from collectors.dockerhub_collector import DockerHubCollector
import requests
from collectors.gitlab_collector import GitLabCollector
from collectors.trivy_collector import TrivyCollector
from normalizers.gitlab_normalizer import GitLabNormalizer
from normalizers.trivy_normalizer import TrivyNormalizer
from state.pipeline_state import PipelineState
from state.trivy_state import TrivyState
from docker_config import get_docker_config
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
        self.docker_config = get_docker_config()

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
    

#je vais savoir si je le laisse :

    

    def extract_trivy_docker_local(self):
        environment = os.getenv("TRIVY_ENVIRONMENT", "unknown")
        project_name = os.getenv("TRIVY_DOCKER_COMPOSE_PROJECT")
    
        events = []
    
        if not project_name:
            print("Docker Compose project is not configured.")
            return []
    
        # 1. Découvrir les conteneurs actifs
        try:
            containers = self.trivy_collector.discover_running_containers(project_name)
    
        except (RuntimeError, OSError) as error:
            print(f"Unable to discover running containers: {error}")
            return []
    
        # 2. Filtrer les conteneurs appartenant au projet ciblé
        project_containers = []
    
        for container in containers:
            labels = container.get("Labels") or {}
    
            if labels.get("com.docker.compose.project") == project_name:
                project_containers.append(container)
    
        print(
            f"Found {len(project_containers)} running containers "
            f"for project: {project_name}"
        )
    
        # 3. Regrouper les conteneurs par identifiant réel d'image
        images = {}
    
        for container in project_containers:
            image_name = container.get("Image")
            image_id = container.get("ImageID")
    
            if not image_name or not image_id:
                continue
    
            if image_id not in images:
                images[image_id] = {
                    "image_name": image_name,
                    "aliases": set()
                }
    
            images[image_id]["aliases"].add(image_name)
    
        # 4. Scanner chaque image unique
        for image_id, image_data in images.items():
            image_name = image_data["image_name"]
            aliases = image_data["aliases"]
    
            # Vérifier si cette image a déjà été analysée
            if all(
                self.trivy_state.is_image_processed(name, image_id)
                for name in aliases
            ):
                print(f"Skipping already processed image: {image_name}")
                continue
    
            try:
                # Scanner l'image
                report = self.trivy_collector.collect(
                    source="docker",
                    image_name=image_name,
                    image_source="docker"
                )
    
                # Normaliser le rapport
                image_events = self.trivy_normalizer.normalize(
                    report,
                    environment=environment
                )
    
                events.extend(image_events)
    
                # Enregistrer l'image après le succès du scan
                for name in aliases:
                    self.trivy_state.mark_image_as_processed(
                        name,
                        image_id
                    )
    
                print(f"Successfully scanned image: {image_name}")
    
            except (RuntimeError, ValueError, OSError) as error:
                print(
                    f"Unable to scan Docker image {image_name}: {error}"
                )
    
        return events
    def extract_trivy_docker(self):
        connection_type = self.docker_config["connection_type"]
    
        if connection_type == "local":
            return self.extract_trivy_docker_local()
    
        elif connection_type == "registry":
            return self.extract_trivy_registry()
        
        elif connection_type == "dockerhub":
            return self.extract_trivy_dockerhub()
    
        elif connection_type == "remote":
            print("Remote Docker scanning is not implemented yet.")
            return []
        
        
    def extract_trivy_registry(self):
        environment = os.getenv("TRIVY_ENVIRONMENT", "unknown")
        client_id = self.docker_config["client_id"]
        project_id = self.docker_config["registry_project_id"]
        events = []
    
        try:
            # 1. Découvrir les images du Registry GitLab
            registry_collector = GitLabRegistryCollector(
                gitlab_url=self.docker_config["gitlab_url"],
                token=self.docker_config["gitlab_token"],
                project_id=self.docker_config["registry_project_id"]
            )
    
            images = registry_collector.discover_images_with_details()
    
            print(f"Found {len(images)} images in GitLab Registry")
    
            # 2. Afficher les images découvertes
            # Scanner chaque image découverte
            for image_info in images:
                image = image_info["location"]
                digest = image_info["digest"]
            
                print(f"Image : {image}")
                print(f"Digest : {digest}")
                
                if self.trivy_state.is_registry_image_processed(
                    client_id, project_id, image, digest
                ):
                    print(f"Skipping already processed Registry image: {image}")
                    continue
            
                print(f"\nScanning Registry image: {image}")
            
                try:
                    # 1. Scanner l'image privée avec Trivy
                    report = self.trivy_collector.collect(
                        source="docker",
                        image_name=image,
                        image_source="remote",
                        registry_username=self.docker_config["registry_username"],
                        registry_password=self.docker_config["registry_password"]
                    )
            
                    # 2. Normaliser le rapport Trivy
                    image_events = self.trivy_normalizer.normalize(
                        report,
                        environment=environment
                    )
            
                    # 3. Ajouter les événements
                    events.extend(image_events)
            
                    print(
                        f"Successfully scanned image: {image} "
                        f"({len(image_events)} events)"
                    )
                    
                    self.trivy_state.mark_registry_image_as_processed(
                        client_id, project_id, image, digest
                    )
            
                except (RuntimeError, ValueError, OSError) as error:
                    print(f"Unable to scan Registry image {image}: {error}")
                
        except (requests.RequestException, RuntimeError, ValueError) as error:
            print(f"Unable to discover GitLab Registry images: {error}")
    
        return events
    
    def extract_trivy_dockerhub(self):

        environment = os.getenv("TRIVY_ENVIRONMENT", "unknown")
    
        client_id = self.docker_config["client_id"]
    
        namespace = self.docker_config["dockerhub_namespace"]
        repository = self.docker_config["dockerhub_repository"]
    
        # Identifier le repository pour le suivi des scans
        project_id = f"{namespace}/{repository}"
    
        events = []
    
        try:
            # 1. Découvrir les images Docker Hub
            dockerhub_collector = DockerHubCollector(
                namespace=namespace,
                repository=repository,
                username=self.docker_config["dockerhub_username"],
                token=self.docker_config["dockerhub_token"]
            )
    
            images = dockerhub_collector.discover_images_with_details()
    
            print(f"Found {len(images)} images in Docker Hub")
    
            # 2. Scanner chaque image découverte
            for image_info in images:
    
                image = image_info["location"]
                digest = image_info["digest"]
    
                print(f"\nImage : {image}")
                print(f"Digest : {digest}")
    
                # 3. Vérifier si l'image a déjà été traitée
                if self.trivy_state.is_registry_image_processed(
                    client_id, project_id, image, digest
                ):
                    print(f"Skipping already processed Docker Hub image: {image}")
                    continue
    
                print(f"Scanning Docker Hub image: {image}")
    
                try:
                    # 4. Scanner l'image avec Trivy
                    report = self.trivy_collector.collect(
                        source="docker",
                        image_name=image,
                        image_source="remote",
                        registry_username=self.docker_config["dockerhub_username"],
                        registry_password=self.docker_config["dockerhub_token"]
                    )
    
                    # 5. Normaliser le rapport
                    image_events = self.trivy_normalizer.normalize(
                        report,
                        environment=environment
                    )
    
                    events.extend(image_events)
    
                    # 6. Enregistrer le scan réussi
                    self.trivy_state.mark_registry_image_as_processed(
                        client_id, project_id, image, digest
                    )
    
                    print(
                        f"Successfully scanned Docker Hub image: {image} "
                        f"({len(image_events)} events)"
                    )
    
                except (RuntimeError, ValueError, OSError) as error:
                    print(f"Unable to scan Docker Hub image {image}: {error}")
    
        except (requests.RequestException, RuntimeError, ValueError) as error:
            print(f"Unable to discover Docker Hub images: {error}")
    
        return events