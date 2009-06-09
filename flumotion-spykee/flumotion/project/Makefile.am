include $(top_srcdir)/common/python.mk
include $(top_srcdir)/common/locale.mk

flumotiondir = $(libdir)/flumotion/python/flumotion/project

flumotion_PYTHON = spykee.py
flumotion_DATA = spykee.locale.xml

clean-local:
	rm -f *.pyc *.pyo

PROJECT = spykee

BUILT_SOURCES = spykee.py spykee.locale.xml
CLEANFILES = $(BUILT_SOURCES)

EXTRA_DIST = spykee.py.in
