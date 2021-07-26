# secretbox

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/python-template/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/python-template/main)
[![Python Tests](https://github.com/Preocts/secretbox/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Preocts/secretbox/actions/workflows/python-tests.yml)

A library that offers a simple method of loading and accessing environmental variables, `.env` file values, and other sources of secrets. The class stores values to state when load methods are called.

Loaded values are also injected into the local environ. This is to assist with adjacent libraries that reference `os.environ` values by default. Required values can be kept in a `.env` file instead of managing a script to load them into the environment.

### Requirements
- Python >= 3.6 <= 3.9

### Optional Dependencies
- boto3
- boto3-stubs[secretsmanager]

---

## Install

```bash
$ pip install secretbox
```

*Optional AWS Secret Manager support*
```bash
$ pip install secretbox[aws]
```

---

## Example use

```python
import sys

from secretbox import SecretBox

secrets = SecretBox()


def main() -> int:
    """Main function"""
    secrets.load()

    my_sevice_password = secrets.get("SERVICE_PW")
    # More code

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Default Behavior:** (shown above)
- On initialization the `SecretBox()` class does nothing. By calling `.load()` we cause the class to load all the currently available environ variables. It also looks for and loads, if found, a `.env` file in the working directory. From there we can access those values with `.get("KEY_NAME")`.

## SecretBox arguments:

`SecretBox(filename: str = ".env", aws_sstore_name: Optional[str] = None, aws_region: Optional[str] = None, auto_load: bool = False)`

**filename**
- You can specify a `.env` formatted file and location, overriding the default behavior to load the `.env` from the working directory

**aws_sstore_name**
- When provided, an attempt to load values from named AWS secrets manager will be made. Requires `aws_region` to be provided. Requires `boto3` and `boto3-stubs[secretsmanager]` to be installed

**aws_region**
- When provided, an attempt to load values from the given AWS secrets manager found in this region will be made. Requires `aws_sstore_name` to be provided. Requires `boto3` and `boto3-stubs[secretsmanager]` to be installed

**auto_load**
- If true, the `load()` method will be auto-exectued on initialization

## Load Order

Secret values are loaded, and over-written if pre-existing, in the following order:

1. Local environment variables
2. `.env` file
3. AWS secret store [optional]

## SecretBox methods:

**.get(["Key Name"], ("default"))**
- Returns the string value of the loaded value by key name. If the key does not exist, an empty string will be returned `""` or the provided optional default value.
- Note: This method pulls from the instance's state and does not reflect changes to the environment before/after loading.

**.load()**
- Runs all importer methods. If optional dependencies are not installed, e.g. boto3, the importer is skipped.

**.load_env_vars()**
- Loads all existing `os.environ` values into state.

**.load_env_file()**
- Loads `.env` file or any file provided with the `filename` argument on initialization.

**.load_aws_store()**
- Loads secrets from AWS secret manager. Requires `aws_sstore_name` and `aws_region` to have been provided. Will raise `NotImplementedError` if library requirements are missing.

---

## `.env` file format

Current format for the `.env` file supports strings only and is parsed in the following order:
- Each seperate line is considered a new possible key/value set
- Each set is delimted by the first `=` found
- Leading and trailing whitespace are removed
- Matched leading/trailing single quotes or double quotes will be stripped from values (not keys).

I'm open to suggestions on standards to follow here.

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
PASSWORD = correct horse battery staple
USER_NAME="not_admin"

MESSAGE = '    Totally not an "admin" account logging in'
```

Will be parsed as:
```python
{
    "PASSWORD": "correct horse battery staple",
    "USER_NAME": "not_admin",
    "MESSAGE": '    Toally not an "admin" account logging in',
}
```

---

## Local developer installation

It is **highly** recommended to use a `venv` for installation. Leveraging a `venv` will ensure the installed dependency files will not impact other python projects.

Clone this repo and enter root directory of repo:
```bash
$ git clone https://github.com/Preocts/secretbox
$ cd secretbox
```

Create and activate `venv`:
```bash
# Linux/MacOS
python3 -m venv venv
. venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate.bat
# or
py -m venv venv
venv\Scripts\activate.bat
```

Your command prompt should now have a `(venv)` prefix on it.

Install editable library and development requirements:
```bash
# Linux/MacOS
pip install -r requirements-dev.txt
pip install --editable .[aws,tests]

# Windows
python -m pip install -r requirements-dev.txt
python -m pip install --editable .[aws,test]
# or
py -m pip install -r requirements-dev.txt
py -m pip install --editable .[aws,test]
```

Install pre-commit hooks to local repo:
```bash
pre-commit install
pre-commit autoupdate
```

Run tests
```bash
tox
```

To exit the `venv`:
```bash
deactivate
```

---

### Makefile

This repo has a Makefile with some quality of life scripts if your system supports `make`.

- `install` : Clean all artifacts, update pip, install requirements with no updates
- `update` : Clean all artifacts, update pip, update requirements, install everything
- `clean-pyc` : Deletes python/mypy artifacts
- `clean-tests` : Deletes tox, coverage, and pytest artifacts
- `build-dist` : Build source distribution and wheel distribution
