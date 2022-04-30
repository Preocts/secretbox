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

## [Development Installation Guide](docs/development.md)

---

## Documentation:

## Example use with `auto_load=True`

This loads the system environ and the `.env` from the current working directory into the class state for quick reference.

```python
from secretbox import SecretBox

secrets = SecretBox(auto_load=True)


def main() -> int:
    """Main function"""
    my_sevice_password = secrets.get("SERVICE_PW")
    # More code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Example use with `load_from()`

This loads our system environ, our AWS secret store, and then a specific `.env` file if it exists (replacing any values from the prior to loads)

Notice we can declare our parameters when creating the `SecretBox` instance and when calling `load_from()`. All keywords will be sent to the loaders with preference to the `load_from()` values.

```python
from secretbox import SecretBox

secrets = SecretBox(filename="sandbox/.override_env")


def main() -> int:
    """Main function"""
    secrets.load_from(
        loaders=["environ", "awssecret", "envfile"],
        aws_sstore_name="mySecrets",
        aws_region_name="us-east-1",
    )
    my_sevice_password = secrets.get("SERVICE_PW")
    # More code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## SecretBox arguments:

`SecretBox(*, auto_load: bool = False, load_debug: bool = False, **kwargs: Any)`

**auto_load**

- Loads environment variables and then the .env file from current working directory if found.

**load_debug**

- When true, internal logger level is set to DEBUG. Secret values are truncated, however it is not recommended to leave this on for production deployments.

**kwargs**

- All keyword arguments will be passed to loaders when called. These can also be given to the `load_from()` method as detailed below.

## SecretBox API:

**NOTE:** All .get methods pull from the instance state of the class and do not reflect changes to the enviornment post-load.

**.get(key: str, default: str | None = None) -> str**

- Returns the string value of the loaded value by key name. If the key does not exists then `KeyError` will be raised unless a default is given, then that is returned.

**.get_int(key: str, default: int | None = None) -> int**

- Returns the int value of the loaded value by key name. Raise `ValueError` if the found key cannot convert to `int`. Raise `KeyError` if the key is not found and no default is given.

**.get_list(key: str, delimiter: str = ",", default: list[str] | None = None) -> List[str]:**

- Returns a list of the loaded value by key name, seperated at defined delimiter. No check is made if delimiter exists in value. `default` is returned if key is not found otherwise a `KeyError` is raised.

**.load_from(loaders: list[str], \*\*kwargs: Any) -> None**

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
