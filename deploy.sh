#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# deploy.sh — Docker Compose lifecycle manager
# Usage:
#   ./deploy.sh start    [profile...]   default: core app monitoring
#   ./deploy.sh stop     [profile...]
#   ./deploy.sh restart  [profile...]
#   ./deploy.sh status
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/environments/local/.env"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
DEFAULT_PROFILES=(core app monitoring)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

log()  { echo -e "${CYAN}[deploy]${NC} $*"; }
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }

check_deps() {
  for cmd in docker; do
    command -v "$cmd" &>/dev/null || err "Required tool not found: $cmd"
  done
  docker compose version &>/dev/null || err "docker compose (v2) is required"
  [[ -f "$ENV_FILE" ]] || err ".env not found at $ENV_FILE — copy .env.example and fill values"
}

build_profile_args() {
  local profiles=("$@")
  local args=()
  for p in "${profiles[@]}"; do
    args+=(--profile "$p")
  done
  echo "${args[@]}"
}

cmd_start() {
  local profiles=("${@:-${DEFAULT_PROFILES[@]}}")
  log "Starting profiles: ${profiles[*]}"
  # shellcheck disable=SC2046
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
    $(build_profile_args "${profiles[@]}") \
    up -d --build --remove-orphans
  log "Waiting for health checks..."
  sleep 30
  cmd_status
}

cmd_stop() {
  local profiles=("${@:-${DEFAULT_PROFILES[@]}}")
  log "Stopping profiles: ${profiles[*]}"
  # shellcheck disable=SC2046
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
    $(build_profile_args "${profiles[@]}") \
    down --remove-orphans
  ok "Stopped."
}

cmd_restart() {
  cmd_stop "$@"
  cmd_start "$@"
}

cmd_status() {
  echo ""
  echo -e "${BOLD}Container Status${NC}"
  echo "────────────────────────────────────────────────────────"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
    --profile core --profile app --profile monitoring \
    ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

  echo ""
  echo -e "${BOLD}Health Summary${NC}"
  echo "────────────────────────────────────────────────────────"
  local all_healthy=true
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    health=$(docker inspect --format '{{.State.Health.Status}}' "$name" 2>/dev/null || echo "no healthcheck")
    if [[ "$health" == "healthy" ]]; then
      ok "$name → healthy"
    elif [[ "$health" == "no healthcheck" ]]; then
      warn "$name → no healthcheck defined"
    else
      echo -e "${RED}[✗]${NC} $name → $health"
      all_healthy=false
    fi
  done < <(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
    --profile core --profile app --profile monitoring \
    ps --format "{{.Name}}" 2>/dev/null)

  echo ""
  if $all_healthy; then
    ok "All services healthy."
  else
    warn "Some services are not healthy — check logs with: docker compose logs <service>"
  fi
}

usage() {
  echo "Usage: $0 {start|stop|restart|status} [profile...]"
  echo "Profiles: core, app, monitoring (default: all three)"
  exit 1
}

check_deps

case "${1:-}" in
  start)   shift; cmd_start   "$@" ;;
  stop)    shift; cmd_stop    "$@" ;;
  restart) shift; cmd_restart "$@" ;;
  status)         cmd_status      ;;
  *)              usage            ;;
esac
