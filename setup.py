from distutils.core import setup

setup(
    name='Python-EPP',
    version='0.1.0',
    author='Jochem Oosterveen',
    author_email='jochem@oosterveen.net',
    packages=['EPP'],
    description='Python EPP client',
    long_description=(
        "Python-EPP provides an interface to the Extensible Provisioning"
        "Protocol (EPP), which is being used for communication between domain"
        "name registries and domain name registrars."
    ),
    install_requires=[
        "BeautifulSoup >= 3.2.1",
    ],
)
