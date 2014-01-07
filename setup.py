#!/usr/bin/env python

from distutils.core import setup

setup(
      name = 'multitail2'
   ,  version = '1.0.0'
   ,  description = 'Enables following multiple files for new lines at once, automatically handling file creation/deletion/rotation'
   ,  long_description = """Accepts a glob spec like '/var/log/*.log' and \
adds/removes/reopens files as they are created, deleted, and rotated."""
   ,  author = 'Derp Ston'
   ,  author_email = 'derpston+pypi@sleepygeek.org'
   ,  url = 'https://github.com/derpston/python-multitail2'
   ,  packages = ['']
   ,  package_dir = {'': 'src'}
   )

