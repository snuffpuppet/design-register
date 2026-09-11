# Register console. Everything runs in Docker; the only host tools used are make, docker, git and python3
# for the sample generator, which writes files and runs no server.
#
#   make sample        write the sample engagement to test-data/puppy-gloves (resets it)
#   make up            build the image and run the console on http://localhost:$(PORT)/
#   make down          stop the console
#   make restart       down, then up
#   make logs          follow the container log
#   make shell         a shell inside the running container
#   make clean         stop the console, remove the image, and delete generated data
#
# Point the console at another engagement:  make up ENG=engagements/acme

IMAGE   ?= register-console
NAME    ?= register-console
PORT    ?= 8080
ENG     ?= test-data/puppy-gloves
ENG_ABS := $(abspath $(ENG))

.PHONY: help build up down restart logs shell status sample clean

help:
	@sed -n '2,13p' Makefile | sed 's/^# \{0,1\}//'

build:
	docker build -q -t $(IMAGE) console

up: build
	@docker rm -f $(NAME) >/dev/null 2>&1 || true
	@test -d "$(ENG_ABS)" || { echo "no engagement at $(ENG); run 'make sample' or /import-confluence <name>"; exit 1; }
	docker run -d --rm --name $(NAME) -p $(PORT):8080 -v "$(ENG_ABS):/engagement" $(IMAGE)
	@echo "console: http://localhost:$(PORT)/  (engagement $(ENG))"

down:
	@docker rm -f $(NAME) >/dev/null 2>&1 && echo "stopped $(NAME)" || echo "$(NAME) was not running"

restart: down up

logs:
	docker logs -f $(NAME)

shell:
	docker exec -it $(NAME) sh

status:
	@docker ps --filter name=$(NAME) --format '{{.Names}}  {{.Status}}  {{.Ports}}' | grep . || echo "$(NAME) is not running"

sample:
	python3 console/make-sample.py

clean: down
	@docker rmi $(IMAGE) >/dev/null 2>&1 && echo "removed image $(IMAGE)" || true
	rm -rf test-data/puppy-gloves
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	@echo "cleaned; 'make sample' regenerates the test data"
