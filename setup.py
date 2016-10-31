import subprocess

from setuptools import setup

try:
    git_ref = subprocess.check_output(['git', 'rev-parse', '--verify', '--short', 'HEAD']).decode().rstrip()
except:
    git_ref = '?'

setup(
    name = 'igd-exporter',
    version = '0+g{}'.format(git_ref),
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
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Monitoring',
    ],
    keywords = 'prometheus monitoring upnp igd',
    packages = ['igd_exporter'],
    install_requires = ['prometheus_client'],
    entry_points = {
        'console_scripts': [
            'igd-exporter = igd_exporter.__main__:main',
        ],
    },
)
