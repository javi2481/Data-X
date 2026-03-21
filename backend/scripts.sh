#!/bin/bash
# Data-X Backend - Development Scripts using uv
# Sprint 4: uv migration

set -e

# Ensure uv is available
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

case "$1" in
    install)
        echo "📦 Installing dependencies with uv..."
        uv sync
        echo "✅ Dependencies installed"
        ;;
    install-dev)
        echo "📦 Installing dev dependencies with uv..."
        uv sync --group dev
        echo "✅ Dev dependencies installed"
        ;;
    lock)
        echo "🔒 Generating lockfile..."
        uv lock
        echo "✅ Lockfile generated: uv.lock"
        ;;
    run)
        shift
        echo "🚀 Running: $@"
        uv run "$@"
        ;;
    test)
        echo "🧪 Running tests..."
        uv run pytest tests/ -v
        ;;
    lint)
        echo "🔍 Running linter..."
        uv run ruff check app/
        ;;
    format)
        echo "✨ Formatting code..."
        uv run ruff format app/
        ;;
    server)
        echo "🌐 Starting development server..."
        uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
        ;;
    shell)
        echo "🐚 Activating virtual environment..."
        source .venv/bin/activate
        exec $SHELL
        ;;
    upgrade)
        echo "⬆️ Upgrading dependencies..."
        uv lock --upgrade
        uv sync
        echo "✅ Dependencies upgraded"
        ;;
    clean)
        echo "🧹 Cleaning caches..."
        rm -rf __pycache__ .pytest_cache .ruff_cache
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        echo "✅ Caches cleaned"
        ;;
    *)
        echo "Data-X Backend - uv Scripts"
        echo ""
        echo "Usage: ./scripts.sh <command>"
        echo ""
        echo "Commands:"
        echo "  install      Install production dependencies"
        echo "  install-dev  Install dev dependencies (pytest, ruff)"
        echo "  lock         Generate/update uv.lock"
        echo "  run <cmd>    Run command in virtual environment"
        echo "  test         Run pytest"
        echo "  lint         Run ruff linter"
        echo "  format       Format code with ruff"
        echo "  server       Start uvicorn dev server"
        echo "  shell        Activate virtual environment"
        echo "  upgrade      Upgrade all dependencies"
        echo "  clean        Clean caches"
        ;;
esac
