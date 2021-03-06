from setuptools import setup, find_packages
import sys
import os

version = '1.0'

requires = [
    'pyyaml',
    'datadog',
]

test_requires = requires + [
    'coverage',
    'python-coveralls',
    'mock',
    'munch',
    'nose',
]

setup(name='statsdhandler',
      version=version,
      description='Python logging handler for generate metrics and publish '
      'to statsite',
      long_description="""\
""",
      classifiers=[
          "Programming Language :: Python",
      ],
      keywords='',
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      test_requires=test_requires,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
