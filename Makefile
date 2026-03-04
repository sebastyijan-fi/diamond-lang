PYTHON ?= python3
SHELL := /bin/bash

.PHONY: help v1-gates format lint release

help:
	@echo "Diamond make targets"
	@echo "  v1-gates   Run full V1 gate validation"
	@echo "  format     Apply code formatting helper"
	@echo "  lint       Run project lint-style checks"

v1-gates:
	@$(SHELL) -lc "./scripts/ci/validate_v1_gates.sh"

format:
	@$(PYTHON) format.py

lint:
	@$(PYTHON) format.py

release:
	@echo "See RELEASE.md and CHANGELOG.md"
	@cat RELEASE.md
