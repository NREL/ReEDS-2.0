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
    'sphinxcontrib.bibtex',
]

bibtex_bibfiles = ['references.bib'] # exported from zotero using better bibtex
bibtex_reference_style = 'author_year'

templates_path = ['_templates']
exclude_patterns = []

suppress_warnings = [
    'myst.xref_missing',
    'myst.header'
]

numfig = True # auto number figures when true

# get GAMSLICE from environment variable
gamslice_secret = os.getenv('GAMSLICE', '')

# get BASE_URL from environment variable
base_url = os.environ.get('BASE_URL', 'https://github.nrel.gov/ReEDS/ReEDS-2.0')
github_releases_url = base_url + '/releases'

myst_enable_extensions = [
    "substitution",
    "dollarmath",
]

myst_substitutions = {
    "base_github_url": base_url,
    "github_releases_url": github_releases_url,
    "gamslice": gamslice_secret
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    'navigation_depth': 3, 
    'logo_only': True
}

html_context = {
    'base_url': base_url,
}

html_logo = '../../images/reeds-logo.png'

# More info on the RTD theme configuration can be found at:
# https://github.com/readthedocs/sphinx_rtd_theme/blob/7c9b1b5d391f6d7fae72274393eb25d1df96e546/docs/configuring.rst