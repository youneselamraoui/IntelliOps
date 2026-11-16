#!/bin/sh
set -e

case "$1" in
  dev)
    exec php artisan serve --host=0.0.0.0 --port=8000
    ;;
  start)
    php artisan optimize
    exec php-fpm
    ;;
  *)
    exec "$@"
    ;;
esac