from setuptools import setup, find_packages
import os

from glustik import __version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='glustik',
        version=__version__,
        packages=find_packages(),
        package_data={'':['examples/*']},
        author='Lee Trout',
        author_email='leetrout@gmail.com',
        url='https://github.com/leetrout/glustik',
        long_description=read('README.md'),
    )

