# Development Guidelines

- [Getting the Source](#get)
- [Setting up a New Development Environment](#setup)
- [Development](#dev)
- [Testing](#test)
- [Contributing](#contributing)

## <a name="get"></a> Getting the Source

<!-- markdown-link-check-disable -->

1. Fork the [repository](https://github.com/fetchai/uAgents.git).
2. Clone your fork of the repository:
    <!-- markdown-link-check-enable -->

   ```shell
   git clone https://github.com/fetchai/uAgents.git
   ```

3. Define an `upstream` remote pointing back to the main uAgents repository:

   ```shell
   git remote add upstream https://github.com/fetchai/uAgents.git
   ```

## <a name="setup"></a> Setting up a New Development Environment

The easiest way to get set up for development is to install Python (`3.9` to `3.12`) and [poetry](https://pypi.org/project/poetry/), and then run the following from the top-level project directory:

```bash
  cd python
  poetry install
  poetry shell
  pre-commit install
```

## <a name="dev"></a>Development

When developing for `uAgents` make sure to have the poetry shell active. This ensures that linting and formatting will automatically be checked during `git commit`.

We are using [Ruff](https://github.com/astral-sh/ruff) with added rules for formatting and linting.
Please consider adding `ruff` to your IDE to speed up the development process and ensure you only commit clean code.

Alternately you can invoke ruff by typing the following from within the `./python` folder

```bash
  ruff check --fix && ruff format
```

## <a name="test"></a>Testing

To run tests use the following command:

```bash
  pytest
```

## <a name="contributing"></a>Contributing

<!-- markdown-link-check-disable -->

For instructions on how to contribute to the project (e.g. creating Pull Requests, commit message convention, etc), see the [contributing guide](CONTRIBUTING.md).

<!-- markdown-link-check-enable -->
