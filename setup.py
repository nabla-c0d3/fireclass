from setuptools import setup, find_packages
from fireclass import __version__
from fireclass import __author__
from fireclass import __email__


setup(
    name="fireclass",
    version=__version__,
    description="Firestore + Dataclass: declare and interact with your Firestore models using dataclasses.",
    python_requires='>=3.7',
    author=__author__,
    author_email=__email__,
    url="https://github.com/nabla-c0d3/fireclass",
    packages=find_packages(exclude=["docs", "tests"]),
    install_requires=[
        'google-cloud-firestore<1.3.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='dataclasses firestore google-cloud',
    project_urls={
        'Source': 'https://github.com/nabla-c0d3/firestore',
    },
)
