from setuptools import setup, find_packages

setup(
    name="python-saber",
    version="0.0.4",
    packages=find_packages(),
    install_requires=[
        'pillow'
    ],
    author="CodeSoft",
    author_email="codesft@proton.me",
    description="A Beat Saber framework written in Python.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/CodeSoftGit/pysaber",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)