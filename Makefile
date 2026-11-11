.PHONY: test lint up down bench seed

# Run all backend tests (requires DB on 18401)
test:
	cd backend && \
	FAKE_LLM=true HF_HOME=./hf_cache \
	DATABASE_URL="postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot" \
	python -m pytest tests/ -v

# Frontend unit tests
test-frontend:
	cd frontend && npm test

# Lint backend
lint:
	cd backend && ruff check app/ tests/

# Lint frontend
lint-frontend:
	cd frontend && npm run lint && npx tsc --noEmit

# Start DB container
up:
	docker run -d --name placement-copilot-db \
		-e POSTGRES_USER=copilot \
		-e POSTGRES_PASSWORD=copilot \
		-e POSTGRES_DB=placement_copilot \
		-p 18401:5432 \
		pgvector/pgvector:pg17 || true

# Stop and remove DB container
down:
	docker stop placement-copilot-db || true
	docker rm placement-copilot-db || true

# Generate and seed synthetic corpus
seed:
	cd data/synthetic && python generator.py data/synthetic
	cd backend && \
	FAKE_LLM=true HF_HOME=./hf_cache \
	DATABASE_URL="postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot" \
	python -c "import asyncio, sys; sys.path.insert(0,'.');from scripts.seed import main; asyncio.run(main())"

# Run extraction / retrieval / answer evals (fake LLM mode)
bench:
	cd evals && \
	FAKE_LLM=true HF_HOME=../backend/hf_cache \
	DATABASE_URL="postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot" \
	python run_evals.py --fake-llm --output results/
