from setuptools import setup

setup(
    name='certbot_namecheap',
    package='./certbot_namecheap.py',
    install_requires=[
        'certbot',
        'dnspython'
    ],
    entry_points={
        'certbot.plugins': [
            'auth=certbot_namecheap:Authenticator',
        ],
    },
)