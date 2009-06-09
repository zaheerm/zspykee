include $(top_srcdir)/common/python.mk

component_PYTHON = __init__.py spykee.py twistedprotocol.py
componentdir = $(libdir)/flumotion/python/flumotion/component/spykee
component_DATA = \
	spykee.xml

clean-local:
	rm -rf *.pyc *.pyo

EXTRA_DIST = $(component_DATA)
