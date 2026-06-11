from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="autoextract",
    version="2.0.0",
    author="pratham2402",
    author_email="pratham2402@users.noreply.github.com",
    description="Automated multi-format archive extraction daemon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pratham2402/AutoExtract",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Archiving",
        "Topic :: Utilities",
    ],
    python_requires=">=3.10",
    install_requires=[
        "watchdog>=6.0.0",
        "PyYAML>=6.0",
        "requests>=2.31.0",
        "rarfile>=4.1",
        "py7zr>=0.21.0",
        "send2trash>=1.8.0",
        "rich>=13.0.0",
        "questionary>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "autoextract=autoextract.__main__:entry",
        ],
    },
)
