"""Sphinx configuration for the dedoku documentation site."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dedoku import __version__  # noqa: E402

project = "dedoku"
author = "n36l3c7"
copyright = "2026, n36l3c7"
version = release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "myst_parser",
]

autodoc_member_order = "bysource"
autodoc_typehints = "description"

exclude_patterns = ["_build"]

html_theme = "furo"
html_title = f"dedoku {__version__}"
html_static_path = ["_static"]
html_favicon = "_static/favicon.svg"
html_theme_options = {
    "source_repository": "https://github.com/n36l3c7/Dedoku/",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_logo": "logo-light.svg",
    "dark_logo": "logo-dark.svg",
}
