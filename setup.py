from setuptools import setup, find_packages

setup(
    name="SisOvos",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-migrate',
        'flask-login',
        'flask-wtf',
        'flask-mail',
        'python-dotenv',
        'email-validator',
        'blinker',
    ],
    python_requires='>=3.6',
)
