import requests
from urllib.parse import quote

class DockerHubCollector:

    def __init__(self, namespace, repository, username=None, token=None):
        self.namespace = namespace
        self.repository = repository
        self.username = username
        self.token = token
        self.session = requests.Session()
        
    def discover_tags(self):
        url = (
            f"https://hub.docker.com/v2/namespaces/"
            f"{self.namespace}/repositories/"
            f"{self.repository}/tags"
        )
    
        tags = []
        params = {
            "page": 1,
            "page_size": 100
        }
    
        while url:
            response = self.session.get(
                url,
                params=params,
                timeout=30
            )
    
            response.raise_for_status()
    
            data = response.json()
    
            if not isinstance(data, dict):
                raise ValueError(
                    "Unexpected Docker Hub tags API response"
                )
    
            results = data.get("results", [])
    
            if not isinstance(results, list):
                raise ValueError(
                    "Unexpected Docker Hub tags results"
                )
    
            tags.extend(results)
    
            # Récupérer la page suivante
            url = data.get("next")
    
            # Les paramètres sont déjà présents dans l'URL suivante
            params = None
    
        return tags
    
    
    def discover_tag_details(self, tag_name):

        encoded_tag = quote(str(tag_name), safe="")
    
        url = (
            f"https://hub.docker.com/v2/namespaces/"
            f"{self.namespace}/repositories/"
            f"{self.repository}/tags/{encoded_tag}"
        )
    
        response = self.session.get(
            url,
            timeout=30
        )
    
        response.raise_for_status()
    
        data = response.json()
    
        if not isinstance(data, dict):
            raise ValueError(
                "Unexpected Docker Hub tag details response"
            )
    
        return data
    
    def get_registry_token(self):

        url = "https://auth.docker.io/token"
    
        params = {
            "service": "registry.docker.io",
            "scope": (
                f"repository:{self.namespace}/"
                f"{self.repository}:pull"
            )
        }
    
        auth = None
    
        if self.username and self.token:
            auth = (self.username, self.token)
    
        response = requests.get(
            url,
            params=params,
            auth=auth,
            timeout=30
        )
    
        response.raise_for_status()
    
        data = response.json()
    
        registry_token = (
            data.get("token")
            or data.get("access_token")
        )
    
        if not registry_token:
            raise ValueError(
                "Unable to obtain Docker Hub Registry token"
            )
    
        return registry_token
    
    def discover_digest(self, tag_name):

        registry_token = self.get_registry_token()
    
        repository_path = (
            f"{self.namespace}/{self.repository}"
        )
    
        encoded_tag = quote(str(tag_name), safe="")
    
        url = (
            f"https://registry-1.docker.io/v2/"
            f"{repository_path}/manifests/{encoded_tag}"
        )
    
        headers = {
            "Authorization": f"Bearer {registry_token}",
            "Accept": ", ".join([
                "application/vnd.oci.image.index.v1+json",
                "application/vnd.oci.image.manifest.v1+json",
                "application/vnd.docker.distribution.manifest.list.v2+json",
                "application/vnd.docker.distribution.manifest.v2+json"
            ])
        }
    
        response = requests.head(
            url,
            headers=headers,
            timeout=30
        )
    
        response.raise_for_status()
    
        digest = response.headers.get(
            "Docker-Content-Digest"
        )
    
        if not digest:
            raise ValueError(
                f"Digest not found for tag: {tag_name}"
            )
    
        return digest
    
    def discover_images_with_details(self):

        tags = self.discover_tags()
    
        images = []
    
        for tag in tags:
    
            tag_name = tag.get("name")
    
            if not tag_name:
                continue
    
            # Récupérer les détails du tag
            details = self.discover_tag_details(tag_name)
    
            # Récupérer le digest réel de l'image
            digest = self.discover_digest(tag_name)
    
            image_location = (
                f"{self.namespace}/"
                f"{self.repository}:{tag_name}"
            )
    
            images.append({
                "name": tag_name,
                "location": image_location,
                "digest": digest,
                "last_updated": details.get("last_updated"),
                "tag_status": details.get("tag_status")
            })
    
        return images