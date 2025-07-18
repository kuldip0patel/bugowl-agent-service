# syntax=docker/dockerfile:1
# check=skip=SecretsUsedInArgOrEnv

# This is the Dockerfile for browser-use, it bundles the following dependencies:
#     python3, pip, playwright, chromium, browser-use and its dependencies.
# Usage:
#     git clone https://github.com/browser-use/browser-use.git && cd browser-use
#     docker build . -t browseruse --no-cache
#     docker run -v "$PWD/data":/data browseruse
#     docker run -v "$PWD/data":/data browseruse --version
# Multi-arch build:
#     docker buildx create --use
#     docker buildx build . --platform=linux/amd64,linux/arm64--push -t browseruse/browseruse:some-tag
#
# Read more: https://docs.browser-use.com

#########################################################################################


FROM python:3.12-slim

LABEL name="browseruse" \
    maintainer="Nick Sweeting <dockerfile@browser-use.com>" \
    description="Make websites accessible for AI agents. Automate tasks online with ease." \
    homepage="https://github.com/browser-use/browser-use" \
    documentation="https://docs.browser-use.com" \
    org.opencontainers.image.title="browseruse" \
    org.opencontainers.image.vendor="browseruse" \
    org.opencontainers.image.description="Make websites accessible for AI agents. Automate tasks online with ease." \
    org.opencontainers.image.source="https://github.com/browser-use/browser-use" \
    com.docker.image.source.entrypoint="Dockerfile" \
    com.docker.desktop.extension.api.version=">= 1.4.7" \
    com.docker.desktop.extension.icon="https://avatars.githubusercontent.com/u/192012301?s=200&v=4" \
    com.docker.extension.publisher-url="https://browser-use.com" \
    com.docker.extension.screenshots='[{"alt": "Screenshot of CLI splashscreen", "url": "https://github.com/user-attachments/assets/3606d851-deb1-439e-ad90-774e7960ded8"}, {"alt": "Screenshot of CLI running", "url": "https://github.com/user-attachments/assets/d018b115-95a4-4ac5-8259-b750bc5f56ad"}]' \
    com.docker.extension.detailed-description='See here for detailed documentation: https://docs.browser-use.com' \
    com.docker.extension.changelog='See here for release notes: https://github.com/browser-use/browser-use/releases' \
    com.docker.extension.categories='web,utility-tools,ai'

ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

######### Environment Variables #################################

# Global system-level config
ENV TZ=UTC \
    LANGUAGE=en_US:en \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 \
    PYTHONIOENCODING=UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_CACHE_DIR=/root/.cache/uv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_PREFERENCE=only-system \
    npm_config_loglevel=error \
    IN_DOCKER=True

# User config
ENV BROWSERUSE_USER="browseruse" \
    DEFAULT_PUID=911 \
    DEFAULT_PGID=911

# Paths
ENV CODE_DIR=/app \
    DATA_DIR=/data \
    VENV_DIR=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

ENV PYTHONUNBUFFERED=1

# Playwright environment variables to ensure browsers are found
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Add AWS Arguments and Environment Variables
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_SECRET_NAME
ARG AWS_REGION_NAME
ARG AWS_IAM_ROLE

ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
ENV AWS_SECRET_NAME=$AWS_SECRET_NAME
ENV AWS_REGION_NAME=$AWS_REGION_NAME
ENV AWS_IAM_ROLE=$AWS_IAM_ROLE
ENV DJANGO_SETTINGS_MODULE=api.settings
ENV PYTHONPATH=/app:/app/bugowl/api

# Build shell config
SHELL ["/bin/bash", "-o", "pipefail", "-o", "errexit", "-o", "errtrace", "-o", "nounset", "-c"] 

# Force apt to leave downloaded binaries in /var/cache/apt (massively speeds up Docker builds)
RUN echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/99keep-cache \
    && echo 'APT::Install-Recommends "0";' > /etc/apt/apt.conf.d/99no-intall-recommends \
    && echo 'APT::Install-Suggests "0";' > /etc/apt/apt.conf.d/99no-intall-suggests \
    && rm -f /etc/apt/apt.conf.d/docker-clean

# Print debug info about build and save it to disk, for human eyes only, not used by anything else
RUN (echo "[i] Docker build for Browser Use $(cat /VERSION.txt) starting..." \
    && echo "PLATFORM=${TARGETPLATFORM} ARCH=$(uname -m) ($(uname -s) ${TARGETARCH} ${TARGETVARIANT})" \
    && echo "BUILD_START_TIME=$(date +"%Y-%m-%d %H:%M:%S %s") TZ=${TZ} LANG=${LANG}" \
    && echo \
    && echo "CODE_DIR=${CODE_DIR} DATA_DIR=${DATA_DIR} PATH=${PATH}" \
    && echo \
    && uname -a \
    && cat /etc/os-release | head -n7 \
    && which bash && bash --version | head -n1 \
    && which dpkg && dpkg --version | head -n1 \
    && echo -e '\n\n' && env && echo -e '\n\n' \
    && which python && python --version \
    && which pip && pip --version \
    && echo -e '\n\n' \
    ) | tee -a /VERSION.txt

