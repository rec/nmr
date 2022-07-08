_classifiers = [
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Topic :: Software Development :: Libraries',
    'Topic :: Utilities',
]

if __name__ == '__main__':
    from setuptools import setup
    import nmbr

    setup(
        name='nmbr',
        author='Tom Ritchford',
        author_email='tom@swirly.com',
        classifiers=_classifiers,
        description='A unique name for each number',
        keywords=['Numbers'],
        license='MIT',
        long_description=open('README.rst').read(),
        py_modules=['nmbr'],
        scripts=['nmbr.py'],
        url='https://github.com/rec/nmbr',
        version=nmbr.__version__,
    )
