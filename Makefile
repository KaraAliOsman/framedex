.PHONY: test lint typecheck goldgen dod gauntlet shot-% help

help:
	@echo "Dekopen Builder Command Center (2026 Cross-Platform Gauntlet)"
	@echo "  make dod        - Fast Definition of Done validation (Rule 19)"
	@echo "  make gauntlet   - Complete 6-phase Adversarial Gauntlet execution"
	@echo "  make test       - Run all test suites (engine, backend, frontend)"
	@echo "  make lint       - Run linters and constitutional anti-pattern guards"
	@echo "  make typecheck  - Strict type checking (mypy strict + tsc)"
	@echo "  make goldgen    - Regenerate engine golden snapshots (Rule 22)"
	@echo "  make shot-XX    - Initialize shot branch and plan (e.g. make shot-01)"

test:
	python scripts/check_dod.py test

lint:
	python scripts/check_dod.py lint

typecheck:
	python scripts/check_dod.py typecheck

goldgen:
	python -m engine.scripts.regenerate_golden

dod:
	python scripts/check_dod.py all

gauntlet:
	python scripts/check_dod.py gauntlet

shot-%:
	python scripts/new_shot.py SHOT-$*
	git checkout -b shot-$* 2>/dev/null || git checkout shot-$*
