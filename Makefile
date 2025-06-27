# Chrome DevTools MCP - Build Automation

.PHONY: install test lint format clean build package check dev help

# Default target
help:
	@echo "Chrome DevTools MCP - Build Commands"
	@echo ""
	@echo "Development:"
	@echo "  install    Install dependencies with uv"
	@echo "  dev        Install in development mode"
	@echo "  test       Run full test suite"
	@echo "  test-quick Run quick smoke tests"
	@echo "  test-dom   Run DOM manipulation tests"
	@echo "  test-console Run console and JavaScript tests"
	@echo "  test-network Run network monitoring tests"
	@echo "  lint       Run linting checks"
	@echo "  format     Format code with ruff"
	@echo "  check      Run all checks (lint + type check + test)"
	@echo ""
	@echo "Distribution:"
	@echo "  package    Build DXT extension package"
	@echo "  clean      Remove build artifacts"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci-test    Run full CI test suite"

# Development setup
install:
	uv sync

dev: install
	uv run mcp install server.py -n "Chrome DevTools MCP" --with-editable .

# Code quality
lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src/

# Testing
test:
	uv run python -m pytest test_devtools_server.py -v

test-quick:
	uv run python -m pytest test_devtools_server.py::test_chrome_detection test_devtools_server.py::test_javascript_execution -v

test-dom:
	uv run python -m pytest test_devtools_server.py -k "test_get_document or test_query_selector or test_element" -v

test-console:
	uv run python -m pytest test_devtools_server.py -k "test_javascript or test_console" -v

test-network:
	uv run python -m pytest test_devtools_server.py -k "test_network" -v

# All checks
check: lint typecheck test

# CI test suite
ci-test: install check

# Packaging
package: clean
	@echo "Building DXT extension package..."
	@VERSION=$$(jq -r '.version' manifest.json) && \
	npx @anthropic-ai/dxt pack . chrome-devtools-protocol-$$VERSION.dxt && \
	echo "✅ Extension packaged: chrome-devtools-protocol-$$VERSION.dxt"

# Cleanup
clean:
	rm -f chrome-devtools-protocol-*.dxt
	rm -rf .ruff_cache/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf src/tools/__pycache__/
	rm -rf .pytest_cache/
	rm -rf chrome_devtools_mcp.egg-info/

# Installation helpers
install-tools:
	npm install -g @anthropic-ai/dxt
	pip install uv

# Development server (for testing)
dev-server:
	uv run python server.py

# Version management
version-patch:
	@echo "Current version: $$(jq -r '.version' manifest.json)"
	@echo "Bumping patch version..."
	@jq '.version = (.version | split(".") | .[0] + "." + .[1] + "." + (.[2] | tonumber + 1 | tostring))' manifest.json > manifest.tmp && mv manifest.tmp manifest.json
	@echo "New version: $$(jq -r '.version' manifest.json)"

version-minor:
	@echo "Current version: $$(jq -r '.version' manifest.json)"
	@echo "Bumping minor version..."
	@jq '.version = (.version | split(".") | .[0] + "." + (.[1] | tonumber + 1 | tostring) + ".0")' manifest.json > manifest.tmp && mv manifest.tmp manifest.json
	@echo "New version: $$(jq -r '.version' manifest.json)"

# Quick development workflow
quick-build: format lint package
	@echo "✅ Quick build complete!"

# Full release workflow  
release: clean check package
	@echo "✅ Release build complete!"
	@echo "📦 Extension: chrome-devtools-protocol-*.dxt"
	@echo ""
	@echo "To release:"
	@echo "1. git tag v$$(jq -r '.version' manifest.json)"
	@echo "2. git push origin v$$(jq -r '.version' manifest.json)"