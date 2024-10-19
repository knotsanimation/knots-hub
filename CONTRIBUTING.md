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

### running the unittests

- make sure you have the extra `test` dependencies installed 
- ```shell
  python -m pytest ./tests  
  ```

### testing the app interface

As it was packaged and deployed. The session is created in a temporary
directory that will be deleted at the end of the script.

- use the `./tests/scripts/knotshub_tester.py` script

You can pass "blocks" of arguments separated by a pipe (`|`), allowing
to call mutiple command in the same session.

```shell
python ./tests/scripts/knotshub_tester.py knots_hub --debug | knots_hub kloch list
```

## developing

Few notes:

- icons at root of this repo are part of the public-interface. Changing their
  path or name is a breaking change.  
