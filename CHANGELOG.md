# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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