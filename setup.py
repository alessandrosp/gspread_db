import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gspread_db",
    version="1.1",
    author="Alessandro Scoccia Pappagallo",
    author_email="aless@ndro.xyz",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    description="A database-like interface for gspread.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=['pandas', 'gspread'],
    keywords='database google spreadsheets',
    packages=setuptools.find_packages(),
    url="https://github.com/annoys-parrot/gspread_db",
)
