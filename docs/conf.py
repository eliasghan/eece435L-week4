import os
import sys

sys.path.insert(0, os.path.abspath('..'))

project = 'School Management System'
copyright = '2026, Elias Ghanem'
author = 'Elias Ghanem'

version = '1.0'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'en'

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
