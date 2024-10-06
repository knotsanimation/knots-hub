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

- make sure you have the extra `doc` dependencies installed (see _installing_).
- execute the `doc/build-doc.py` script

You can also use the `doc/serve-doc.py` for auto-building when
you edit a source file (doesn't work for autodoc and source code).

## tests

Running the unittests.

- make sure you have the extra `test` dependencies installed 
- ```shell
  python -m pytest ./tests  
  ```

## developing

Few notes:

- icons at root of this repo are part of the public-interface. Changing their
  path or name is a breaking change.  
