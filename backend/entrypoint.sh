#!/bin/sh
set -e

case "$1" in
  dev)
    # Migrations en dev : mets RUN_MIGRATIONS=true dans .env.dev si tu les veux au démarrage
    if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
      php artisan migrate --force
    fi
    exec php artisan serve --host=0.0.0.0 --port=8000
    ;;
  start)
    # Sans APP_KEY, Laravel plante au premier appel : on échoue tout de suite, avec un message clair
    if [ -z "${APP_KEY:-}" ]; then
      echo "ERREUR : APP_KEY manquant (vérifie le fichier .env utilisé par env_file)" >&2
      exit 1
    fi

    # Migrations : seulement si RUN_MIGRATIONS=true (staging : oui, prod : à la demande)
    if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
      php artisan migrate --force
    fi

    php artisan optimize
    chown -R www-data:www-data storage bootstrap/cache
    exec php-fpm
    ;;
  *)
    exec "$@"
    ;;
esac