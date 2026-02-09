from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ticket2pr",
    version="0.3.10",
    author="Ben Gabay",
    author_email="ben.gabay38@gmail.com",
    description="Automate Jira ticket to GitHub PR workflow",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bengabay11/ticket2pr",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "claude-agent-sdk>=0.1.25",
        "colorlog>=6.9.0",
        "gitpython>=3.1.46",
        "jira>=3.10.5",
        "pydantic>=2.11.5",
        "pydantic-settings[toml]>=2.9.1",
        "pygithub>=2.8.1",
        "python-dotenv>=1.1.0",
        "rich>=14.0.0",
        "tomli-w>=1.2.0",
        "typing_extensions>=4.0.0",
        "typer>=0.21.1",
    ],
    extras_require={
        "dev": [
            "absolufy-imports>=0.3.1",
            "bandit>=1.8.3",
            "codespell>=2.4.1",
            "mypy>=1.16.0",
            "pre-commit>=4.2.0",
            "pytest>=8.3.5",
            "pytest-cases>=3.8.6",
            "ruff>=0.11.12",
        ],
    },
    entry_points={
        "console_scripts": [
            "ticket2pr=src.cli:cli_main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
