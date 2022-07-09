from setuptools import setup

setup(
    name='hashbak',
    package='./hashbak',
    install_requires=[
        'boto3',
        'cryptography',
    ],
    entry_points={
        'console_scripts': [
            'hashbak = hashbak.cli:main',
        ],
    },
)
