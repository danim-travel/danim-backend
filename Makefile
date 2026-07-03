.PHONY: format type test coverage check
.PHONY: user posts comments follows notifications directmessages explores
.PHONY: _app-check man

DOCKER = docker compose exec django uv run

# ─── 전체 ────────────────────────────────────────────────────────────────────

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

check: format type coverage

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
