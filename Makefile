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
#   make anonymise     write a shareable copy of an engagement (see engagements/abb-nokia/anonymise)
#   make push-pages    build the Confluence push files for a frozen engagement into <ENG>/push/ (sends nothing)
#   make test          run the console's unit tests inside the python image
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

.PHONY: help build rebuild up down restart reload logs shell status sample clean env anonymise push-pages test

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

# Unit tests for the console, run in the official python image. No host python.
test:
	docker run --rm -v "$(CURDIR)/console:/app" -w /app python:3.12-slim python -m unittest discover -s tests -v

# A shareable copy of an engagement: every company, person, product and technical term
# replaced by a haberdashery one, and the baseline verdicts re-keyed onto it. The tool and
# its glossary live in the source engagement; see engagements/abb-nokia/anonymise/README.md.
SRCENG ?= engagements/abb-nokia
DEST   ?= engagements/test

anonymise: build
	@test -d "$(SRCENG)/anonymise" || { echo "no anonymise tool in $(SRCENG)"; exit 1; }
	rm -rf "$(DEST)"
	$(COMPOSE) run --rm --no-deps -v "$(CURDIR):/repo" -w /repo --entrypoint sh console -c \
	  'python3 /repo/$(SRCENG)/anonymise/translate.py /repo/$(DEST) && python3 /repo/$(SRCENG)/anonymise/verdicts.py /repo/$(DEST)'
	@echo "anonymised $(SRCENG) -> $(DEST); serve it with 'make up ENG=$(DEST)'"

clean:
	$(COMPOSE) down --rmi local --remove-orphans
	rm -rf test-data/puppy-gloves
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	@echo "cleaned; 'make sample' regenerates the test data"

# Build what /push-confluence will send: one storage-format body per register page, plus a manifest.
# Refuses any engagement but the one named in confluence.json push.engagement.
push-pages: build
	docker run --rm -v "$(CURDIR):/work" -w /work $(IMAGE) python /app/push-pages.py $(ENG)
