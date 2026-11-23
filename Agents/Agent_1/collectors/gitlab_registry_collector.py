import requests
from urllib.parse import quote


class GitLabRegistryCollector:

    def __init__(self, gitlab_url, token, project_id):

        self.gitlab_url = gitlab_url.rstrip("/")
        self.project_id = quote(str(project_id), safe="")

        self.session = requests.Session()
        self.session.headers.update({
            "PRIVATE-TOKEN": token
        })

    def discover_repositories(self):

        url = (
            f"{self.gitlab_url}/api/v4/projects/"
            f"{self.project_id}/registry/repositories"
        )

        repositories = []

        while url:

            response = self.session.get(
                url,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                raise ValueError(
                    "Unexpected GitLab Registry API response"
                )

            repositories.extend(data)

            # Récupérer la page suivante si elle existe
            url = response.links.get("next", {}).get("url")

        return repositories
    
    def discover_tags(self, repository_id):
        url = (
            f"{self.gitlab_url}/api/v4/projects/"
            f"{self.project_id}/registry/repositories/"
            f"{repository_id}/tags"
        )
        tags = []
        while url:
            response = self.session.get(
                url,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError(
                    "Unexpected GitLab Registry tags response"
                )
            tags.extend(data)
            # Récupérer la page suivante
            url = response.links.get("next", {}).get("url")
        return tags
    
    def discover_images(self):
        repositories = self.discover_repositories()
        images = []
        for repository in repositories:
            repository_id = repository.get("id")
            if not repository_id:
                continue
            tags = self.discover_tags(repository_id)
            for tag in tags:
                print("Tag details:", tag)
                print("Available fields:", list(tag.keys()))
            for tag in tags:
                image_location = tag.get("location")
                if image_location:
                    images.append(image_location)
    
        # Éliminer les éventuels doublons
        return list(dict.fromkeys(images))
    
    def discover_images_with_details(self):
        repositories = self.discover_repositories()
        images = []
    
        for repository in repositories:
            repository_id = repository.get("id")
    
            if not repository_id:
                continue
    
            tags = self.discover_tags(repository_id)
    
            for tag in tags:
                tag_name = tag.get("name")
    
                if not tag_name:
                    continue
    
                details = self.discover_tag_details(
                    repository_id,
                    tag_name
                )
    
                images.append({
                    "name": details.get("name"),
                    "location": details.get("location"),
                    "digest": details.get("digest"),
                    "revision": details.get("revision"),
                    "created_at": details.get("created_at")
                })
    
        return images
    
    
    def discover_tag_details(self, repository_id, tag_name):
        encoded_tag = quote(str(tag_name), safe="")
    
        url = (
            f"{self.gitlab_url}/api/v4/projects/"
            f"{self.project_id}/registry/repositories/"
            f"{repository_id}/tags/{encoded_tag}"
        )
    
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
    
        data = response.json()
    
        if not isinstance(data, dict):
            raise ValueError("Unexpected GitLab Registry tag details response")
    
        return data