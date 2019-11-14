# Release a new version

As a maintainer, if you plan to release a new version of Watson, you will find
useful information in this page.

## Bump a new `x.y.z` release

Create a new branch:

```bash
$ git checkout -b prepare-x.y.z
```

Edit the following files to describe changes and bump the version number:

* `watson/version.py`: update the version number
* `CHANGELOG.md`: add release notes (see previous releases examples)
* `docs/about/release-notes.md`: copy/paste release notes here
* `watson.completion` and `watson.zsh-completion`: generate up-to-date
  completion script by running `make completion-scripts`

Then commit your work, tag the release and push everything to GitHub:

```bash
$ git add watson/version.py CHANGELOG.md docs/about/release-notes.md
$ git commit -m 'Bump release to x.y.z'
$ git tag x.y.z
$ git push origin prepare-x.y.z
$ git push origin --tags
```

Create a new pull request (PR) with the `prepare-x.y.z` branch. You can safely
merge this PR if all tests are green.

Draft a new [Watson Release on
GitHub](https://github.com/TailorDev/Watson/releases) with the same release
notes.

## Push the `x.y.z` release to PyPI

Checkout the up-to-date `master` branch:

```bash
$ git checkout master
$ git pull --rebase origin master
```

Now, build the release and submit it to PyPI using
[twine](https://github.com/pypa/twine) (you'll need to be registered as a
maintainer of the package):

```bash
$ python setup.py sdist bdist_wheel
$ twine upload dist/*
```

## Update online documentation

We use [`mkdocs`](http://www.mkdocs.org) to generate the online documentation.
It must be updated via:

```bash
$ mkdocs gh-deploy --clean
```

## Publish the `x.y.z` release to Homebrew

* Fork the [Homebrew/homebrew-core](https://github.com/Homebrew/homebrew-core)
  repository to your personal GitHub account.
* Get the new release SHA256 checksum by copying it from [td-watson
  Warehouse](https://pypi.org/project/td-watson/#files) page (the new PyPI)
* Update brew formula with the automation command `bump-formula-pr`:

```bash
$ brew bump-formula-pr \
  --url='https://files.pythonhosted.org/packages/[...]/td-watson-x.y.z.tar.gz' \
  --sha256='PASTE THE SHA256 CHECKSUM HERE' \
  watson
```

Note: you may also need to update versions of Watson's dependencies (and related
checksum). See [Homebrew's
documentation](https://docs.brew.sh/How-To-Open-a-Homebrew-Pull-Request.html)
for details.
