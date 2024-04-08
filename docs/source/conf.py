import os

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ReEDS'
copyright = '2024, NREL'
author = 'NREL'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = []

suppress_warnings = [
    'myst.xref_missing',
    'myst.header'
]

# get BASE_URL from environment variable
base_url = os.environ.get('BASE_URL', 'https://github.nrel.gov/ReEDS/ReEDS-2.0')

myst_enable_extensions = [
    "substitution",
]

myst_substitutions = {
    "base_github_url": base_url
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
#html_context = {
#    'display_github': True, 
#    'github_repo': 'ReEDS-2.0', 
#}
html_theme_options = {
    'navigation_depth': 3, 
    'logo_only': True
}

html_context = {
    'base_url': base_url,
}

# html_static_path = ['_static']
html_logo = '../../images/reeds-logo.png'

# More info on the RTD theme configuration can be found at:
# https://github.com/readthedocs/sphinx_rtd_theme/blob/7c9b1b5d391f6d7fae72274393eb25d1df96e546/docs/configuring.rst