# Create non-privileged user for browseruse and chrome
RUN echo "[*] Setting up $BROWSERUSE_USER user uid=${DEFAULT_PUID}..." \
    && groupadd --system $BROWSERUSE_USER \
    && useradd --system --create-home --gid $BROWSERUSE_USER --groups audio,video $BROWSERUSE_USER \
    && usermod -u "$DEFAULT_PUID" "$BROWSERUSE_USER" \
    && groupmod -g "$DEFAULT_PGID" "$BROWSERUSE_USER" \
    && mkdir -p /data \
    && mkdir -p /home/$BROWSERUSE_USER/.config \
    && chown -R $BROWSERUSE_USER:$BROWSERUSE_USER /home/$BROWSERUSE_USER \
    && ln -s $DATA_DIR /home/$BROWSERUSE_USER/.config/browseruse \
    && echo -e "\nBROWSERUSE_USER=$BROWSERUSE_USER PUID=$(id -u $BROWSERUSE_USER) PGID=$(id -g $BROWSERUSE_USER)\n\n" \
    | tee -a /VERSION.txt
    # DEFAULT_PUID and DEFAULT_PID are overridden by PUID and PGID in /bin/docker_entrypoint.sh at runtime
    # https://docs.linuxserver.io/general/understanding-puid-and-pgid

# Install base apt dependencies (adding backports to access more recent apt updates)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=apt-$TARGETARCH$TARGETVARIANT \
    echo "[+] Installing APT base system dependencies for $TARGETPLATFORM..." \
#     && echo 'deb https://deb.debian.org/debian bookworm-backports main contrib non-free' > /etc/apt/sources.list.d/backports.list \
    && mkdir -p /etc/apt/keyrings \
    && apt-get update -qq \
    && apt-get install -qq -y --no-install-recommends \
        # 1. packaging dependencies
        apt-transport-https ca-certificates apt-utils gnupg2 unzip curl wget grep \
        # 2. docker and init system dependencies:
        # dumb-init gosu cron zlib1g-dev \
        # 3. frivolous CLI helpers to make debugging failed archiving easierL
        nano iputils-ping dnsutils jq \
        # tree yq procps \
        # 4. browser dependencies: (auto-installed by playwright install --with-deps chromium)
     #    libnss3 libxss1 libasound2 libx11-xcb1 \
     #    fontconfig fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-khmeros fonts-kacst fonts-symbola fonts-noto fonts-freefont-ttf \
     #    at-spi2-common fonts-liberation fonts-noto-color-emoji fonts-tlwg-loma-otf fonts-unifont libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libavahi-client3 \
     #    libavahi-common-data libavahi-common3 libcups2 libfontenc1 libice6 libnspr4 libnss3 libsm6 libunwind8 \
     #    libxaw7 libxcomposite1 libxdamage1 libxfont2 \
     #    # 5. x11/xvfb dependencies:
     #    libxkbfile1 libxmu6 libxpm4 libxt6 x11-xkb-utils x11-utils xfonts-encodings \
     #    xfonts-scalable xfonts-utils xserver-common xvfb \
     && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy only dependency manifest
WORKDIR /app
COPY pyproject.toml uv.lock* /app/

RUN --mount=type=cache,target=/root/.cache,sharing=locked,id=cache-$TARGETARCH$TARGETVARIANT \
    echo "[+] Setting up venv using uv in $VENV_DIR..." \
    && ( \
     which uv && uv --version \
     && uv venv \
     && which python | grep "$VENV_DIR" \
     && python --version \
    ) | tee -a /VERSION.txt

# Install playwright using pip (with version from pyproject.toml)
RUN --mount=type=cache,target=/root/.cache,sharing=locked,id=cache-$TARGETARCH$TARGETVARIANT \
     echo "[+] Installing playwright via pip using version from pyproject.toml..." \
     && ( \
        uv pip install "$(grep -oP 'p....right>=([0-9.])+' pyproject.toml | head -n 1)" \
        && uv pip install "$(grep -oP 'p....right>=([0-9.])+' pyproject.toml | tail -n 1)" \
        && PLAYWRIGHT_VERSION=$(grep -E "playwright>=" pyproject.toml | grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+" | head -1) \
        && PATCHRIGHT_VERSION=$(grep -E "patchright>=" pyproject.toml | grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+" | head -1) \
        && echo "Installing playwright==$PLAYWRIGHT_VERSION patchright==$PATCHRIGHT_VERSION" \
        && uv pip install playwright==$PLAYWRIGHT_VERSION patchright==$PATCHRIGHT_VERSION \
        && which playwright \
        && playwright --version \
        && echo -e '\n\n' \
     ) | tee -a /VERSION.txt

