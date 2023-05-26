<!--
Copyright (c) 2022, Oracle and/or its affiliates.

Licensed under the Universal Permissive License v 1.0 as shown at
http://oss.oracle.com/licenses/upl.
 -->

# Developing Coherence Python Client

### Pre-Requisites
* Use `bash` shell
* [pyenv](https://github.com/pyenv/pyenv) version 2.3.x or later
* [poetry](https://github.com/python-poetry/poetry) version 1.5.x or later

### Project Structure
* `bin` - various shell scripts
* `etc` - contains the ProtoBuff .protoc files and other various files
* `coherence` - Python source files and related resources
* `tests` - contains the library test cases in plain Python

### Setup working environment
1. Install Python version 3.11.3

    ```pyenv install 3.11.3```

2. Checkout the source from GitHub and change directory to the project root dir

3. Set pyenv local version for this project to  3.11.3

    ```pyenv local  3.11.3```
4. Set poetry to use python  3.11.3

    ```poetry env use 3.11.3```
5. Install all the required dependencies using poetry

    ```poetry install```
6. For setting up IntelliJ IDE, install the Python and PyEnv plugins
7. Get the full path of the poetry/python virtualenv

    ```poetry env list --full-path```
8. Use the path above to setup the project settings in IntelliJ IDE. See [this](https://www.jetbrains.com/help/idea/creating-virtual-environment.html)

    Use the *Existing Environment* option to use the path above

**Note:** Incase one needs to re-generate the sources from .proto files, make sure steps 1-5 are done.
Run the Makefile in the virtualenv shell:
```
poetry shell
make generate-proto
```
