from setuptools import setup, find_packages

setup(
    name='glotter2',
    version='0.3.0',
    entry_points={'console_scripts': ['glotter = glotter.__main__:main']},
    packages=find_packages(exclude=('test',)),
    install_requires=[
        'docker>=6.0.1, <7',
        'Jinja2>=3.1.2, <4',
        'pytest>=7.2.1, <8',
        'PyYAML>=6.0, <7'
    ],
    python_requires='>=3.8',
)
