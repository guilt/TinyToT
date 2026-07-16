# Configuration file for the Sphinx documentation builder.

import os
import sys
from datetime import date
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

# Make the tinytot package importable when building docs from repo root.
sys.path.insert(0, os.path.abspath("../.."))

project = "TinyToT"
html_title = "TinyToT — Tree of Thoughts Inference Server"
author = "TinyToT Contributors"
copyright = f"{date.today().year}, {author}"

try:
    version = _pkg_version("tinytot")
    release = version
except PackageNotFoundError:
    version = "dev"
    release = "dev"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "myst_nb",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]

todo_include_todos = True

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

myst_enable_extensions = ["colon_fence", "deflist", "fieldlist"]
myst_heading_anchors = 4
myst_url_schemes = ("http", "https", "mailto")
myst_fence_as_directive = ["mermaid"]
mermaid_params = ["--width", "100%", "--backgroundColor", "transparent"]
myst_suppress_warnings = ["myst.header"]

# Suppress toc.not_included for API reference files (linked from README, not toctree)
suppress_warnings = ["toc.not_included"]

master_doc = "index"
source_suffix = [".rst", ".md"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "README.md"]

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

nb_execution_mode = "off"
