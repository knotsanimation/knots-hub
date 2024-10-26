# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.13.1] - 2024-10-26

### fixed

- usage of `kloch` command with the `--debug` flag

### chores

- add a tester script in `test/scripts` to test in production-like context
- `kloch` is now retrieved from pypi


## [0.13.0] - 2024-10-20

### added

- `knots` vendor: just useful to create a directory dedicated to the pipeline for now

## [0.12.1] - 2024-10-20

### changed

- improved debug logging for vendor install

### fixed

- app restarting when using `kloch -- ...` args 
  (this replaces the private `--restarted_` arg with an environment variable)

## [0.12.0] - 2024-10-19

### added

- wrapper script to more easily the app in deploy condition for developers

### changed

- restarting system: windows cannot fully restart a process so we now launch
  a child process to the local executable instead of restarting it.
- better formatting of the logs emitted by a child process when installing

### fixed

- error when no vendor record file specified
- remove special character in uninstall script

## [0.11.1] - 2024-10-08

### fixed

- rare exception when uninstalling and no vendor was ever installed
- better handling of vendor installation fails

## [0.11.0] - 2024-10-08

### changed

- better feedback on uninstalling
- better feedback when vendor install fail

### fixed

- subprocess error when installing rez vendor

## [0.10.0] - 2024-10-07

overall polishing

### added

- cli: `about --open-data-dir`

### changed

- cli: `about --open-local-dir` by `about --open-install-dir`
- cli: `about`: better display of information
- remove shortcut creation in local data dir (used pre-0.7.0)

## [0.9.1] - 2024-10-06

### fixed

- missing super call in `about` subcommand (leading to missing update/restart part)

## [0.9.0] - 2024-10-06

### added

- `about` subcommand to provide meta info about knots-hub

## [0.8.2] - 2024-10-06

### added

- config option to skip "local check"

### fixed

- handling of restart when using the `kloch` subcommand

### changed

- better error messages 


## [0.8.1] - 2024-10-06

### fixed

- sys.executable doesn't exist when compiled with nuitka

### changed

- improved exception handling user experience


## [0.8.0] - 2024-10-06

### added

- improve error is `sys.executable` doesn't exist on launch

### changed

- simplify hub installer config:
  - replaced the installer-list json file by a simple key=value config string
  - ! config environment variable changed name

### chores

- added this CHANGELOG

## [0.7.0] - 2024-10-06

### changed

- refacto of the installation system:
  - we now assume the app is always started first from the server version. this allow to remove the complex juggling between restarts.
  - add vendor record file to store install metadata per vendor, on the filesystem
- more robust serialization/unserialization
- minimum python version supported is 3.9

### added

- allow env var in vendor config
- uninstaller also remove the temp dir it creates

### chors

- enable unittest CI on github