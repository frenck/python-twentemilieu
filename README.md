# Python: Meppel Afvalkalender

[![GitHub Release][releases-shield]][releases]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![Build Status][build-shield]][build]

Asynchronous Python client for the Meppel Afvalkalender API.

## About

This package allows you to request waste pickup days from Meppel Afvalkalender
programmatically. It is mainly created to allow third-party programs to use
or respond to this data.

An excellent example of this might be Home Assistant, which allows you to write
automations, e.g., play a Google Home announcement in the morning when it is
trash pickup day.

## Installation

```bash
pip install meppel_afvalkalender
```

## Usage

```python
import asyncio

from meppel_afvalkalender import MeppelAfvalkalender, WASTE_TYPE_NON_RECYCLABLE


async def main(loop):
    """Show example on stats from Meppel Afvalkalender."""
    async with MeppelAfvalkalender(post_code="1234AB", house_number=1, loop=loop) as tw:
        unique_id = await tw.unique_id()
        print("Unique Address ID:", unique_id)
        await tw.update()
        pickup = await tw.next_pickup(WASTE_TYPE_NON_RECYCLABLE)
        print("Next pickup for Non-recyclable:", pickup)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
```

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality. The format of the log is based on
[Keep a Changelog][keepchangelog].

Releases are based on [Semantic Versioning][semver], and use the format
of ``MAJOR.MINOR.PATCH``. In a nutshell, the version will be incremented
based on the following:

- ``MAJOR``: Incompatible or major changes.
- ``MINOR``: Backwards-compatible new features and enhancements.
- ``PATCH``: Backwards-compatible bugfixes and package updates.

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Setting up development environment

In case you'd like to contribute, a `Makefile` has been included to ensure a
quick start.

```bash
make venv
source ./venv/bin/activate
make dev
```

Now you can start developing, run `make` without arguments to get an overview
of all make goals that are available (including description):

```bash
$ make
Asynchronous Python client for Meppel Afvalkalender.

Usage:
  make help                            Shows this message.
  make dev                             Set up a development environment.
  make lint                            Run all linters.
  make lint-black                      Run linting using black & blacken-docs.
  make lint-flake8                     Run linting using flake8 (pycodestyle/pydocstyle).
  make lint-pylint                     Run linting using PyLint.
  make lint-mypy                       Run linting using MyPy.
  make test                            Run tests quickly with the default Python.
  make coverage                        Check code coverage quickly with the default Python.
  make install                         Install the package to the active Python's site-packages.
  make clean                           Removes build, test, coverage and Python artifacts.
  make clean-all                       Removes all venv, build, test, coverage and Python artifacts.
  make clean-build                     Removes build artifacts.
  make clean-pyc                       Removes Python file artifacts.
  make clean-test                      Removes test and coverage artifacts.
  make clean-venv                      Removes Python virtual environment artifacts.
  make dist                            Builds source and wheel package.
  make release                         Release build on PyP
  make venv                            Create Python venv environment.
```

## Authors & contributors

The original setup of this repository is by [Franck Nijhof][frenck].
The Meppel Afvalkalender version is by [Westenberg][westenberg].

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2021 Westenberg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[build-shield]: https://github.com/westenberg/python-meppel-afvalkalender/workflows/Continuous%20Integration/badge.svg
[build]: https://github.com/westenberg/python-meppel-afvalkalender/actions
[code-quality-shield]: https://img.shields.io/lgtm/grade/python/g/westenberg/python-meppel-afvalkalender.svg?logo=lgtm&logoWidth=18
[codecov-shield]: https://codecov.io/gh/westenberg/python-meppel-afvalkalender/branch/master/graph/badge.svg
[codecov]: https://codecov.io/gh/westenberg/python-meppel-afvalkalender
[commits-shield]: https://img.shields.io/github/commit-activity/y/westenberg/python-meppel-afvalkalender.svg
[commits]: https://github.com/westenberg/python-meppel-afvalkalender/commits/master
[contributors]: https://github.com/westenberg/python-meppel-afvalkalender/graphs/contributors
[westenberg]: https://github.com/westenberg
[keepchangelog]: http://keepachangelog.com/en/1.0.0/
[license-shield]: https://img.shields.io/github/license/westenberg/python-meppel-afvalkalender.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2020.svg
[project-stage-shield]: https://img.shields.io/badge/project%20stage-experimental-yellow.svg
[releases-shield]: https://img.shields.io/github/release/westenberg/python-meppel-afvalkalender.svg
[releases]: https://github.com/westenberg/python-meppel-afvalkalender/releases
[semver]: http://semver.org/spec/v2.0.0.html
