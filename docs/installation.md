# Installation

## System requirements

The system requirements for the Python μAgents package are as follows, but libraries for more platforms and languages will be released soon.

!!! Info "System requirements"
    The Python μAgents pacakge runs on `Ubuntu/Debian`, `MacOS`, and `Windows`.
    
    You need <a href="https://www.python.org/downloads/" target="_blank">Python</a> 3.8, 3.9 or 3.10 on your system.

## Install from PyPI

!!! Info "We recommend first creating a clean Python virtual environment, for example using [poetry](https://python-poetry.org/docs/) or [pipenv](https://pipenv.pypa.io/en/latest/install/)."
    === "poetry"
        Create and enter a new `poetry` virtual environment:
        ``` bash
        poetry init -n && poetry shell
        ```
    === "pipenv"
        Create and enter a new `pipenv` environment:
        ``` bash
        pipenv --python 3.10 && pipenv shell
        ```

Now install μAgents from the PyPI package registry:
``` bash
pip install uagents
```

??? note "Alternatively, install from source code:"

    Download the latest released version from Github and navigate to the uAgents directory

    ```
    git clone https://github.com/fetchai/uAgents.git
    cd uAgents
    ```

    Install the required dependencies

    ```
    poetry install
    ```

    Open the virtual environment

    ```
    poetry shell
    ```
