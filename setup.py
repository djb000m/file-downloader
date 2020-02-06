from setuptools import setup

setup(
    name="download-files",
    version="0.1",
    author="djb000m",
    description=(
        "A little tool to download all files of a specified type from a supplied url"
    ),
    py_modules=["file_downloader"],
    install_requires=[
        "colorama; platform_system=='Windows'",  # Colorama is only required for Windows.
        "click",
        "requests",
        "bs4",
        "lxml",
    ],
    entry_points="""
        [console_scripts]
        download-files=file_downloader:cli
    """,
)
