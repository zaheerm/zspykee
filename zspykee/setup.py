from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(name = "zspykee",
      version = "0.1",
      description = "ZSpykee, Spykee robot control with python",
      long_description = """\
Control your Spykee robot with ZSpykee
""",
      packages = find_packages(),
      package_data = {'zspykee': ['data/*.glade'] },
      install_requires = ['Twisted >= 2.5.0'],
      entry_points = {
        'gui_scripts': [
        'gzspykee = zspykee.app.main',
        ]
      }
)
