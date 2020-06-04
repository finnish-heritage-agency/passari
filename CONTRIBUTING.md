Development guidelines
======================

The codebase has been developed with the following (rough) guidelines in mind:

* Try to keep the codebase [PEP 8](https://www.python.org/dev/peps/pep-0008/) compliant. This will pay off when using static code analysis tools like [flake8](https://flake8.pycqa.org/en/latest/) and [pylint](http://pylint.pycqa.org/en/latest/intro.html) that help you catch iffy code before they cause problems.
* Try to maintain good test coverage. Tests are written in [pytest](https://docs.pytest.org/en/latest/) and uses fixtures extensively in an effort to keep tests succinct.
* Try to follow [Semantic Versioning](https://semver.org). In short, using the version format `X.Y.Z`, increment Z when only adding bug fixes, increment Y when adding features in a backwards compatible manner and increment X when making incompatible API changes.
* Only support Python 3.6+. Code is written using Python 3.6 features without aiming to support earlier versions such as Python 3.5 or Python 2.7.
* Try to keep documentation up-to-date. Documentation is written in `docs/` using [Sphinx](http://www.sphinx-doc.org/).

Finally, these guidelines are not set in stone and you can use good judgment to ignore them when they're more trouble than they're worth.
