# CPU image for the deterministic half of the pipeline: geometry, score,
# rank, biophys, evaluate, analyze and report. The generative and folding
# stages (RFdiffusion, ProteinMPNN, ESMFold2, Protenix, Boltz,
# AF2-initial-guess) need GPUs and large weights; they run in their own
# containers and are reached through adapters, so this image stays small and
# reproducible. See DESIGN.md section 1.

FROM python:3.12-slim-bookworm AS build

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies resolve from the lockfile alone, so this layer is cached
# until the lockfile actually changes.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev


FROM python:3.12-slim-bookworm AS runtime

# A pinned, unprivileged user keeps committed results owned predictably
# when the campaign tree is bind-mounted.
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid 1000 --create-home app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=build --chown=app:app /app/.venv /app/.venv

USER app
WORKDIR /work

ENTRYPOINT ["counterscreen"]
CMD ["--help"]
