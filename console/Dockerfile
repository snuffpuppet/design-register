FROM python:3.12-slim
WORKDIR /app
COPY server.py model.py baseline.py ./
COPY static ./static
EXPOSE 8080
# The engagement folder is bind-mounted at /engagement by docker compose or run.sh.
CMD ["python", "server.py", "/engagement", "8080"]
