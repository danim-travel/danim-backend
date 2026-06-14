.PHONY: format type test coverage check
.PHONY: man

format:
	docker compose exec django uv run black .
	docker compose exec django uv run isort .

type:
	docker compose exec django uv run mypy .

test:
	docker compose exec django uv run pytest || [ $$? -eq 5 ]

coverage:
	docker compose exec django uv run coverage run manage.py test tests
	docker compose exec django uv run coverage report -m

check: format type test coverage

# misc
man:
	docker exec -it danim-backend-django-1 uv run python manage.py "$(a)"
