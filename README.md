# secretbox

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/python-template/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/python-template/main)
[![Python Tests](https://github.com/Preocts/secretbox/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Preocts/secretbox/actions/workflows/python-tests.yml)
[![codecov](https://codecov.io/gh/Preocts/secretbox/branch/main/graph/badge.svg?token=7QFJGMD3JI)](https://codecov.io/gh/Preocts/secretbox)

A library that offers a simple method of loading and accessing environmental variables, `.env` file values, and other sources of secrets. The class stores values to state when load methods are called.

Loaded values are also injected into the local environ. This is to assist with adjacent libraries that reference `os.environ` values by default. Required values can be kept in a `.env` file instead of managing a script to load them into the environment.

---

### Requirements

- Python >=3.7

### Optional Dependencies

- boto3
- boto3-stubs[secretsmanager]
- boto3-stubs[ssm]

---

## Installation

```bash
$ pip install secretbox
```

_Optional AWS support_

```bash
$ pip install secretbox[aws]
```

---

# Documentation:

## Example use with `auto_load=True`

This loads the system environ and the `.env` from the current working directory into the class state for quick reference. Loaded secrets can be accessed from the `.values` property or from other methods such as `os.getenviron()`.

```python
from secretbox import SecretBox

secrets = SecretBox(auto_load=True)


def main() -> int:
    """Main function"""
    my_sevice_password = secrets.values.get("SERVICE_PW")
    # More code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Example use with `use_loaders()`

Loaders collect key:value pair secrets from various sources. When you need more than one source loaded, in a particular order, with a single collection of all loaded values then `.use_loaders()` is the solution. Each loader is executed in turn and the results compiled with the `SecretBox` object.

This loads the system environment variables, an AWS secret store, and then a specific `.env` file if it exists. Secrets are loaded in the order of loaders, replacing any matching keys from the prior loader.

```python
from secretbox import AWSSecretLoader
from secretbox import EnvFileLoader
from secretbox import EnvironLoader
from secretbox import SecretBox

secrets = SecretBox()


def main() -> int:
    """Main function"""
    secrets.use_loaders(
        EnvironLoader(),
        AWSSecretLoader("mySecrets", "us-east-1"),
        EnvFileLoader("sandbox/.override_env"),
    )

    my_sevice_password = secrets.values.get("SERVICE_PW")
    # More code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## Example use with stand-alone loader

Loaders can be used as needed. For this example we only need to load an AWS Parameter store.

```python
from secretbox import AWSParameterStoreLoader

secrets = AWSParameterStoreLoader("mystore/params/", "us-west-2")
secrets.run()


def main() -> int:
    """Main function"""
    my_sevice_password = secrets.values.get("SERVICE_PW")
    # More code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---



### SecretBox arguments:

`SecretBox(*, auto_load: bool = False, load_debug: bool = False)`

**auto_load**

- Loads environment variables and then the .env file from current working directory if found.

**load_debug**

- When true, internal logger level is set to DEBUG. Secret values are truncated, however it is not recommended to leave this on for production deployments.

### SecretBox API:

**.values**

- *Property*: A copy of the `dict[str, str]` key:value pairs loaded

**.use_loaders(\*loaders: Loader) -> None**

- Loaded results are injected into environ and stored in state.

---

**NOTE:** All .get methods pull from the instance state of the class and do not reflect changes to the enviornment post-load.

**.get(key: str, default: str | None = None) -> str**

- Returns the string value of the loaded value by key name. If the key does not exists then `KeyError` will be raised unless a default is given, then that is returned.

**.set(key: str, value: str) -> None**

- Adds the key:value pair to both the secretbox instance and the environment variables

**.get_int(key: str, default: int | None = None) -> int** -- *deprecated*

- Returns the int value of the loaded value by key name. Raise `ValueError` if the found key cannot convert to `int`. Raise `KeyError` if the key is not found and no default is given.

**.get_list(key: str, delimiter: str = ",", default: list[str] | None = None) -> List[str]:** -- *deprecated*

- Returns a list of the loaded value by key name, seperated at defined delimiter. No check is made if delimiter exists in value. `default` is returned if key is not found otherwise a `KeyError` is raised.

**.load_from(loaders: list[str], \*\*kwargs: Any) -> None** -- *deprecated*

- Runs load_values from each of the listed loadered in the order they appear
- Loader options:
  - **environ**
    - Loads the current environmental variables into secretbox.
  - **envfile**
    - Loads .env file. Optional `filename` kwarg can override the default load of the current working directory `.env` file.
  - **awssecret**
    - Loads secrets from an AWS secret manager. Requires `aws_sstore_name` and `aws_region_name` keywords to be provided or for those values to be in the environment variables under `AWS_SSTORE_NAME` and `AWS_REGION_NAME`. `aws_sstore_name` is the name of the store, not the arn.
  - **awsparameterstore**
    - Loads secrets from an AWS Parameter Store (SSM/ASM). Requires `aws_sstore_name` and `aws_region_name` keywords to be provided or for those values to be in the environment variables under `AWS_SSTORE_NAME` and `AWS_REGION_NAME`. `aws_sstore_name` is the name or prefix of the parameters to retrieve.
- **kwargs**
  - All keyword arguments are passed into the loaders when they are called. Each loader details which extra keyword arguments it uses or requires above.

---

### Loaders

All loaders follow the same abstract base class. Calling `.run()` will load secrets from the loader's source. Each loader will have optional parameters definable on instantiation.

**EnvironLoader**

Load system environ values

**EnvFileLoader**

Load local .env file.

- Args:
  - filename: [str] Optional filename (with path) to load, default is `.env`

**AWSSecretLoader**

Load secrets from an AWS secret manager.

- Args:
  - aws_sstore: [str] Name of the secret store (not the arn)
    - Can be provided through environ `AWS_SSTORE_NAME`
  - aws_region: [str] Regional location of secret store
    - Can be provided through environ `AWS_REGION_NAME` or `AWS_REGION`

**AWSParameterStoreLoader**

Load secrets from AWS parameter store.

- Args:
  - aws_sstore: [str] Name of parameter or path of parameters if endings with `/`
    - Can be provided through environ `AWS_SSTORE_NAME`
  - aws_region: [str] Regional Location of parameter(s)
    - Can be provided through environ `AWS_REGION_NAME` or `AWS_REGION`

---

## A note about logging output

This library restricts any `DEBUG` logging output during the use of a `boto3` client or the methods of that client. This is to prevent the logging of your secrets as well as the bearer tokens used within AWS. You can disable this at the aws loader by adjusting `hide_boto_debug` to be `False`. You will need to define your own instance of the `AWSParameterStore` or `AWSSecretLoader` and adjust their flag before calling `load_values()`.

---

## `.env` file format

Current format for the `.env` file supports strings only and is parsed in the following order:

- Each seperate line is considered a new possible key/value set
- Each set is delimted by the first `=` found
- Leading `export` keyword is removed from key, case agnostic
- Leading and trailing whitespace are removed
- Matched leading/trailing single quotes or double quotes will be stripped from values (not keys).

I'm open to suggestions on standards to follow here. This is compiled from "crowd standard" and what is useful at the time.

This `.env` example:

```conf
# Comments are ignored

KEY=value

Invalid lines without the equal sign delimiter will also be ignored
```

Will be parsed as:

```python
{"KEY": "value"}
```

This `.env` example:

```conf
export PASSWORD = correct horse battery staple
USER_NAME="not_admin"

MESSAGE = '    Totally not an "admin" account logging in'
```

Will be parsed as:

```python
{
    "PASSWORD": "correct horse battery staple",
    "USER_NAME": "not_admin",
    "MESSAGE": '    Totally not an "admin" account logging in',
}
```

---

## Local developer installation

It is **strongly** recommended to use a virtual environment
([`venv`](https://docs.python.org/3/library/venv.html)) when working with python
projects. Leveraging a `venv` will ensure the installed dependency files will
not impact other python projects or any system dependencies.

The following steps outline how to install this repo for local development. See
the [CONTRIBUTING.md](../CONTRIBUTING.md) file in the repo root for information
on contributing to the repo.

**Windows users**: Depending on your python install you will use `py` in place
of `python` to create the `venv`.

**Linux/Mac users**: Replace `python`, if needed, with the appropriate call to
the desired version while creating the `venv`. (e.g. `python3` or `python3.8`)

**All users**: Once inside an active `venv` all systems should allow the use of
`python` for command line instructions. This will ensure you are using the
`venv`'s python and not the system level python.

---

## Installation steps

Clone this repo and enter root directory of repo:

```bash
git clone https://github.com/Preocts/secretbox
cd secretbox
```

Create the `venv`:

```bash
python -m venv venv
```

Activate the `venv`:

```bash
# Linux/Mac
. venv/bin/activate

# Windows
venv\Scripts\activate
```

The command prompt should now have a `(venv)` prefix on it. `python` will now
call the version of the interpreter used to create the `venv`

Install editable library and development requirements:

```bash
# Update pip and tools
python -m pip install --upgrade pip wheel setuptools

# Install development requirements
python -m pip install -r requirements-dev.txt

# Install requirements (if any defined)
python -m pip install -r requirements.txt
```

Install pre-commit [(see below for details)](#pre-commit):

```bash
pre-commit install
```

---

## Misc Steps

Run pre-commit on all files:

```bash
pre-commit run --all-files
```

Run tests:

```bash
tox [-r] [-e py3x]
```

To deactivate (exit) the `venv`:

```bash
deactivate
```

---

## [pre-commit](https://pre-commit.com)

> A framework for managing and maintaining multi-language pre-commit hooks.

This repo is setup with a `.pre-commit-config.yaml` with the expectation that
any code submitted for review already passes all selected pre-commit checks.
`pre-commit` is installed with the development requirements and runs seemlessly
with `git` hooks.

---

## Makefile

This repo has a Makefile with some quality of life scripts if the system
supports `make`.  Please note there are no checks for an active `venv` in the
Makefile.

| PHONY             | Description                                                        |
| ----------------- | ------------------------------------------------------------------ |
| `init`            | Update pip, setuptools, and wheel to newest version                |
| `install`         | install project                                                    |
| `install-dev`     | install development requirements and project                       |
| `build-dist`      | Build source distribution and wheel distribution                   |
| `clean-artifacts` | Deletes python/mypy artifacts including eggs, cache, and pyc files |
| `clean-tests`     | Deletes tox, coverage, and pytest artifacts                        |
| `clean-build`     | Deletes build artifacts                                            |
| `clean-all`       | Runs all clean scripts                                             |
