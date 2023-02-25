from setuptools import setup

setup(
    name='glotter2',
    description='An execution library for scripts written in any language. This is a fork of auroq/glotter',
    version='0.3.0',
    author='auroq',
    maintainer='rzuckerm',
    url='https://github.com/rzuckerm/glotter2',
    entry_points={'console_scripts': ['glotter = glotter.__main__:main']},
    packages=['glotter'],
    install_requires=[
        'docker>=6.0.1, <7',
        'Jinja2>=3.1.2, <4',
        'pytest>=7.2.1, <8',
        'PyYAML>=6.0, <7'
    ],
    license='MIT License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only'
    ],
    python_requires='>=3.8',
)
