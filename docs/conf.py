# Sphinx basic configuration
import os
import sys

# If you want Sphinx to document your source code (optional)
# sys.path.insert(0, os.path.abspath('..'))

project = 'Medical Register'
copyright = '2025, PumukyDev & Alejandro Quiñones'
author = 'PumukyDev & Alejandro Quiñones'
release = '0.1.0'

# -- General Configuration ---------------------------------------------------

extensions = [
    # Allows Sphinx to interpret Markdown files (.md)
    'myst_parser',
    # Enable Autodoc for documenting Python code (optional)
    'sphinx.ext.autodoc',
    # Support for NumPy and Google style docstrings
    'sphinx.ext.napoleon',
    # Adds links to highlight source code
    'sphinx.ext.viewcode',
]

# Templates path
templates_path = ['_templates']

# The name of the root document (the main documentation file)
root_doc = 'index'

# List of patterns to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Configuration for HTML (including Furo theme) -------------------------

# The theme for HTML documents ('furo' is the modern and clean one you requested)
html_theme = 'furo'

# The directory where static files will be placed
html_static_path = ['_static']

# This is important: list of source documents. 
# The 'Schema.rtf' file will be ignored since it is not .md or .rst.
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# MyST (Markdown) Configuration
myst_enable_extensions = [
    # Allows definition lists (optional)
    "deflist",
    # Allows math environments (optional)
    "amsmath",
    # Allows HTML image tags in Markdown (optional)
    "html_image",
]

# Furo theme configuration (optional)
html_theme_options = {
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#254F6D",
        "color-brand-content": "#254F6D",
    },
}