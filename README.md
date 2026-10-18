# crag-radar-back

Backend of Crag Radar. The code runs inside a Docker container, so you only need Docker
on the host. The `stack` script wraps every Docker command used during development.

## Requirements

- **Docker** with BuildKit enabled. BuildKit is the default since Docker 23. The
  `Dockerfile` uses `RUN --mount=type=cache` and does not build without it.
- **Bash**, to run the `stack` script.
- **uv** (optional), only to work outside the container or to serve the docs locally.

You do not need Python on the host. The image installs Python and all dependencies with
`uv` from `uv.lock`.

### Configuration

| File | Purpose |
| --- | --- |
| `.stack` | `PYTHON_IMAGE_VERSION` (Python of the image), `IMAGE_NAME`, `CONTAINER_NAME`, `EXPOSED_PORT`, `CONTAINER_PORT`. |
| `deployments/config-<target>.env` | Environment variables passed to the container. `./stack up` requires the file of the chosen target to exist, even if empty. `local` is used for development and `ci` by the pipeline. |

The code supports Python 3.10 to 3.14. To build with another Python version, change
`PYTHON_IMAGE_VERSION` in `.stack`, or set it for a single build:

```bash
PYTHON_IMAGE_VERSION=3.12 ./stack build
```

## Build

```bash
./stack build          # dev image: runtime and development dependencies
./stack build common   # runtime dependencies only
```

The `Dockerfile` has two stages:

- `common` installs the package and its runtime dependencies into `/app/.venv`.
- `dev` adds the development and documentation tools: pytest, ruff, mypy and MkDocs.

## Deploy

```bash
./stack up             # start the container with deployments/config-local.env
./stack up <target>    # start it with deployments/config-<target>.env
./stack down           # remove the container
```

`./stack up` mounts the project folder at `/app`, so code changes are visible in the
container without rebuilding. The virtual environment stays the one built in the image.
Rebuild the image after changing dependencies in `pyproject.toml`.

## Run tests and checks

The container must be running (`./stack up`). Extra arguments are passed to each tool.

```bash
./stack test                         # all tests
./stack test test/racker -k register # a subset, with any pytest options
./stack ruff src test                # lint and fix
./stack format src test              # format
./stack mypy src                     # type check (strict)
./stack docs                         # build the documentation
./stack exec                         # open a shell in the container
./stack run "<command>"              # run any command in the container
./stack lock                         # update uv.lock
```

Run `./stack help` to list every command.

## Documentation

The docs are built with MkDocs. The API reference is generated from the docstrings in
`src/`. The `dev` image includes the docs tools.

```bash
./stack docs                               # mkdocs build --strict, into site/
./stack run "mkdocs serve -a 0.0.0.0:80"   # serve at http://localhost:<EXPOSED_PORT>
```

The serve command assumes `CONTAINER_PORT=80`, as set in `.stack`. With uv on the host,
`uv run --group docs mkdocs serve` serves the docs at http://127.0.0.1:8000.

## Continuous integration

`.github/workflows/ci.yml` runs on every push to `main` and on every pull request. It
uses the same `stack` commands as development, with the `ci` deployment target. All
settings come from `.stack` and `deployments/config-ci.env`, except the Python version.

- **Tests:** for each Python version from 3.10 to 3.14, runs
  `PYTHON_IMAGE_VERSION=<version> ./stack build`, then `./stack up ci` and `./stack test`.
  Python 3.15 also runs, but is allowed to fail: some locked dependencies don't have
  Python 3.15 builds yet.
- **Docs:** runs `./stack build`, `./stack up ci` and `./stack docs` with the Python version
  from `.stack`. The docs are built with `--strict`, so a broken link or docstring fails
  the job.

Both jobs remove the container with `./stack down` at the end, even when a step fails.

## The `racker` module

`racker` links classes to the pydantic models that configure them. You can then build
an object from a plain dictionary, such as one loaded from JSON or YAML, without knowing
its class in advance. The `"type"` field of the dictionary selects the class.

```python
from pydantic import BaseModel

from racker.registry import Registry


class Storage:
    """Base class of every storage."""


class LocalStorageConfig(BaseModel):
    type: str = "local"
    root: str


class LocalStorage(Storage):
    def __init__(self, config: LocalStorageConfig) -> None:
        self.root: str = config.root


registry: Registry = Registry()
registry.add_base(base_class=Storage)
registry.register(class_=LocalStorage, config_class=LocalStorageConfig, base_class=Storage)

storage: Storage = registry.instantiate_from_dict(
    base_class=Storage,
    config_dict={"type": "local", "root": "/data"},
)
```

It has three classes:

- **`Entry`** links a class, its base class and its config class. It checks that the
  class derives from the base class, and that the config class has a `type` field with a
  fixed default value.
- **`RegistryBase`** holds the entries of one base class. Each class has exactly one
  config class, each config class has exactly one class, and no two config classes share
  a `type` value. It turns a dictionary into the matching config object.
- **`Registry`** holds one `RegistryBase` per base class. It registers classes, looks up a
  class from its config class and back, and builds objects from dictionaries.

Each `Registry` instance is independent, and every lookup is fully typed. See the
**Racker** tab of the documentation for the full explanation and the **API reference**
tab for every class and method.

## Project layout

```text
src/
  racker/      class/config registry described above
test/          tests, mirroring src/
docs/          MkDocs sources
deployments/   container environment per deployment target (local, ci)
old/, tmp/     earlier and scratch code, not part of the package
```