# Install Chromium using playwright
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=apt-$TARGETARCH$TARGETVARIANT \
    --mount=type=cache,target=/root/.cache,sharing=locked,id=cache-$TARGETARCH$TARGETVARIANT \
    echo "[+] Installing chromium apt pkgs and binary to /root/.cache/ms-playwright..." \
    && apt-get update -qq \
    && playwright install --with-deps --no-shell chromium \
    # && playwright install --with-deps chrome \
    && rm -rf /var/lib/apt/lists/* \
    && export CHROME_BINARY="$(python -c 'from playwright.sync_api import sync_playwright; print(sync_playwright().start().chromium.executable_path)')" \
    && ln -s "$CHROME_BINARY" /usr/bin/chromium-browser \
    && ln -s "$CHROME_BINARY" /app/chromium-browser \
    && mkdir -p "/home/${BROWSERUSE_USER}/.config/chromium/Crash Reports/pending/" \
    && chown -R "$BROWSERUSE_USER:$BROWSERUSE_USER" "/home/${BROWSERUSE_USER}/.config" \
    && chmod -R 755 "$PLAYWRIGHT_BROWSERS_PATH" \
    && ( \
        which chromium-browser && /usr/bin/chromium-browser --version \
        && echo "Playwright browsers installed at: $PLAYWRIGHT_BROWSERS_PATH" \
        && ls -la "$PLAYWRIGHT_BROWSERS_PATH" || echo "Browser path not found" \
        && echo "Browser permissions:" \
        && ls -la "$PLAYWRIGHT_BROWSERS_PATH"/*/ | head -5 || echo "Cannot list browser subdirectories" \
        && which chromium-browser && /usr/bin/chromium-browser --version \
        && echo -e '\n\n' \
    ) | tee -a /VERSION.txt

RUN --mount=type=cache,target=/root/.cache,sharing=locked,id=cache-$TARGETARCH$TARGETVARIANT \
     echo "[+] Installing browser-use pip sub-dependencies..." \
     && ( \
        uv sync --all-extras --no-dev --no-install-project \
        && echo -e '\n\n' \
     ) | tee -a /VERSION.txt

# Copy the rest of the browser-use codebase
COPY . /app

# Install the browser-use package and all of its optional dependencies
RUN --mount=type=cache,target=/root/.cache,sharing=locked,id=cache-$TARGETARCH$TARGETVARIANT \
     echo "[+] Installing browser-use pip library from source..." \
     && ( \
        uv sync --all-extras --locked --no-dev \
        && which browser-use \
        && browser-use --version 2>&1 \
        && echo -e '\n\n' \
     ) | tee -a /VERSION.txt

RUN mkdir -p "$DATA_DIR/profiles/default" \
    && chown -R $BROWSERUSE_USER:$BROWSERUSE_USER "$DATA_DIR" "$DATA_DIR"/* \
    && ( \
        echo -e "\n\n[√] Finished Docker build successfully. Saving build summary in: /VERSION.txt" \
        && echo -e "PLATFORM=${TARGETPLATFORM} ARCH=$(uname -m) ($(uname -s) ${TARGETARCH} ${TARGETVARIANT})\n" \
        && echo -e "BUILD_END_TIME=$(date +"%Y-%m-%d %H:%M:%S %s")\n\n" \
    ) | tee -a /VERSION.txt




# Create necessary directories with proper permissions
RUN mkdir -p /app/logs && \
    mkdir -p /app/staticfiles && \
    mkdir -p /app/media && \
    mkdir -p /logs && \
    chmod -R 777 /app/logs && \
    chmod -R 777 /app/staticfiles && \
    chmod -R 777 /app/media && \
    chmod -R 777 /logs


COPY entrypoint.sh /app/
COPY celery-entrypoint.sh /app/
COPY verify-browsers.sh /app/
# Convert line endings and set permissions
RUN sed -i 's/\r$//' /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/celery-entrypoint.sh && \
    sed -i 's/\r$//' /app/verify-browsers.sh && \
    chmod +x /app/entrypoint.sh && \
    chmod +x /app/celery-entrypoint.sh && \
    chmod +x /app/verify-browsers.sh


ENV PATH="/app/.venv/bin:$PATH"

RUN ["apt-get", "update"]
RUN ["apt-get", "install", "-y", "vim"]


# Switch back to root for entrypoint script execution
USER root

# Set working directory
WORKDIR /app

# Default command (can be overridden by docker-compose)
CMD ["/bin/bash"]
USER "$BROWSERUSE_USER"
VOLUME "$DATA_DIR"
EXPOSE 9242
EXPOSE 9222
EXPOSE 8010
EXPOSE 8020

# HEALTHCHECK --interval=30s --timeout=20s --retries=15 \
#     CMD curl --silent 'http://localhost:8000/health/' | grep -q 'OK'

ENTRYPOINT ["browser-use"]
