from setuptools import setup

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='sqlalchemy-multidb',
    version='1.0.2',
    packages=['sqlalchemy_multidb'],
    url='https://github.com/viniciuschiele/sqlalchemy-multidb',
    license='MIT',
    author='Vinicius Chiele',
    author_email='vinicius.chiele@gmail.com',
    description='Provides methods to load the database configurations from a config object and access multiple databases easily.',
    long_description=long_description,
    keywords=['sqlalchemy'],
    install_requires=['sqlalchemy>=1.0.0'],
    classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
