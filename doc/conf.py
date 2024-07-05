# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import pathlib
import time

from importlib.metadata import distribution

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = "1.3"

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "auto_intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinxcontrib.programoutput",
]

# Be picky about warnings
nitpicky = True

# Ignores stuff we can't easily resolve on other project's sphinx manuals
nitpick_ignore = []

# Allows the user to override warnings from a separate file
nitpick_path = pathlib.Path("nitpick-exceptions.txt")
if nitpick_path.exists():
    for line in nitpick_path.open():
        if line.strip() == "" or line.startswith("#"):
            continue
        dtype, target = line.split(None, 1)
        target = target.strip()
        nitpick_ignore.append((dtype, target))

# Always includes todos
todo_include_todos = True

# Generates auto-summary automatically
autosummary_generate = True

# Create numbers on figures with captions
numfig = True

# If we are on OSX, the 'dvipng' path maybe different
dvipng_osx = pathlib.Path("/Library/TeX/texbin/dvipng")
if dvipng_osx.exists():
    pngmath_dvipng = dvipng_osx

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The main toctree document.
master_doc = "index"

# General information about the project.
project = "clapper"
package = distribution(project)

copyright = f"{time.strftime('%Y')}, Idiap Research Institute"  # noqa: A001

# The short X.Y version.
version = package.version
# The full version, including alpha/beta/rc tags.
release = version

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["links.rst"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"
pygments_dark_style = "monokai"

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []

# Some variables which are useful for generated material
project_variable = project.replace(".", "_")
short_description = package.metadata["Summary"]
owner = ["Idiap Research Institute"]

# -- Options for HTML output ---------------------------------------------------

html_theme = "furo"

html_theme_options = {
    "source_edit_link": f"https://gitlab.idiap.ch/software/{project}/-/edit/main/doc/{{filename}}",
}

html_title = f"{project} {release}"

# -- Post configuration --------------------------------------------------------

# Default processing flags for sphinx
autoclass_content = "class"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

auto_intersphinx_packages = [("python", "3"), "click"]
auto_intersphinx_catalog = "catalog.json"

# Doctest global setup
sphinx_source_dir = pathlib.Path.cwd().resolve()
doctest_global_setup = f"""
import os
data = os.path.join('{sphinx_source_dir}', 'data')
"""
