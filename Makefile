.PHONY: hooks pins format type test coverage check
.PHONY: user posts comments follows notifications directmessages explores
.PHONY: _app-check man

DOCKER = docker compose exec django uv run

# ─── 전체 ────────────────────────────────────────────────────────────────────

# .git/hooks 는 Git 이 추적하지 않아 클론·pull 로 전파되지 않는다. 각자 1회 실행 필요.
# 다른 타깃과 달리 호스트에서 실행한다 — .git/hooks 에 파일을 쓰는 작업이고
# 컨테이너에는 git 이 없다.
#
# uv run 이 아니라 uv tool install 을 쓰는 이유: uv run 은 명령 실행 전에 프로젝트
# 의존성을 동기화하는데, dev 그룹에 torch(~400MB)가 있어 632바이트짜리 훅 파일 하나
# 만들려고 ~900MB 를 내려받게 된다. uv tool 은 프로젝트와 분리된 환경에 pre-commit 만
# 설치하므로(~30MB), .venv 를 지우거나 --no-dev 로 재설치해도 훅이 계속 동작한다.
# 두 번째 줄에 uv tool run 을 쓰는 이유: uv tool install 이 실행 파일을 ~/.local/bin 에
# 두는데 그 경로가 PATH 에 없는 환경이 있어(설치 시 uv 가 경고한다) 곧바로 pre-commit 을
# 부르면 실패한다. uv tool run 은 PATH 와 무관하게 설치된 도구를 찾아 실행한다.
hooks:
	uv tool install pre-commit==4.6.0
	uv tool run pre-commit install

# 훅 설정(.pre-commit-config.yaml)과 uv.lock 의 버전이 어긋났는지 대조한다.
# 훅은 uv.lock 을 읽지 못해 두 파일이 따로 관리되므로, uv lock 이 돌 때마다 벌어질 수 있다.
pins:
	$(DOCKER) python scripts/check_hook_pins.py

format:
	$(DOCKER) black .
	$(DOCKER) isort .

type:
	$(DOCKER) mypy .

test:
	$(DOCKER) pytest || [ $$? -eq 5 ]

coverage:
	$(DOCKER) coverage run -m pytest
	$(DOCKER) coverage report -m

check: pins format type coverage

# ─── 앱별 ────────────────────────────────────────────────────────────────────

_app-check:
	@if [ -z "$(APP)" ]; then echo "ERROR: APP is not set. Use: make user (or posts, comments, follows, notifications, directmessages, explores)"; exit 1; fi
	$(DOCKER) black apps/$(APP)/
	$(DOCKER) isort apps/$(APP)/
	$(DOCKER) mypy apps/$(APP)/
	$(DOCKER) coverage run -m pytest tests/test_$(APP)/ || [ $$? -eq 5 ]
	$(DOCKER) coverage report --include="apps/$(APP)/*" -m

user:
	$(MAKE) _app-check APP=users

posts:
	$(MAKE) _app-check APP=posts

comments:
	$(MAKE) _app-check APP=comments

follows:
	$(MAKE) _app-check APP=follows

notifications:
	$(MAKE) _app-check APP=notifications

directmessages:
	$(MAKE) _app-check APP=directmessages

explores:
	$(MAKE) _app-check APP=explores

# ─── misc ────────────────────────────────────────────────────────────────────

man:  # -it 플래그 필요로 DOCKER 변수 미사용
	docker exec -it danim-backend-django-1 uv run python manage.py "$(a)"
