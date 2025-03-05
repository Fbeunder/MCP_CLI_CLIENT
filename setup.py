from setuptools import setup, find_packages

setup(
    name="mcp_cli_client",
    version="0.1.0",
    description="Een Python client voor het werken met MCP (Machine Communication Protocol) servers",
    author="Fbeunder",
    author_email="",
    url="https://github.com/Fbeunder/MCP_CLI_CLIENT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "mcp-cli=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
)
