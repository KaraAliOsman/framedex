.PHONY: test lint typecheck build database goldgen dod gauntlet shot-% help

help:
	@echo "Dekopen Builder Command Center (2026 Canonical Verification)"
	@echo "  make dod        - Canonical full Definition of Done (Rule 19)"
	@echo "  make gauntlet   - Compatibility alias for make dod; same evidence, never run both"
	@echo "  make test       - Run all test suites (engine, backend, frontend)"
	@echo "  make lint       - Run linters and constitutional anti-pattern guards"
	@echo "  make typecheck  - Strict type checking (mypy strict + tsc)"
	@echo "  make build      - Build the production frontend"
	@echo "  make database   - Run the live Supabase reset/lint/pgTAP gate"
	@echo "  make goldgen    - Regenerate engine golden snapshots (Rule 22)"
	@echo "  make shot-XX    - Initialize shot branch and plan (e.g. make shot-01)"

test:
	python scripts/check_dod.py test

lint:
	python scripts/check_dod.py lint

typecheck:
	python scripts/check_dod.py typecheck

build:
	python scripts/check_dod.py build

database:
	python scripts/check_dod.py database

goldgen:
	python -m engine.scripts.regenerate_golden

dod:
	python scripts/check_dod.py all

gauntlet:
	@echo "Compatibility alias: make gauntlet == make dod; do not run both."
	$(MAKE) dod

shot-%:
	python scripts/new_shot.py SHOT-$*
	git checkout -b shot-$* 2>/dev/null || git checkout shot-$*
