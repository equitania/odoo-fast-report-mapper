import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoo-fast-report-mapper-equitania",
    version="0.0.7",
    author="Lukas von Ehr - Equitania Software GmbH",
    author_email="l.von.ehr@equitania.de",
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
    python_requires='>=3.6',
    entry_points='''
    [console_scripts]
    odoo-fr-mapper=odoo_fast_report_mapper.odoo_fast_report_mapper:start_odoo_fast_report_mapper
    ''',
    install_requires=[
        'click>=7.1.2',
        'OdooRPC>=0.7.0',
        'PyYaml>=3.12'
    ]
)