# Contributing

Developer documentation for this repository.

## installing

Python dependencies are managed through [poetry](https://python-poetry.org/).

```shell
git clone https://github.com/knotsanimation/knots-hub.git
cd knots-hub
poetry install --all-extras
```

## documentation

Building the static documentation.

- make sure you have the `doc` extras dependencies installed.
- execute [build-doc.py](doc/build-doc.py)

You can also use the [serve-doc.py](doc/serve-doc.py) for auto-building when
you edit a source file (doesn't work for autodoc and source code).

## tests

Running the unittests.

- make sure you have the `test` extras dependencies installed.
- ```shell
  python -m pytest ./tests  
  ```
