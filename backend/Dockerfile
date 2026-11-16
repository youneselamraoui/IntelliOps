# syntax=docker/dockerfile:1.7
ARG PHP_VERSION=8.4-fpm-alpine

# ──────────────────────── STAGE 1 — BASE ───────────────────────────

FROM php:${PHP_VERSION} AS base

WORKDIR /var/www/html

COPY --from=ghcr.io/mlocati/php-extension-installer /usr/bin/install-php-extensions /usr/local/bin/

RUN apk add --no-cache openssl git unzip \
    && install-php-extensions pdo_pgsql pgsql bcmath intl zip gd opcache pcntl

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

ENV COMPOSER_ALLOW_SUPERUSER=1 \
    COMPOSER_CACHE_DIR=/tmp/composer-cache

# HMVC : les composer.json des modules doivent exister avant "composer install"
COPY composer.json composer.lock ./
COPY Modules ./Modules


# ─────────────────────── STAGE 2 — DEVELOPMENT ────────────────────

FROM base AS development

ENV APP_ENV=local \
    APP_DEBUG=true

RUN --mount=type=cache,target=/tmp/composer-cache \
    composer install --no-interaction --no-scripts --prefer-dist

COPY . .

RUN composer dump-autoload \
    && chmod +x entrypoint.sh \
    && chown -R www-data:www-data storage bootstrap/cache

EXPOSE 8000

ENTRYPOINT ["sh", "./entrypoint.sh"]
CMD ["dev"]


# ──────────────────────── STAGE 3 — PRODUCTION ────────────────────

FROM base AS production

ENV APP_ENV=production \
    APP_DEBUG=false

RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini" \
    && printf "opcache.enable=1\nopcache.memory_consumption=192\nopcache.max_accelerated_files=20000\nopcache.validate_timestamps=0\n" \
       > "$PHP_INI_DIR/conf.d/zz-opcache.ini"

RUN --mount=type=cache,target=/tmp/composer-cache \
    composer install --no-dev --no-interaction --no-scripts --prefer-dist --no-autoloader

COPY . .

RUN composer dump-autoload --no-dev --classmap-authoritative \
    && chmod +x entrypoint.sh \
    && mkdir -p storage/framework/cache storage/framework/sessions storage/framework/views storage/logs bootstrap/cache \
    && chown -R www-data:www-data storage bootstrap/cache

EXPOSE 9000

ENTRYPOINT ["sh", "./entrypoint.sh"]
CMD ["start"]