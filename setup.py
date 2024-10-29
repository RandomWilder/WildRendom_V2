from setuptools import setup, find_packages

setup(
    name='wildrandom',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-migrate',
        'marshmallow',
        'pytest',
        'pyjwt'
    ],
)