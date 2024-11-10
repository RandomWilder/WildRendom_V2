from setuptools import setup, find_packages

setup(
    name='wildRandom',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-migrate',
        'marshmallow',
        'sqlalchemy',
        'alembic',
        'pytest',
        'pyjwt'
    ],
)