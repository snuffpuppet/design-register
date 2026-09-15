FROM python:3.12-slim
RUN apt-get update -qq && apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY server.py model.py baseline.py pull-page.py integrity.py items.py views.py renumber.py push-pages.py ./
COPY static ./static
EXPOSE 8080
# The engagement folder is bind-mounted at /engagement by docker compose or run.sh.
CMD ["python", "server.py", "/engagement", "8080"]
