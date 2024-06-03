# Development Guidelines

- [Getting the Source](#get)
- [Setting up a New Development Environment](#setup)
- [Development](#dev)
  - [General code quality checks](#devsetup)
  - [General code quality checks](#devcommands)
  - [General code quality checks](#testing)
  - [General code quality checks](#general)
  - [Updating documentation](#docs)
  - [Updating API documentation](#api)
  - [Updating dependencies](#deps)
  - [Tests](#tests)
  - [Miscellaneous checks](#misc)
- [Contributing](#contributing)

## <a name="get"></a> Getting the Source

<!-- markdown-link-check-disable -->
1. Fork the [repository](https://github.com/fetchai/uAgents.git).
2. Clone your fork of the repository:
    <!-- markdown-link-check-enable -->

   ``` shell
   git clone https://github.com/fetchai/uAgents.git
   ```

3. Define an `upstream` remote pointing back to the main uAgents repository:

   ``` shell
   git remote add upstream https://github.com/fetchai/uAgents.git
   ```

## <a name="setup"></a> Setting up a New Development Environment

1. Ensure you have Python (version `3.8`, `3.9`, `3.10` or `3.11`) and [`poetry`][poetry].

2. ``` shell
   make new-env
   ```

   This will create a new virtual environment using poetry with the project and all the development dependencies installed.

   > We use <a href="https://python-poetry.org" target="_blank">poetry</a> to manage dependencies. All python specific dependencies are specified in `pyproject.toml` and installed with the library. 
   > 
   > You can have more control on the installed dependencies by leveraging poetry's features.

3. ``` shell
   poetry shell
   ```

    To enter the virtual environment.

## <a name="dev"></a>Development

### <a name="devsetup"></a>Development setup

The easiest way to get set up for development is to install Python (`3.9` to `3.12`) and [poetry](https://pypi.org/project/poetry/), and then run the following from the top-level project directory:

```bash
  cd python
  poetry install
  poetry shell
  pre-commit install
```

### <a name="devcommands"></a>Development commands

When developing for `uAgents` make sure to have the poetry shell active. This ensures that linting and formatting will automatically be checked during `git commit`.

We are using [Ruff](https://github.com/astral-sh/ruff) with added rules for formatting and linting.
Please consider adding `ruff` to your IDE to speed up the development process and ensure you only commit clean code.

Alternately you can invoke ruff by typing the following from within the `./python` folder

```bash
  ruff check --fix && ruff format
```

### <a name="testing"></a> Testing

To run tests use the following command:

```bash
  pytest
```

### <a name="general"></a>General code quality checks

To run general code quality checkers, formatters and linters:

- ``` shell
   make lint
  ```

  Automatically formats your code and sorts your imports, checks your code's quality and scans for any unused code.

- ``` shell
   make mypy
  ```

  Statically checks the correctness of the types.

- ``` shell
   make pylint
  ```

  Analyses the quality of your code.

- ``` shell
   make security
  ```

  Checks the code for known vulnerabilities and common security issues.

- ``` shell
   make clean
  ```

  Cleans your development environment and deletes temporary files and directories.

### <a name="docs"></a>Updating documentation

We use [`mkdocs`][mkdocs] and [`material-for-mkdocs`][material] for static documentation pages. To make changes to the documentation:

- ``` shell
   make docs-live
  ```
  <!-- markdown-link-check-disable -->
  This starts a live-reloading docs server on localhost which you can access by going to <http://127.0.0.1:8000/> in your browser. Making changes to the documentation automatically reloads this page, showing you the latest changes.
  <!-- markdown-link-check-enable -->
  To create a new documentation page, add a markdown file under `/docs/` and add a reference to this page in `mkdocs.yml` under `nav`.

### <a name="api"></a>Updating API documentation

If you've made changes to the core `uagents` package that affects the public API:

- ``` shell
   make generate-api-docs
  ```

  This regenerates the API docs. If pages are added/deleted, or there are changes in their structure, these need to be reflected manually in the `nav` section of `mkdocs.yaml`.

### <a name="deps"></a>Updating dependencies

We use [`poetry`][poetry] and `pyproject.toml` to manage the project's dependencies.

If you've made any changes to the dependencies (e.g. added/removed dependencies, or updated package version requirements):

- ``` shell
   poetry lock
  ```

  This re-locks the dependencies. Ensure that the `poetry.lock` file is pushed into the repository (by default it is).

  Note: Whenever the lock file is updated, you need to make sure the version of `tox` installed in the CI workflows matches the version in `poetry.lock`.

- ``` shell
   make liccheck
  ```

  Checks that the licence for the library is correct, taking into account the licences for all dependencies, their dependencies and so forth.

### <a name="tests"></a>Tests

To test the project, we use `pytest`. To run the tests:

- ``` shell
   make test
  ```

  Runs all the tests.

- ``` shell
   make unit-test
   ```

  Runs all unit tests.

- ``` shell
   make integration-test
  ```

  Runs all integration tests.

- ``` shell
   make coverage-report
  ```

  Produces a coverage report (you should run tests using one of the above commands first).

### <a name="misc"></a>Miscellaneous checks

- ``` shell
   make copyright-check
  ```

  Checks that all files have the correct copyright header (where applicable).

## <a name="contributing"></a>Contributing

<!-- markdown-link-check-disable -->
For instructions on how to contribute to the project (e.g. creating Pull Requests, commit message convention), see the [contributing guide](CONTRIBUTING.md).
<!-- markdown-link-check-enable -->

[mkdocs]: https://www.mkdocs.org
[material]: https://squidfunk.github.io/mkdocs-material/
[poetry]: https://python-poetry.org
[contributing guide]: https://github.com/fetchai/uAgents/blob/main/CONTRIBUTING.md
[repo]: https://github.com/fetchai/uAgents
