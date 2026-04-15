# Python: Twente Milieu

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![Build Status][build-shield]][build]
[![Code Coverage][codecov-shield]][codecov]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

[![Sponsor Frenck via GitHub Sponsors][github-sponsors-shield]][github-sponsors]

[![Support Frenck on Patreon][patreon-shield]][patreon]

Asynchronous Python client for the Twente Milieu API.

## About

This package allows you to request waste pickup days from Twente Milieu
programmatically. It is mainly created to allow third-party programs to use
or respond to this data.

An excellent example of this might be Home Assistant, which allows you to write
automations, e.g., play a Google Home announcement in the morning when it is
trash pickup day.

## Installation

```bash
pip install twentemilieu
```

## Usage

```python
import asyncio

from twentemilieu import TwenteMilieu, WasteType


async def main() -> None:
    """Show example on stats from Twente Milieu."""
    async with TwenteMilieu(post_code="1234AB", house_number=1) as twente:
        unique_id = await twente.unique_id()
        print("Unique Address ID:", unique_id)
        pickups = await twente.update()
        print("Next pickup for Non-recyclable:", pickups.get(WasteType.NON_RECYCLABLE))


if __name__ == "__main__":
    asyncio.run(main())
```

## Behavior & error handling

Each API call is a single HTTP POST — the client does **not** retry on
transient failures. If you need retries with backoff, wrap the calls in
your own retry loop (or use something like [`backoff`][backoff]).

Requests are bounded by a per-call timeout, which defaults to 10 seconds
and can be overridden via the `request_timeout` constructor argument:

```python
async with TwenteMilieu(
    post_code="1234AB",
    house_number=1,
    request_timeout=5,
) as twente:
    ...
```

Cancellation is plain `asyncio`: cancelling the task awaiting
`unique_id()` or `update()` aborts the in-flight request, and the
context manager still cleans up the internal session on exit.

All exceptions inherit from `TwenteMilieuError`:

| Exception                     | Raised when                                            |
| ----------------------------- | ------------------------------------------------------ |
| `TwenteMilieuConnectionError` | Request timed out or the network / API was unreachable |
| `TwenteMilieuAddressError`    | The address could not be found in the service area     |
| `TwenteMilieuError`           | Any other unexpected response from the API             |

## Command-line interface

This package ships with an optional CLI that is handy for quickly
inspecting the waste pickup schedule for an address. Install it with
the `cli` extra:

```bash
pip install "twentemilieu[cli]"
```

The CLI exposes two commands: `upcoming` (a chronologically sorted list
of the next pickups across all waste types) and `next` (the single next
pickup, optionally filtered by waste type). Both commands accept
`--post-code`, `--house-number`, and an optional `--house-letter`, and
both support a `--json` flag for machine-readable output.

```bash
# Show the next 5 pickups across all waste types
twentemilieu upcoming --post-code 7531AT --house-number 148

# Limit to the next 3 pickups and emit JSON
twentemilieu upcoming --post-code 7531AT --house-number 148 --limit 3 --json

# Show the very next pickup (any waste type)
twentemilieu next --post-code 7531AT --house-number 148

# Show the next organic pickup only
twentemilieu next --post-code 7531AT --house-number 148 --waste-type organic

# Emit as JSON for use in scripts
twentemilieu next --post-code 7531AT --house-number 148 --waste-type organic --json
```

Address options can also be supplied via the `TWENTEMILIEU_POST_CODE`,
`TWENTEMILIEU_HOUSE_NUMBER`, and `TWENTEMILIEU_HOUSE_LETTER` environment
variables. Run any command with `--help` for the full reference.

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality. The format of the log is based on
[Keep a Changelog][keepchangelog].

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Setting up development environment

The easiest way to start, is by opening a CodeSpace here on GitHub, or by using
the [Dev Container][devcontainer] feature of Visual Studio Code.

[![Open in Dev Containers][devcontainer-shield]][devcontainer]

This Python project is fully managed using the [Poetry][poetry] dependency manager. But also relies on the use of NodeJS for certain checks during development.

You need at least:

- Python 3.11+
- [Poetry][poetry-install]
- NodeJS 24+ (including NPM)

To install all packages, including all development requirements:

```bash
npm install
poetry install
```

As this repository uses the [prek][prek] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run prek run --all-files
```

To run just the Python tests:

```bash
poetry run pytest
```

## Authors & contributors

The original setup of this repository is by [Franck Nijhof][frenck].

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2019-2026 Franck Nijhof

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

[backoff]: https://github.com/litl/backoff
[build-shield]: https://github.com/frenck/python-twentemilieu/actions/workflows/tests.yaml/badge.svg
[build]: https://github.com/frenck/python-twentemilieu/actions/workflows/tests.yaml
[codecov-shield]: https://codecov.io/gh/frenck/python-twentemilieu/branch/main/graph/badge.svg
[codecov]: https://codecov.io/gh/frenck/python-twentemilieu
[contributors]: https://github.com/frenck/python-twentemilieu/graphs/contributors
[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/frenck/python-twentemilieu
[frenck]: https://github.com/frenck
[github-sponsors-shield]: https://frenck.dev/wp-content/uploads/2019/12/github_sponsor.png
[github-sponsors]: https://github.com/sponsors/frenck
[keepchangelog]: http://keepachangelog.com/en/1.0.0/
[license-shield]: https://img.shields.io/github/license/frenck/python-twentemilieu.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2026.svg
[patreon-shield]: https://frenck.dev/wp-content/uploads/2019/12/patreon.png
[patreon]: https://www.patreon.com/frenck
[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[prek]: https://github.com/j178/prek
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[python-versions-shield]: https://img.shields.io/pypi/pyversions/twentemilieu
[pypi]: https://pypi.org/project/twentemilieu
[releases-shield]: https://img.shields.io/github/release/frenck/python-twentemilieu.svg
[releases]: https://github.com/frenck/python-twentemilieu/releases
[semver]: http://semver.org/spec/v2.0.0.html
