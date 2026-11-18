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

# Entrypoint copié HORS de /var/www/html : en dev, le bind mount ./backend
# ne l'écrase pas, et le sed retire les fins de ligne Windows (CRLF)
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh


# ─────────────────────── STAGE 2 — DEVELOPMENT ────────────────────
FROM base AS development

ENV APP_ENV=local \
    APP_DEBUG=true

RUN --mount=type=cache,target=/tmp/composer-cache \
    composer install --no-interaction --no-scripts --prefer-dist

COPY . .

RUN composer dump-autoload --no-scripts \
    && chown -R www-data:www-data storage bootstrap/cache

EXPOSE 8000

ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]
CMD ["dev"]


# ──────────────────────── STAGE 3 — PRODUCTION ────────────────────
# Utilisé par prod ET staging (php-fpm sur 9000, appelé en FastCGI par le nginx du frontend)
FROM base AS production

ENV APP_ENV=production \
    APP_DEBUG=false

RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini" \
    && printf "opcache.enable=1\nopcache.memory_consumption=192\nopcache.max_accelerated_files=20000\nopcache.validate_timestamps=0\n" \
       > "$PHP_INI_DIR/conf.d/zz-opcache.ini"

RUN --mount=type=cache,target=/tmp/composer-cache \
    composer install --no-dev --no-interaction --no-scripts --prefer-dist --no-autoloader

COPY . .

RUN composer dump-autoload --no-dev --no-scripts --classmap-authoritative \
    && rm -f bootstrap/cache/*.php \
    && mkdir -p storage/framework/cache storage/framework/sessions storage/framework/views storage/logs bootstrap/cache \
    && chown -R www-data:www-data storage bootstrap/cache

EXPOSE 9000

ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]
CMD ["start"]