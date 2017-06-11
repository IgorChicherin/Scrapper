import sys
from cx_Freeze import setup, Executable

base = None

if sys.platform == 'win32':
    base = "Win32GUI"

executables = [Executable("scraper.py", base=base)]

packages = ['idna', 'lxml', 'multiprocessing']
options = {
    'build_exe': {

        'packages': packages,
    },

}

setup(
    name='Scrapper',
    version='',
    packages=[''],
    url='',
    license='',
    author='Igor Chicherin',
    author_email='',
    description='',
    executables=executables,
    options=options
)
