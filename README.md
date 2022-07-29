# secretbox

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/python-template/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/python-template/main)
[![Python Tests](https://github.com/Preocts/secretbox/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Preocts/secretbox/actions/workflows/python-tests.yml)
[![codecov](https://codecov.io/gh/Preocts/secretbox/branch/main/graph/badge.svg?token=7QFJGMD3JI)](https://codecov.io/gh/Preocts/secretbox)

A library that offers a simple method of loading and accessing environmental
variables, `.env` file values, and other sources of secrets. The class stores
values to state when load methods are called.

Loaded values are also injected into the local environ. This is to assist with
adjacent libraries that reference `os.environ` values by default. Required
values can be kept in a `.env` file instead of managing a script to load them
into the environment.

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

*The optional aws package includes boto3. If you are using secretbox on AWS
objects that already have boto3 install, such as lambda, this remains an
optional package for your deploy.*

---

# Documentation:

## Example use with `auto_load=True`

This loads the system environ and the `.env` from the current working directory
into the class state for quick reference. Loaded secrets can be accessed from
the `.values` property or from other methods such as `os.getenviron()`.

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

Loaders collect key:value pair secrets from various sources. When you need more
than one source loaded, in a particular order, with a single collection of all
loaded values then `.use_loaders()` is the solution. Each loader is executed in
turn and the results compiled with the `SecretBox` object.

This loads the system environment variables, an AWS secret store, and then a
specific `.env` file if it exists. Secrets are loaded in the order of loaders,
replacing any matching keys from the prior loader.

```python
from secretbox import SecretBox

secrets = SecretBox()


def main() -> int:
    """Main function"""
    secrets.use_loaders(
        secrets.EnvironLoader(),
        secrets.AWSSecretLoader("mySecrets", "us-east-1"),
        secrets.EnvFileLoader("sandbox/.override_env"),
    )

    my_sevice_password = secrets.values.get("SERVICE_PW")
    # More code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## Example use with stand-alone loader

Loaders can be used as needed. For this example we only need to load an AWS
Parameter store.

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

- Loads environment variables and then the .env file from current working
  directory if found.

**load_debug**

- When true, internal logger level is set to DEBUG. Secret values are truncated,
  however it is not recommended to leave this on for production deployments.

### SecretBox API:

**.values**

- *Property*: A copy of the `dict[str, str]` key:value pairs loaded

**.use_loaders(\*loaders: Loader) -> None**

- Loaded results are injected into environ and stored in state.

---

**NOTE:** All .get methods pull from the instance state of the class and do not
reflect changes to the enviornment post-load.

**.get(key: str, default: str | None = None) -> str**

- Returns the string value of the loaded value by key name. If the key does not
  exists then `KeyError` will be raised unless a default is given, then that is
  returned.

**.set(key: str, value: str) -> None**

- Adds the key:value pair to both the secretbox instance and the environment
  variables

---

### Loaders

All loaders follow the same abstract base class. Calling `.run()` will load
secrets from the loader's source. Each loader will have optional parameters
definable on instantiation.

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
  - aws_sstore: [str] Name of parameter or path of parameters if endings with
    `/`
    - Can be provided through environ `AWS_SSTORE_NAME`
  - aws_region: [str] Regional Location of parameter(s)
    - Can be provided through environ `AWS_REGION_NAME` or `AWS_REGION`

---

## A note about logging output

This library restricts any `DEBUG` logging output during the use of a `boto3`
client or the methods of that client. This is to prevent the logging of your
secrets as well as the bearer tokens used within AWS. You can disable this at
the aws loader by adjusting `hide_boto_debug` to be `False`. You will need to
define your own instance of the `AWSParameterStore` or `AWSSecretLoader` and
adjust their flag before calling `load_values()`.

---

## `.env` file format

Current format for the `.env` file supports strings only and is parsed in the
following order:

- Each seperate line is considered a new possible key/value set
- Each set is delimted by the first `=` found
- Leading `export` keyword is removed from key, case agnostic
- Leading and trailing whitespace are removed
- Matched leading/trailing single quotes or double quotes will be stripped from
  values (not keys).

I'm open to suggestions on standards to follow here. This is compiled from
"crowd standard" and what is useful at the time.

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

```console
# Update pip and tools
$ python -m pip install --upgrade pip

# Install editable version of library
$ python -m pip install --editable .[dev]
```

Install pre-commit [(see below for details)](#pre-commit):

```console
$ pre-commit install
```

---

## Misc Steps

Run pre-commit on all files:

```console
$ pre-commit run --all-files
```

Run tests:

```console
$ tox [-r] [-e py3x]
```

Build dist:

```console
$ python -m pip install --upgrade build

$ python -m build
```

To deactivate (exit) the `venv`:

```console
$ deactivate
```

---

## Note on flake8:

`flake8` is included in the `requirements-dev.txt` of the project. However it
disagrees with `black`, the formatter of choice, on max-line-length and two
general linting errors. `.pre-commit-config.yaml` is already configured to
ignore these. `flake8` doesn't support `pyproject.toml` so be sure to add the
following to the editor of choice as needed.

```ini
--ignore=W503,E203
--max-line-length=88
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

| PHONY             | Description                                                           |
| ----------------- | --------------------------------------------------------------------- |
| `init`            | Update pip to newest version                                          |
| `install`         | install the project                                                   |
| `install-test`    | install test requirements and project as editable install             |
| `install-dev`     | install development/test requirements and project as editable install |
| `build-dist`      | Build source distribution and wheel distribution                      |
| `clean-artifacts` | Deletes python/mypy artifacts, cache, and pyc files                   |
| `clean-tests`     | Deletes tox, coverage, and pytest artifacts                           |
| `clean-build`     | Deletes build artifacts                                               |
| `clean-all`       | Runs all clean scripts                                                |
