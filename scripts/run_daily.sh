#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

cd "$PROJECT_DIR"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

log() { echo "[$(date '+%F %T')] $*"; }

run_step() {
    local name="$1"; shift
    log "▶ ${name} 시작"
    if "$@"; then
        log "✔ ${name} 완료"
    else
        local code=$?
        log "✗ ${name} 실패 (exit=${code}) — 파이프라인 중단"
        exit "$code"
    fi
}

log "==== 일일 파이프라인 시작 ===="
run_step "generate_embeddings" docker exec danim-backend-django-1 uv run manage.py generate_embeddings
run_step "load_codewords"      docker exec danim-backend-django-1 uv run manage.py load_codewords
run_step "update_user_taste"   docker exec danim-backend-django-1 uv run manage.py update_user_taste
log "==== 일일 파이프라인 완료 ===="
