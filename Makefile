SOURCES  ?= analytics-api-docs
SPECS    ?= $(SOURCES)/zenesis-oas
DIST     ?= dist
OVERLAYS ?= overlays
RULES    ?= rules.json
PY       ?= python3
CLI       = $(PY) -m zenesis_oas --rules $(RULES)

.PHONY: help sources update-sources inventory convert overlays verify test check clean

help:
	@echo "make sources         fetch the analytics-api-docs submodule at the pinned commit"
	@echo "make update-sources  move the pin to the tip of analytics-api-docs main"
	@echo "make inventory  list vendor extensions in $(SPECS)/ without converting"
	@echo "make convert    write clean OpenAPI to $(DIST)/"
	@echo "make overlays   regenerate the Overlay 1.0.0 documents in $(OVERLAYS)/"
	@echo "make verify     prove the conversion is lossless"
	@echo "make test       run the unit tests"
	@echo "make check      inventory + verify + test    <- what CI runs"
	@echo "make clean      remove $(DIST)/"
	@echo
	@echo "Override any path:  make convert SPECS=path/to/json DIST=out"

# The specs are not stored here. They come from the analytics-api-docs
# repository, included as a git submodule and pinned to one commit, so every
# conversion states which revision of the source it came from. This target
# only fetches when the submodule has not been initialised; it never moves a
# checkout you already have, so it is safe after `make update-sources`.
sources:
	@test -e $(SPECS) || git submodule update --init $(SOURCES)

# Move the pin to the newest commit on analytics-api-docs main. Review with
# `git diff --submodule`, rebuild, and commit the pin with any overlay drift.
update-sources:
	@git submodule update --init --remote --merge $(SOURCES)
	@git diff --submodule -- $(SOURCES)

# Run this first after moving the pin. Exits non-zero if any vendor key has no
# rule, so you find out before the key is silently dropped.
inventory: sources
	@$(CLI) inventory $(SPECS)

convert: sources
	@$(CLI) convert $(SPECS) $(DIST)

overlays: sources
	@$(CLI) overlay $(SPECS) --out $(OVERLAYS)

# Gate 1: every converted document plus its overlays equals the source exactly.
# Gate 2: no conversion warnings.
verify: sources
	@$(CLI) verify $(SPECS) --overlays $(OVERLAYS)

test:
	@$(PY) -m unittest discover -s tests

check: inventory test verify
	@echo
	@echo "All checks passed. Publish: $(DIST)/"

clean:
	@rm -rf $(DIST)
