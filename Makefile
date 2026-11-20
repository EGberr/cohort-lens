.PHONY: install data api web dev test lint eval docker

install:            ## Install backend (uv) and frontend (pnpm) dependencies
	cd backend && uv sync
	cd web && pnpm install

data:               ## Regenerate the synthetic panel, the report corpus and the index
	cd backend && uv run python -m app.ingest build

api:                ## Run the FastAPI backend on :8000
	cd backend && uv run uvicorn app.main:app --reload --port 8000

web:                ## Run the Next.js frontend on :3000
	cd web && pnpm dev

dev:                ## Run both (Ctrl-C stops both)
	$(MAKE) -j2 api web

test:               ## Backend tests + frontend type-check and lint
	cd backend && uv run pytest -q
	cd web && pnpm exec tsc --noEmit && pnpm lint

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

eval:               ## Retrieval + answer benchmarks -> data/eval/report.{json,md}
	cd backend && uv run python -m eval.run_eval

docker:             ## Build and run the full stack with Docker Compose
	docker compose up --build
