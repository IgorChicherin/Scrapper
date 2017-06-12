import sys
from cx_Freeze import setup, Executable

base = None

if sys.platform == 'win32':
    base = "Win32GUI"

executables = [Executable("scraper.py", base='Win32GUI')]

packages = ['idna', 'lxml', 'multiprocessing', 'time', 'sys']
options = {
    'build_exe': {

        'packages': packages,
    },

}

setup(
    name='Scrapper',
    version='1.0',
    packages=[''],
    url='',
    license='',
    author='Igor Chicherin',
    author_email='',
    description='',
    executables=executables,
    options=options
)
