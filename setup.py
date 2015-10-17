from setuptools import setup, find_packages
setup(
    name='gCoin-python',
    version='0.1',
    description='Friendly gCoin Auto Test and Edge Test API binding for Python',
    long_description='This package is composed of Auto Test and Edge Test.'
    ' Auto Test allows performing commands such as voting to other alliances in order to'
    ' deploy multiple testing nodes. Edge Test using python scripts to call bitcoin-rpc via shell.',
    maintainer='Sig',
    maintainer_email='sigurrosss159@gmail.com',
    url='https://github.com/sigshen/gcoin-test.git',
    packages=find_packages("src"),
    package_dir={'': 'src'},
    install_requires=[
        'Fabric==1.10.2',
    ]
)
