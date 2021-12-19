# Contributors Guide

## `poetry` dependency management

This project recommends using [poetry](https://python-poetry.org)

`poetry`, among many things, manages your python virtual environments for you, so you don't need to do that yourself
- specific poetry commands know what to do with respect to shielded environments
- additionally executing any command you are used to prefixed by `poetry run` simply applies the venv

The actual poetry commands to execute are wrapped in a `Makefile` allowing contributors to simply use `make` (and the available auto completion - on some platforms)


## environment setup

```bash
$ make init
```

This will call `poetry upgrade` to add dependencies required for this project into a project-specific virtualenv (which will be created on first use)

The non-poetry alternative is to:
* make your own virtualenv
* use `pip install «package»==«version»` for the dependency-entries found in the `pyproject.toml`


## tweek local preferences

```bash
$ cp dotenv-example .env
$ ${EDITOR} .env              # change your own environment settings

$ cp debug-logconf.yml your-logconf.yml
$ ${EDITOR} your-logconf.yml  # change your own logging preferences
```

## check coding syntax
```bash
$ make check
```

This will apply `flake8` with some project preferences to check up on some basic code styles and best practices.


## run the CLI
To test-run the [CLI tool](docs/cli) use the locally provided wrapper shell

```bash
$ ./nhc2_coco.sh --help
```

## (#N/A) run tests

```bash
$ make test
```

Actually, we don't have proper unit tests yet.  
Mainly due to the fact that there is no simple nhc2 mock system available that could be used in CI/CD contexts as well.  Surely a full domain of contribution-opportunity right there :smirk:
