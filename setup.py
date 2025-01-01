from setuptools import setup, find_packages


def read_requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()


setup(
    name='news-scraper-pdf',
    version='1.1.4',
    description='Scrape news as PDF.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=read_requirements(),
    license='MIT',
    author='pressomaniac',
    entry_points={
        'console_scripts': [
            'news-scraper-pdf = src.get_edition:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
