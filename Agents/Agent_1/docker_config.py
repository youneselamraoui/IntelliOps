import os
from dotenv import load_dotenv


def get_docker_config():
    # Charger les variables du fichier .env
    load_dotenv()

    connection_type = os.getenv(
        "DOCKER_CONNECTION_TYPE", "local"
    ).lower()

    # Vérifier le mode choisi
    if connection_type not in [
            "local","registry","remote","dockerhub" ]:
        raise ValueError(
            f"Unsupported Docker connection type: {connection_type}"
        )

    config = {
        "connection_type": connection_type,
        "client_id": os.getenv("CLIENT_ID", "default"),
    }

    # Mode Registry
    if connection_type == "registry":
        gitlab_url = os.getenv("GITLAB_URL")
        gitlab_token = os.getenv("GITLAB_TOKEN")
        project_id = os.getenv("GITLAB_REGISTRY_PROJECT_ID")
        registry_username = os.getenv("GITLAB_REGISTRY_USERNAME")
        if not gitlab_url:
            raise ValueError("GITLAB_URL is required for registry mode")
    
        if not gitlab_token:
            raise ValueError("GITLAB_TOKEN is required for registry mode")
    
        if not project_id:
            raise ValueError(
                "GITLAB_REGISTRY_PROJECT_ID is required for registry mode"
            )

        config["gitlab_url"] = gitlab_url.rstrip("/")
        config["gitlab_token"] = gitlab_token
        config["registry_project_id"] = project_id
        config["registry_username"] = registry_username
        config["registry_password"] = gitlab_token
        
    elif connection_type == "dockerhub":
        
        namespace = os.getenv("DOCKERHUB_NAMESPACE")
        repository = os.getenv("DOCKERHUB_REPOSITORY")
        username = os.getenv("DOCKERHUB_USERNAME")
        token = os.getenv("DOCKERHUB_TOKEN")
    
        if not namespace or not repository:
            raise ValueError(
                "DOCKERHUB_NAMESPACE and DOCKERHUB_REPOSITORY are required"   )
        config["dockerhub_namespace"] = namespace
        config["dockerhub_repository"] = repository
        config["dockerhub_username"] = username
        config["dockerhub_token"] = token

    # Mode Docker Engine distant
    elif connection_type == "remote":
        docker_host = os.getenv("DOCKER_HOST")
        tls_verify = os.getenv("DOCKER_TLS_VERIFY", "1")
        cert_path = os.getenv("DOCKER_CERT_PATH")

        if not docker_host:
            raise ValueError("DOCKER_HOST is required for remote mode")

        if tls_verify != "1":
            raise ValueError("Remote Docker connection must use TLS verification")

        if not cert_path or not os.path.isdir(cert_path):
            raise ValueError(
                "DOCKER_CERT_PATH must point to a valid certificate directory"
            )

        for filename in ["ca.pem", "cert.pem", "key.pem"]:
            if not os.path.isfile(os.path.join(cert_path, filename)):
                raise ValueError(
                    f"Missing Docker TLS certificate: {filename}"
                )

        config["docker_host"] = docker_host
        config["docker_tls_verify"] = tls_verify
        config["docker_cert_path"] = cert_path

    return config