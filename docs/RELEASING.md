# Releasing

Each package is released on its own by a GitHub Actions workflow. A release starts when someone with write access publishes a GitHub Release whose tag names the package and the version.

| Package | Registry | Workflow | Tag |
|---------|----------|----------|-----|
| `codemie-sdk-python` | PyPI | `publish-python.yml` | `python-vX.Y.Z[-rcN]` |
| `codemie-sdk` | npm | `publish-node.yml` | `node-vX.Y.Z[-rcN]` |

A merge to `main` never releases a package. A `python-v*` tag runs only the Python workflow. A `node-v*` tag runs only the Node workflow. A tag with any other prefix runs neither.

## How to release

1. Merge the changes you want to release to `main`. Wait for CI to pass.
2. Choose the version. It must be higher than the highest version on the registry and on the line in the manifest (see below).
3. Create the Release. Use **Publish release**: **Save draft** does not start a workflow.
   - UI: Releases > Draft a new release > choose a new tag such as `python-v0.1.665`, target `main` > Publish release.
   - CLI: `gh release create python-v0.1.665 --target main --generate-notes`
4. Open the run in the Actions tab. `verify` builds and checks. `publish` waits for approval if the `release` environment has reviewers.

## How versions work

The tag is the version: `python-v0.1.665` releases `0.1.665`. The manifest (`pyproject.toml`, `package.json`) holds only the base line, `MAJOR.MINOR.0`. It is `0.1.0` today.

- The tag must be a release `MAJOR.MINOR.PATCH` or release candidate `MAJOR.MINOR.PATCH-rcN` (such as `python-v0.1.665-rc0` or `node-v0.1.665-rc0`) on the same `MAJOR.MINOR` line as the manifest. Other pre-release tags, a missing part or a leading zero fails.
- Release candidate versions (`-rcN`) are published under the `rc` dist-tag on npm (`npm install codemie-sdk@rc`), keeping `latest` pointing to stable. On PyPI, pip ignores pre-releases by default.
- The workflow stamps the version into the build only. It does not commit a version change.
- The Python `__version__` is read from the installed package metadata, so there is one source of truth.
- To start a new line (a feature or breaking release), raise the base in the manifest, for example to `0.2.0`, and merge it. Then tag `python-v0.2.0`.
- Runs are grouped by tag, so a release is never cancelled by a newer one.

## Checks before anything is published

The `verify` job has no secrets. It fails, and nothing is published, when:

- the release commit is not on `main`;
- for a manual publish, the tag does not exist or does not point to the dispatched commit;
- the tag prefix, format or line does not match;
- the version is equal to or lower than the highest published version (`scripts/release/check_version.py --version`);
- lint, tests or the build fail.

The `publish` job runs the version check again right before the upload, because it can wait for approval and another release may land in between.

A timeout, network error, malformed registry response or a published version that cannot be parsed stops the release. The gate fails closed. A package that is not on the registry yet (HTTP 404) passes. Pre-release versions on the registry follow PEP 440 for PyPI and semantic versioning for npm.

`scripts/release/check_version.py --tag <tag> --base <MAJOR.MINOR[.0]>` prints the version a tag names and uses no network.

## Dry run

Local, with no credentials and no publish. It reads the live registry, stamps a copy of the package, runs lint and tests, and builds:

```bash
scripts/release/dry_run.sh python python-v0.1.665   # needs poetry
scripts/release/dry_run.sh node node-v0.1.665       # needs node and npm
```

In GitHub, start the workflow with `workflow_dispatch` and give the `tag` input. It builds and checks only (`dry_run` is on by default). To publish from a manual run, set `dry_run` off, type `publish` in the `publish` input, and start the run from `main`. A run from another branch, or without all three, does not publish. A manual publish needs the tag to exist and to point to the commit it runs from. It creates no Release, so use a Release for real releases.

## Registry setup

Do this once, by a repository administrator.

- **GitHub environment `release`.** Create it in Settings > Environments. Restrict deployments to the tags `python-v*` and `node-v*` (the manual publish runs from `main`, so also allow `main`). Add required reviewers if a second approval is wanted.
- **Who can release.** Only people with write access can create a Release. Keep that group small.
- **PyPI token.** Store a PyPI API token as the secret `PYPI_API_TOKEN`, preferably on the `release` environment. Only the PyPI `publish` job reads it.
- **npm token.** Create an automation token for `codemie-sdk` and store it as the secret `NPM_TOKEN`, preferably on the `release` environment. Only the npm `publish` job reads it.
