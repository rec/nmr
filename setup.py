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

    VERS = '__version__'

    with open('nmbr.py') as fp:
        for line in fp:
            if line.startswith(VERS):
                vers, equals, version = line.strip().split()
                assert vers == VERS
                assert equals == '='
                assert version[0] == version[-1] == "'"
                version = version[1:-1]
                break
        else:
            assert False

    with open('requirements.txt') as f:
        required = f.read().splitlines()

    setup(
        name='nmbr',
        author='Tom Ritchford',
        author_email='tom@swirly.com',
        classifiers=_classifiers,
        data_files=[('.', ['words.txt'])],
        description='A unique name for each number',
        install_requires=required,
        keywords=['Numbers'],
        license='MIT',
        long_description=open('README.rst').read(),
        py_modules=['nmbr'],
        scripts=['nmbr.py'],
        url='https://github.com/rec/nmbr',
        version=version,
    )
