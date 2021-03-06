# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
# sys.path.insert(0, os.path.abspath('.'))

sys.path.insert(0, os.path.abspath(os.pardir))


# -- Project information -----------------------------------------------------

project = 'Test'
copyright = '2020, Marco Koch'
author = 'Marco Koch'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_ext.cmake_domain"
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# A boolean that decides whether parentheses are appended to function and method
# role text (e.g. the content of :func:`input`) to signify that the name is
# callable. Default is True.
add_function_parentheses = True


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# If true, the reST sources are included in the HTML build as _sources/name.
# The default is True.
html_copy_source = False

# If true (and html_copy_source is true as well), links to the reST sources will
# be added to the sidebar. The default is True.
html_show_sourcelink = False


# -- Options for sphinx_ext.cmake_domain -------------------------------------

# A list of prefixes that will be ignored when sorting CMake objects in an index
cmake_index_common_prefix = ["MY_", "my_"]

# Show the `.cmake` file extension after module names. Default is False.
cmake_modules_add_extension = True
