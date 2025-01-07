"""
Setup script for PubNWR
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pubnwr",
    version="2.0.0",
    author="Dmitri Baughman",
    author_email="dmitri@nowwaveradio.com",
    description="Now Wave Radio's music player automation script",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nowwaveradio/pubnwr",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    install_requires=[
        'pylast>=5.2.0',
        'pylistenbrainz>=0.4.0',
        'facebook-sdk>=3.1.0',
        'atproto>=0.0.1',
        'watchdog>=3.0.0',
        'pytz>=2024.1',
        'requests>=2.31.0',
        'urllib3>=2.0.0',
    ],
    entry_points={
        'console_scripts': [
            'pubnwr=src.main:main',
        ],
    },
    package_data={
        'pubnwr': ['config/*.ini'],
    },
    data_files=[
        ('etc', ['config/pubnwr_MYRIAD.ini']),
    ],
)

