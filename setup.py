from setuptools import setup

setup(
    name='json_explorer',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'json_explorer=json_explorer:main'
        ]
    }
)