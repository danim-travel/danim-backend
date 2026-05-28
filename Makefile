.PHONY: format type test coverage check

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
