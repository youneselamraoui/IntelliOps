# IntelliOps : lancement avec Docker

Toutes les commandes se lancent depuis la RACINE du dépôt.
Docker et Compose sont déjà installés sur les VM (playbook Ansible 01-docker.yml).

## Préparer la VM
1. cp .env.staging.example .env      (ou .env.prod.example en production)
2. Remplacer le mot de passe dans .env.

## VM base de données (en premier)
docker compose --project-directory . -f infrastructure/docker-compose.db.yml up -d
docker compose --project-directory . -f infrastructure/docker-compose.db.yml ps

## VM application (ensuite)
Staging :
docker compose -f docker-compose.yml -f infrastructure/docker-compose.staging.yml up -d --build
Production :
docker compose -f docker-compose.yml -f infrastructure/docker-compose.prod.yml up -d --build

## Vérifier la configuration avant de lancer
Remplacer up -d --build par config.

## Arrêter
Remplacer up -d --build par down.
Ne jamais utiliser -v en production : cela supprime les données.