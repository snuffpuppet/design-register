# Register console. Everything runs in Docker through docker compose; the only host tools used are make,
# docker, git and python3 for the sample generator, which writes files and runs no server.
#
#   make sample        write the sample engagement to test-data/puppy-gloves (resets it)
#   make build         build the image, letting Docker resolve what has changed
#   make rebuild       build the image from scratch, no layer cache
#   make up            build the image and run the console on http://localhost:$(PORT)/
#   make down          stop the console
#   make restart       down, then up
#   make reload        restart the server process after a python change (no rebuild)
#   make logs          follow the container log
#   make shell         a shell inside the running container
#   make clean         stop the console, remove the image, and delete generated data
#   make anonymise     deterministic fixture export using a private glossary (docs/anonymisation.md)
#   make push-pages    build the Confluence push files for an engagement into <ENG>/push/ (sends nothing)
#   make test          build and run the console unit tests in Docker
#
# Point the console at another engagement:  make up ENG=engagements/acme
# Serve it somewhere else:                  make up PORT=8090
# Anonymise somewhere other than test:      make anonymise DEST=engagements/demo

DOCKER_HOST := unix://$(HOME)/.docker/run/docker.sock
export DOCKER_HOST

IMAGE   ?= register-console
NAME    ?= register-console
PORT    ?= 8085
# Whatever is already pinned wins, so a bare "make up" brings back the engagement being worked on
# rather than silently resetting a live session to the sample. Pass ENG= to change it deliberately.
PINNED  := $(shell sed -n 's|.*- "\(.*\):/engagement"|\1|p' docker-compose.override.yaml 2>/dev/null)
ENG     ?= $(if $(PINNED),$(PINNED),test-data/puppy-gloves)
ENG_ABS := $(abspath $(ENG))
export IMAGE NAME PORT ENG_ABS

COMPOSE := docker compose

.PHONY: help build rebuild up down restart reload logs shell status sample clean env anonymise push-pages test acceptance

help:
	@sed -n '2,20p' Makefile | sed 's/^# \{0,1\}//'

# Compose merges docker-compose.override.yaml on every invocation, including when Docker recreates a
# container by itself. Writing the engagement there rather than passing it through this make process's
# environment is what stops a recreated container falling back to the sample.
env:
	@test -d "$(ENG_ABS)" || { echo "no engagement at $(ENG); run 'make sample' or /import-confluence <name>"; exit 1; }
	@printf '# written by "make up"; the engagement and port the console is pinned to.\n# console/ is mounted over /app so an edit to the server or the page needs no image rebuild:\n# static files are picked up on a browser reload, python changes by "make reload".\nservices:\n  console:\n    ports:\n      - "%s:8080"\n    volumes:\n      - "%s:/engagement"\n      - "%s/console:/app"\n' '$(PORT)' '$(ENG_ABS)' '$(CURDIR)' > docker-compose.override.yaml
	@echo "pinned: $(ENG) on port $(PORT)"

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) build --no-cache

up: build env
	$(COMPOSE) up -d
	@echo "console: http://localhost:$(PORT)/  (engagement $(ENG))"

down:
	$(COMPOSE) down

restart: down up

# python changed: restart the process. Static files need nothing but a browser reload.
reload:
	$(COMPOSE) restart console
	@echo "console restarted on http://localhost:$(PORT)/"

logs:
	$(COMPOSE) logs -f console

shell:
	$(COMPOSE) exec console sh

status:
	@$(COMPOSE) ps --format '{{.Name}}  {{.Status}}  {{.Ports}}' | grep . || echo "$(NAME) is not running"

sample:
	python3 console/make-sample.py

# Unit tests for the console, run in the official python image. No host python. Renumber's tests
# shell out to git, so the image needs it installed first.
test: build
	docker run --rm -v "$(CURDIR)/console:/app" -w /app $(IMAGE) python -W ignore::ResourceWarning -m unittest discover -s tests -v

# Deterministic export; the private glossary stays with the source on the work laptop.
SRCENG ?= engagements/abb-nokia
DEST   ?= /tmp/register-anonymised
GLOSSARY ?= $(SRCENG)/anonymise/glossary.json

anonymise: build
	@test -f "$(GLOSSARY)" || { echo "Set GLOSSARY to the private replacements JSON on the work laptop."; exit 1; }
	@test -d "$(dir $(DEST))" || { echo "Create the destination parent folder first."; exit 1; }
	docker run --rm -v "$(abspath $(SRCENG)):/source:ro" -v "$(abspath $(GLOSSARY)):/private-glossary.json:ro" -v "$(abspath $(dir $(DEST))):/output" $(IMAGE) python /app/anonymise.py /source "/output/$(notdir $(DEST))" --glossary /private-glossary.json

acceptance: test
	@echo "Container tests passed. Follow docs/work-laptop-acceptance.md for browser checks."

# Preview is read-only. Apply requires the preview token and operator, with other writers stopped.
export EXPECT MADE_BY
.PHONY: proposal-check proposal-migrate proposal-recover
proposal-check: build
	docker run --rm -v "$(ENG_ABS):/engagement:ro" $(IMAGE) python /app/proposal_upgrade.py /engagement

proposal-migrate: build
	docker run --rm -e EXPECT -e MADE_BY -v "$(ENG_ABS):/engagement" $(IMAGE) python /app/proposal_upgrade.py /engagement --apply

proposal-recover: build
	docker run --rm -v "$(ENG_ABS):/engagement" $(IMAGE) python /app/proposal_upgrade.py /engagement --recover

clean:
	$(COMPOSE) down --rmi local --remove-orphans
	rm -rf test-data/puppy-gloves
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	@echo "cleaned; 'make sample' regenerates the test data"

# Build what /push-confluence will send: one storage-format body per register page, plus a manifest.
# Refuses any engagement but the one named in confluence.json push.engagement.
push-pages: build
	docker run --rm -v "$(CURDIR):/work" -w /work $(IMAGE) python /app/push-pages.py $(ENG)
