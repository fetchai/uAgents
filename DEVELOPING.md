## Development setup

The easiest way to get set up for development is to install Python (`3.8`, `3.9`, or `3.10`) and [poetry](https://pypi.org/project/poetry/), and then run the following from the top-level project directory:

```bash
  poetry install
  poetry shell
```

## Development commands

Following are some helpful commands for development:

- To run the code formatter:

  ```bash
    black .
  ```

- To run lint checks:

  ```bash
    pylint $(git ls-files '*.py')
  ```

- To run tests:

  ```bash
    pytest
  ```

Before committing and opening a PR, use the above commands to run the checks locally. This saves CI hours and ensures you only commit clean code.