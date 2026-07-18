.PHONY: setup docker-up docker-down run-dev worker-run test clean

PYTHON = backend/.venv/bin/python
PIP = backend/.venv/bin/pip

setup:
	@echo "Creating virtual environment in backend/..."
	python3 -m venv backend/.venv
	@echo "Installing requirements..."
	PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 $(PIP) install -r backend/requirements.txt
	@echo "Setup complete. Virtual environment ready in backend/.venv"

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

run-dev:
	cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

worker-run:
	cd backend && PYTHONPATH=. .venv/bin/celery -A app.tasks.worker.celery_app worker --loglevel=info

test:
	cd backend && PYTHONPATH=. .venv/bin/pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.venv

frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev
