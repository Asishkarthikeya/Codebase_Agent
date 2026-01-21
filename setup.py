# Work-around the fact that `pip install -e .` doesn't work with `pyproject.toml` files.
from setuptools import setup

setup(
    name="code_chatbot",
    version="0.1.0",
    packages=["code_chatbot", "api"],
    install_requires=[
        "streamlit",
        "langchain",
        "chromadb",
        "networkx",
        "tree-sitter",
    ],
)
