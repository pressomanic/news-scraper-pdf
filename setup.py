from setuptools import setup, find_packages


def read_requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()


setup(
    name='news-scraper',
    version='0.0.1',
    packages=find_packages(),
    install_requires=read_requirements(),
    license='MIT',
    author='',
    description='',
    entry_points={
        'console_scripts': [
            'news-scraper = src.get_edition:main'
        ]
    }
)
