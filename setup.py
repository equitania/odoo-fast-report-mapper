import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoo-fast-report-mapper-YOUR-USERNAME-HERE",
    version="0.0.1",
    author="Lukas von Ehr - Equitania Software GmbH",
    author_email="l.von.ehr@equitania.de",
    description="A package to create FastReport entries in Odoo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=['odoo_fast_report_mapper', 'odoo_report_helper'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)