#!/usr/bin/env python
# Create the virtualenv bootstrap script

prereqs = True
try:
    import virtualenv
except ImportError:
    print "Please install virtualenv (creates local Python environments)"
    print "  http://pypi.python.org/pypi/virtualenv"
    prereqs = False

if not prereqs:
    import sys
    print "Fix these issues and try again"
    sys.exit(1)

import virtualenv, textwrap, os
output = virtualenv.create_bootstrap_script(textwrap.dedent("""
   import os, subprocess
   def after_install(options, home_dir):
       subprocess.call([join(home_dir, 'bin', 'pip'),
           'install', '-r', 'requirements.txt'])
       print "To enter the environment, use:"
       print "source", join(home_dir, 'bin', 'activate')
"""))
f = open('bootstrap.py', 'w').write(output)
os.chmod('bootstrap.py', 0744)
print """To install the virtualenv here, run:
./bootstrap.py .
(the trailing dot is important!)"""

