# PySaber
A Beat Saber framework written in Python.

## Features
### Compression
Significantly reduce your wall/geo count without losing quality when generating text!
### TTF Font Support
Load TTF files to use any font you want. Arial? Comic Sans? Ghostly Panic? If it's a TTF file, it should work!
### Customizable Text Generation
Generate text with customizable parameters including color, position, scale, depth, and track.
### Geometric Text Generation
Generate text using Chroma Geometry with customizable materials and shaders.
### Difficulty Management
Easily manage and modify beatmaps using the `Beatmap` and `Difficulty` classes.
### Multi-Language Support
Generate text in multiple languages with Unicode support.
### Custom Data Modification & Preservation
PySaber preserves your CustomData, and allows modification.

## Installation
To install PySaber, use pip:

```sh
pip install python-saber
```

Alternatively, you can install PySaber by cloning the repository and using `setup.py`:

```sh
git clone https://github.com/CodeSoftGit/pysaber.git
cd pysaber
python setup.py install
```