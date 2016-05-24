from setuptools import setup


setup(
    name='sshadduser',
    version='0.5',
    author='Mark E. Haase',
    author_email='mehaase@gmail.com',
    description='1-step to create user with SSH keys',
    license='MIT',
    keywords='open ssh add user authorized keys',
    url='https://github.com/TeamHG-Memex/sshadduser',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities',
    ],
    install_requires=[
        'Click',
    ],
    py_modules=['sshadduser'],
    entry_points='''
        [console_scripts]
        sshadduser=sshadduser:main
    '''
)
