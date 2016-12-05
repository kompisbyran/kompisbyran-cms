import imp
import os
import sys

sys.path.insert(0, os.path.dirname(__file__) + 'src/')

wsgi = imp.load_source('wsgi', 'src/app.py')
application = wsgi.app
