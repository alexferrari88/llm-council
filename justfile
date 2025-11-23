# LLM Council - Common Workflows

# Default recipe: show available commands
default:
    @just --list

# =============================================================================
# Primary Commands (Docker-first)
# =============================================================================

# Start the application (docker)
up:
    docker compose up -d

# Stop the application
down:
    docker compose down

# View logs
logs:
    docker compose logs -f

# Rebuild and restart
restart:
    docker compose down
    docker compose build
    docker compose up -d

# Build images
build:
    docker compose build

# Full reset: rebuild from scratch
rebuild:
    docker compose down
    docker compose build --no-cache
    docker compose up -d

# =============================================================================
# Local Development (without Docker)
# =============================================================================

# Install all dependencies locally
install:
    uv sync
    cd frontend && npm install

# Start both backend and frontend locally
dev-local:
    #!/usr/bin/env bash
    set -e
    echo "Starting LLM Council..."
    echo ""
    echo "Starting backend on http://localhost:8001..."
    uv run python -m backend.main &
    BACKEND_PID=$!
    sleep 2
    echo "Starting frontend on http://localhost:5173..."
    cd frontend && npm run dev &
    FRONTEND_PID=$!
    echo ""
    echo "✓ LLM Council is running!"
    echo "  Backend:  http://localhost:8001"
    echo "  Frontend: http://localhost:5173"
    echo ""
    echo "Press Ctrl+C to stop both servers"
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
    wait

# Start backend only (local)
backend:
    uv run python -m backend.main

# Start frontend only (local)
frontend:
    cd frontend && npm run dev

# Build frontend for production (local)
build-frontend:
    cd frontend && npm run build

# Preview production build (local)
preview:
    cd frontend && npm run preview

# =============================================================================
# Code Quality
# =============================================================================

# Lint frontend
lint:
    cd frontend && npm run lint

# Format Python code with ruff
format:
    uv run ruff format backend

# Check Python code with ruff
check:
    uv run ruff check backend

# Fix Python linting issues
fix:
    uv run ruff check --fix backend

# =============================================================================
# Data & Testing
# =============================================================================

# Clean conversation data
clean-data:
    rm -rf data/conversations/*
    echo "Conversation data cleared"

# Test OpenRouter API connectivity
test-openrouter:
    uv run python test_openrouter.py
