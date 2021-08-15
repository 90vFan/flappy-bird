from setuptools import setup, find_packages
import datetime

VERSION = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

with open('README.md', 'r', encoding="utf8") as f:
    readme = f.read()


setup(
    name='gameai',
    version=VERSION,
    author='Joseph.Fan',
    author_email='',
    description='Game AI',
    long_description=readme,
    url='',
    packages=find_packages(),
    package_dir={'gameai': 'gameai'},
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    extras_require={
        'test': ['pytest']
    },
    python_requires='>=3.6'
)
