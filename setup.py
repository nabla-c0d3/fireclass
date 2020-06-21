from pathlib import Path
from typing import Dict

from setuptools import setup, find_packages

root_path = Path(__file__).absolute().parent


def _get_long_description():
    readme_path = root_path / "README.md"
    return readme_path.read_text()


def get_project_info() -> Dict[str, str]:
    proj_info: Dict[str, str] = {}
    proj_info_path = root_path / "fireclass" / "__version__.py"
    exec(proj_info_path.read_text(), proj_info)
    return proj_info


project_info = get_project_info()


setup(
    name="fireclass",
    version=project_info["__version__"],
    description="Firestore + Dataclass: declare and interact with your Firestore models using dataclasses.",
    long_description=_get_long_description(),
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    author=project_info["__author__"],
    author_email=project_info["__email__"],
    url="https://github.com/nabla-c0d3/fireclass",
    packages=find_packages(exclude=["docs", "tests"]),
    install_requires=["google-cloud-firestore<1.8.0", "typing-extensions"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="dataclasses firestore google-cloud google-cloud-platform orm",
    project_urls={"Source": "https://github.com/nabla-c0d3/fireclass"},
)
