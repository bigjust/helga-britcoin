from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name="helga-britcoin",
    version=version,
    description=('HALP'),
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='irc bot britcoin',
    author='Justin Caratzas',
    author_email='bigjust@lambdaphil.es',
    license='LICENSE',
    packages=find_packages(),
    install_requires = (
        'humanize',
    ),
    include_package_data=True,
    py_modules=['helga_britcoin'],
    zip_safe=True,
    entry_points = dict(
        helga_plugins = [
            'britcoin = helga_britcoin:BritCoinPlugin',
        ],
    ),
)
