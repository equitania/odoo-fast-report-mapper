import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoo-fast-report-mapper-equitania",
    version="0.1.23",
    author="Equitania Software GmbH",
    author_email="info@equitania.de",
    description="A package to create FastReport entries in Odoo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/equitania/odoo-fast-report-mapper",
    packages=['odoo_fast_report_mapper', 'odoo_report_helper'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points='''
    [console_scripts]
    odoo-fr-mapper=odoo_fast_report_mapper.odoo_fast_report_mapper:start_odoo_fast_report_mapper
    ''',
    install_requires=[
        'OdooRPC>=0.9.0',
        'click>=8.1.3',
        'PyYaml>=5.4.1'
    ]
)
