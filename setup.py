import setuptools
import os
from pathlib import Path

# Read version from __version__.py
def get_version():
    """Read version from __version__.py file"""
    version_file = Path(__file__).parent / "odoo_fast_report_mapper" / "__version__.py"
    version_dict = {}
    with open(version_file, "r", encoding="utf-8") as f:
        exec(f.read(), version_dict)
    return version_dict["__version__"]

# Read README file for long description
def read_readme():
    """Read README.md file with proper encoding"""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    try:
        with open(readme_path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "A Python library for creating, managing, and testing FastReport entries in Odoo environments."

long_description = read_readme()

setuptools.setup(
    name="odoo-fast-report-mapper-equitania",
    version=get_version(),
    author="Equitania Software GmbH",
    author_email="info@equitania.de",
    description="A Python library for creating, managing, and testing FastReport entries in Odoo environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/equitania/odoo-fast-report-mapper",
    project_urls={
        "Bug Reports": "https://github.com/equitania/odoo-fast-report-mapper/issues",
        "Source": "https://github.com/equitania/odoo-fast-report-mapper",
        "Documentation": "https://www.ownerp.com/odoo-fastreport",
        "Company": "https://www.equitania.de",
    },
    packages=['odoo_fast_report_mapper', 'odoo_report_helper'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Natural Language :: English",
        "Natural Language :: German",
    ],
    keywords="odoo, fastreport, report, pdf, generator, yaml, mapping, cli",
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'odoo-fast-report-mapper=odoo_fast_report_mapper.odoo_fast_report_mapper:start_odoo_fast_report_mapper',
            'odoo-fr-mapper=odoo_fast_report_mapper.odoo_fast_report_mapper:start_odoo_fast_report_mapper',
        ],
    },
    install_requires=[
        'OdooRPC>=0.10.1',
        'click>=8.1.3',
        'PyYaml>=5.4.1',
        'tqdm>=4.65.0',
        'python-dotenv>=0.19.0'
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=22.0',
            'flake8>=4.0',
            'mypy>=0.910',
            'twine>=4.0',
        ],
        'test': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
