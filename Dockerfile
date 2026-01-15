FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y gcc libffi-dev libpq-dev curl
# Install IonScale CLI
RUN curl -L -o ionscale https://github.com/jsiebens/ionscale/releases/download/v0.18.0/ionscale_linux_amd64
RUN chmod +x ionscale
RUN mv ionscale /usr/local/bin
# Install App
RUN mkdir /workspace
ADD . /workspace
WORKDIR /workspace
RUN uv sync


