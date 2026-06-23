#!/usr/bin/env bash
#
# run_rebuild.sh — 수동 전체 재구축 (--all)
#   generate_embeddings --all -> bake_codebook -> load_codewords --all -> update_user_taste --all
#
# 각 단계마다 [y/N] 으로 물어보고, 정확히 'y' 를 입력했을 때만 실행한다.
# 'y' 이외의 입력은 그 단계를 스킵하고 다음 단계로 넘어간다.
#
set -uo pipefail

# ===== 환경에 맞게 수정 =====
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_ACTIVATE="$PROJECT_DIR/.venv/bin/activate"
PYTHON="python"
# export DJANGO_SETTINGS_MODULE="config.settings.prod"
LOG_DIR="$PROJECT_DIR/logs"
# ============================

cd "$PROJECT_DIR"
if [ -n "$VENV_ACTIVATE" ] && [ -f "$VENV_ACTIVATE" ]; then
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
fi
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/rebuild_$(date +%Y%m%d_%H%M%S).log"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"; }

# 확인 후 실행. 'y' 가 아니면 스킵. 실행 실패 시 계속 여부를 다시 물음.
confirm_run() {
    local desc="$1"; shift
    echo
    echo "────────────────────────────────────────────"
    echo "다음 단계: ${desc}"
    echo "     명령: $*"
    read -r -p "실행할까요? [y/N]: " ans
    if [ "$ans" != "y" ]; then
        log "⏭  스킵: ${desc}  (입력='${ans}')"
        return 0
    fi

    log "▶ 실행: ${desc}"
    "$@" 2>&1 | tee -a "$LOG_FILE"
    local code=${PIPESTATUS[0]}      # tee 가 아니라 실제 명령의 종료코드
    if [ "$code" -eq 0 ]; then
        log "✔ 완료: ${desc}"
        return 0
    fi

    log "✗ 실패: ${desc} (exit=${code})"
    read -r -p "실패했습니다. 다음 단계를 계속할까요? [y/N]: " cont
    if [ "$cont" != "y" ]; then
        log "사용자 요청으로 파이프라인 중단"
        exit "$code"
    fi
}

echo "==== 수동 전체 재구축 (--all) ===="
echo "주의: 단계는 파이프라인 순서대로 진행됩니다."
echo "      generate_embeddings --all 은 전역 평균(embedding_mean.npy)을 새로 계산하므로,"
echo "      이후 bake_codebook / load_codewords 까지 함께 돌려야 정합성이 맞습니다."

confirm_run "임베딩 전체 재생성 + 전역 평균 재계산" docker exec -it danim-backend-django-1 uv run manage.py generate_embeddings --all
confirm_run "코드북 재생성 (K-means, --all 옵션 없음)" docker exec -it danim-backend-django-1 uv run manage.py bake_codebook
confirm_run "코드워드 전체 재배정" docker exec -it danim-backend-django-1 uv run manage.py load_codewords --all
confirm_run "유저 취향 전체 재계산" docker exec -it danim-backend-django-1 uv run manage.py update_user_taste --all

echo
log "==== 재구축 스크립트 종료 ===="
