#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# scripts/bootstrap-k3s.sh
# Bootstraps the full platform on an existing k3s cluster.
# Equivalent to the Kind bootstrap-kind.sh but for k3s.
#
# Usage:
#   ./scripts/bootstrap-k3s.sh [--skip-monitoring] [--dry-run]
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SKIP_MONITORING=false
DRY_RUN=false
NAMESPACE_APP=dev
NAMESPACE_MONITORING=monitoring
NAMESPACE_INGRESS=ingress-nginx
NAMESPACE_JENKINS=jenkins

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${CYAN}[bootstrap]${NC} $*"; }
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }
step() { echo ""; echo -e "${BOLD}══ $* ══${NC}"; }

for arg in "$@"; do
  case $arg in
    --skip-monitoring) SKIP_MONITORING=true ;;
    --dry-run) DRY_RUN=true ;;
  esac
done

run() {
  if $DRY_RUN; then
    echo -e "${YELLOW}[dry-run]${NC} $*"
  else
    "$@"
  fi
}

check_deps() {
  step "Checking dependencies"
  for cmd in kubectl helm kustomize; do
    if command -v "$cmd" &>/dev/null; then
      ok "$cmd found: $(command -v "$cmd")"
    else
      err "Required tool not found: $cmd"
    fi
  done
  kubectl cluster-info &>/dev/null || err "Cannot connect to Kubernetes cluster"
  ok "Cluster reachable"
}

add_helm_repos() {
  step "Adding Helm repositories"
  run helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>/dev/null || true
  run helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
  run helm repo add grafana https://grafana.github.io/helm-charts 2>/dev/null || true
  run helm repo add jenkins https://charts.jenkins.io 2>/dev/null || true
  run helm repo update
  ok "Helm repos updated"
}

create_namespaces() {
  step "Creating namespaces"
  for ns in "$NAMESPACE_APP" "$NAMESPACE_MONITORING" "$NAMESPACE_INGRESS" "$NAMESPACE_JENKINS"; do
    if kubectl get namespace "$ns" &>/dev/null; then
      warn "Namespace $ns already exists"
    else
      run kubectl create namespace "$ns"
      ok "Created namespace: $ns"
    fi
  done
}
