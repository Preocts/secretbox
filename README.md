# secretbox

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/python-template/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/python-template/main)

A library that offers a simple method of loading and accessing environmental variables, `.env` file values, and other sources of secrets. The class stores values to state when load methods are called.

Loaded values are also injected into the local environ. This is to assist with adjacent libraries that reference `os.environ` values by default. Required values can be kept in a `.env` file instead of managing a script to load them into the environment.

### Requirements
- Python >= 3.6 <= 3.9

### Optional Dependencies
- boto3
- boto3-stubs[secretsmanager]

---

## Example use

```python
from secretbox.loadenv import LoadEnv

secrets = LoadEnv()


def main() -> int:
    """Main function"""
    secrets.load()

    my_sevice_password = secrets.get("SERVICE_PW")
    # More code

    return 0


if __name__ == "__main__":
    exit(main())
```

## LoadEnv arguments:

**Default:** (shown above)
- On initialization the `LoadEnv()` class does nothing. By calling `.load()` we cause the class to load all the currently available environ variables. It also looks for and loads, if found, a `.env` file in the working directory. From there we can access those values with `.get("KEY_NAME")`.

**auto_load**
- Alternatively, you can initialize with `LoadEnv(auto_load=True)` and the `load()` method will be executed on creation of the class instance.

**filename**
- You can specify a `.env` formatted file and location, overriding the default behavior to load the `.env` from the working directory.

**aws_sstore_name**
- When provided, an attempt to load values from named AWS secrets manager will be made. Requires `aws_region` to be provided. Requires `boto3` and `boto3-stubs[secretsmanager]` to be installed.

**aws_region**
- When provided, an attempt to load values from the given AWS secrets manager found in this region will be made. Requires `aws_sstore_name` to be provided. Requires `boto3` and `boto3-stubs[secretsmanager] to be installed.

## LoadEnv methods:

**.get("[Key Name]")**
- Returns the string value of the loaded value by key name. If the key does not exist, an empty string will be returned `""`.

**.load()**
- Runs all importer methods. If optional dependencies are not installed, e.g. boto3, the importer is skipped.

**.load_env_vars()**
- Loads all existing `os.environ` values into state.

**.load_env_file()**
- Loads `.env` file or any file provided with the `filename` argument on initialization.

**.load_aws_store()**
- Loads secrets from AWS secret manager. Requires `aws_sstore_name` and `aws_region` to have been provided. Will raise `NotImplementedError` if library requirements are missing.

---

## Install

**TODO**

---

## Local developer installation

It is **highly** recommended to use a `venv` for installation. Leveraging a `venv` will ensure the installed dependency files will not impact other python projects.

The instruction below make use of a bash shell and a Makefile.  All commands should be able to be run individually of your shell does not support `make`

Clone this repo and enter root directory of repo:
```bash
$ git clone https://github.com/Preocts/secretbox
$ cd secretbox
```

Create and activate `venv`:
```bash
$ python3 -m venv venv
$ . venv/bin/activate
```

Your command prompt should now have a `(venv)` prefix on it.

Install editable library and development requirements:
```bash
(venv) $ pip install -r requirements-dev.txt
(venv) $ pip install --editable .[aws,tests]
```

Run tests
```bash
(venv) $ tox
```

To exit the `venv`:
```bash
(venv) $ deactivate
```

---

### Makefile

This repo has a Makefile with some quality of life scripts if your system supports `make`.

- `update` : Clean all artifacts, update pip, update requirements, install everything
- `clean-pyc` : Deletes python/mypy artifacts
- `clean-tests` : Deletes tox, coverage, and pytest artifacts
