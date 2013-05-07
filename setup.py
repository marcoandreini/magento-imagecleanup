#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='magento-imagecleanup',
      version='0.1',
      description='Magento Image Cleanup',
      author='Marco Andreini',
      author_email='marco.andreini@gmail.com',
      url='https://github.com/marcoandreini/magento-imagecleanup',
      license = 'GPL',
      keywords = 'magento image cleanup',
      packages = find_packages(),
      scripts = ['src/magentoimagecleanup.py'],
      install_requires=['MySQL-python']
     )
