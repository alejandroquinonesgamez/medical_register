#!/usr/bin/env bash
# Invoca Docker Compose v2 (`docker compose`) o el binario v1 (`docker-compose`).
# Uso: source desde otros scripts del directorio scripts/
#
#   source "$SCRIPT_DIR/docker_compose.sh"
#   docker_compose build web

docker_compose_available() {
	command -v docker >/dev/null 2>&1 || return 1
	if docker compose version >/dev/null 2>&1; then
		return 0
	fi
	command -v docker-compose >/dev/null 2>&1
}

docker_compose() {
	local p="${COMPOSE_PROJECT_NAME:-medical_register}"
	local b="${COMPOSE_DOCKER_CLI_BUILD:-0}"
	local k="${DOCKER_BUILDKIT:-0}"
	if docker compose version >/dev/null 2>&1; then
		COMPOSE_DOCKER_CLI_BUILD="$b" DOCKER_BUILDKIT="$k" COMPOSE_PROJECT_NAME="$p" \
			docker compose "$@"
	elif command -v docker-compose >/dev/null 2>&1; then
		COMPOSE_DOCKER_CLI_BUILD="$b" DOCKER_BUILDKIT="$k" COMPOSE_PROJECT_NAME="$p" \
			docker-compose "$@"
	else
		echo "docker_compose: no se encontró 'docker compose' ni 'docker-compose'" >&2
		echo "  En Arch: sudo pacman -S docker-compose" >&2
		echo "  O instala el plugin: https://docs.docker.com/compose/install/" >&2
		return 127
	fi
}
