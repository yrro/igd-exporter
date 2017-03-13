import os
import subprocess

from setuptools import setup

# Prefer to use the version from the Debian package. Fall back to the version
# from git. This way the .git directory does not have to be included in the
# Debian source package.
if os.path.exists('debian/changelog'):
    for line in subprocess.check_output(['dpkg-parsechangelog']).decode().split('\n'):
        tokens = line.split()
        if tokens[0] == 'Version:':
            version = tokens[1]
            break
else:
    build_no = os.environ.get('BUILD_NUMBER', '0')
    git_ref = subprocess.check_output(['git', 'rev-parse', '--verify', '--short', 'HEAD']).decode().rstrip()
    version = '0.dev{}+g{}'.format(build_no, git_ref)

setup(
    name = 'igd-exporter',
    version = version,
    description = 'Prometheus exporter for UPnP Internet Gateway Device metrics',
    url = 'https://github.com/yrro/igd-exporter',
    author = 'Sam Morris',
    author_email = 'sam@robots.org.uk',
    license = 'MIT',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Environment :: No Input/Output (Daemon)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: System :: Monitoring',
    ],
    keywords = 'prometheus monitoring upnp igd',
    packages = ['igd_exporter'],
    install_requires = [
        'prometheus_client',
        'setuptools'
    ],
    entry_points = {
        'console_scripts': [
            'igd-exporter = igd_exporter:main',
        ],
    },
)
