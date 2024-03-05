## Development setup

The easiest way to get set up for development is to install Python (`3.9` to `3.12`) and [poetry](https://pypi.org/project/poetry/), and then run the following from the top-level project directory:

```bash
  cd python
  poetry install
  poetry shell
  pre-commit install
```

## Development commands

When developing for `uAgents` make sure to have the poetry shell active. This ensures that linting and formatting will automatically be checked during `git commit`.

We are using [Ruff](https://github.com/astral-sh/ruff) with added rules for formatting and linting.
Please consider adding `ruff` to your IDE to speed up the development process and ensure you only commit clean code.

Alternately you can invoke ruff by typing the following from within the `./python` folder

```bash
  ruff check --fix && ruff format
```

### Testing

To run tests use the following command:

```bash
  pytest
```
