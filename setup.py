"""
Setup the package.

To use the full functionality of this file, you must:

```sh
$ pip install pyyaml
$ pip install twine
$ pip install wheel
$ pip install re-extensions
```
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple

import yaml
from re_extensions import rsplit, word_wrap
from setuptools import Command, find_packages, setup

here = Path(__file__).parent

# Load the package's meta-data from metadata.yml.
yml: Dict[str, Any] = yaml.safe_load((here / "metadata.yml").read_text())
NAME: Final[str] = yml["NAME"]
VERSION: Final[Optional[str]] = yml["VERSION"]
SUMMARY: Final[str] = yml["SUMMARY"]
HOMEPAGE: Final[str] = yml["HOMEPAGE"]
AUTHOR: Final[str] = yml["AUTHOR"]
AUTHOR_EMAIL: Final[str] = yml["AUTHOR_EMAIL"]
REQUIRES_PYTHON: Final[str] = yml["REQUIRES_PYTHON"]
REQUIRES: Final[List[str]] = yml["REQUIRES"]
EXTRAS: Final[Dict] = yml["EXTRAS"]
SOURCE: str = yml["SOURCE"]
LICENSE = (here / "LICENSE").read_text().partition("\n")[0]
CLASSIFIERS: List[str] = yml["CLASSIFIERS"]
SUBMODULES: List[str] = yml["SUBMODULES"]
EXCLUDES: List[str] = yml["EXCLUDES"]

# Import the README and use it as the long-description.
readme_path = here / "README.md"
try:
    long_description = "\n" + readme_path.read_text()
except FileNotFoundError:
    long_description = SUMMARY


# Load the package's __version__.py module as a dictionary.
about = {}
python_exec = exec
if not VERSION:
    try:
        python_exec((here / SOURCE / "__version__.py").read_text(), about)
    except FileNotFoundError:
        about["__version__"] = "0.0.0"
else:
    about["__version__"] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Print things in bold."""
        print(f"\033[1m{s}\033[0m")

    def initialize_options(self):
        """Initialize options."""

    def finalize_options(self):
        """Finalize options."""

    def run(self):
        """Run commands."""
        raise NotImplementedError


def _readme2doc(
    readme: str,
    name: str = NAME,
    requires: List[str] = REQUIRES,
    homepage: str = HOMEPAGE,
    pkg_license: str = LICENSE,
) -> Tuple[str, str]:
    doc, rd = "", ""
    for i, s in enumerate(rsplit("\n## ", readme)):
        head = re.search(" .*\n", s).group()[1:-1]
        if i == 0:
            s = re.sub("^\n# .*", f"\n# {name}", s)
        elif head == "Requirements":
            s = re.sub(
                "```txt.*```",
                "```txt\n" + "\n".join(requires) + "\n```",
                s,
                flags=re.DOTALL,
            )
        elif head == "Installation":
            s = re.sub(
                "```sh.*```", f"```sh\n$ pip install {name}\n```", s, flags=re.DOTALL
            )
        elif head == "See Also":
            pypipage = f"https://pypi.org/project/{name}/"
            s = re.sub(
                "### PyPI project\n.*",
                f"### PyPI project\n* {pypipage}",
                re.sub(
                    "### Github repository\n.*",
                    f"### Github repository\n* {homepage}",
                    s,
                ),
            )
        elif head == "License":
            s = f"\n## License\nThis project falls under the {pkg_license}.\n"

        rd += s
        if head not in {"Installation", "Requirements", "History"}:
            doc += s
    doc = re.sub("<!--html-->.*<!--/html-->", "", doc, flags=re.DOTALL)
    return word_wrap(doc, maximum=88) + "\n\n", rd


class ReadmeFormatError(Exception):
    """Raised when the README has a wrong format."""


def _wrap_packages(
    name: str = NAME,
    src: str = SOURCE,
    exclude: List[str] = EXCLUDES,
    submodule: List[str] = SUBMODULES,
    top: Path = here,
) -> Tuple[List[str], Dict[str, str]]:
    main_name = name.replace("-", "_")
    main_pkgs = find_packages(exclude=exclude + [x + "*" for x in submodule])
    pkgs = [re.sub(f"^{src}", main_name, x) for x in main_pkgs]
    pkg_dir = {main_name: src}
    for sub_name in submodule:
        sub_yml: Dict[str, Any] = yaml.safe_load(
            (top / sub_name.replace(".", "/") / "metadata.yml").read_text()
        )
        sub_excludes: List[str] = sub_yml["EXCLUDES"]
        sub_src: str = sub_yml["SOURCE"]
        sub_subm: List[str] = sub_yml["SUBMODULES"]
        if sub_subm:
            raise ValueError(
                "can not build submodules of a submodule: "
                + ", ".join(f"{sub_name}.{x}" for x in sub_subm)
            )
        sub_pkgs = find_packages(
            exclude=exclude
            + main_pkgs
            + [sub_name]
            + [f"{sub_name}.{x}" for x in sub_excludes]
        )
        wrapped_pkgs = [
            re.sub(f"^{src}", main_name, x).replace(f".{sub_src}", "") for x in sub_pkgs
        ]
        pkgs.extend(wrapped_pkgs)
        for p, q in zip(wrapped_pkgs, sub_pkgs):
            pkg_dir[p] = q.replace(".", "/")
    return pkgs, pkg_dir


if __name__ == "__main__":
    # Import the __init__.py and change the module docstring.
    try:
        init_path = here / SOURCE / "__init__.py"
        module_file = init_path.read_text()
        new_doc, long_description = _readme2doc(long_description)
        if "'''" in new_doc and '"""' in new_doc:
            raise ReadmeFormatError("Both \"\"\" and ''' are found in the README")
        if '"""' in new_doc:
            new_doc = f"'''{new_doc}'''"
        else:
            new_doc = f'"""{new_doc}"""'
        module_file = re.sub(
            "^\"\"\".*\"\"\"|^'''.*'''|^", new_doc, module_file, flags=re.DOTALL
        )
        init_path.write_text(module_file)
        readme_path.write_text(long_description.strip())
    except FileNotFoundError:
        pass

    packages, package_dir = _wrap_packages()
    # Where the magic happens.
    setup(
        name=NAME,
        version=about["__version__"],
        description=SUMMARY,
        long_description=long_description,
        long_description_content_type="text/markdown",
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        python_requires=REQUIRES_PYTHON,
        url=HOMEPAGE,
        packages=packages,
        package_dir=package_dir,
        install_requires=REQUIRES,
        extras_require=EXTRAS,
        include_package_data=False,
        license=LICENSE.partition(" ")[0],
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=CLASSIFIERS,
        # $ setup.py publish support.
        cmdclass={"upload": UploadCommand},
    )
