from setuptools import setup, find_packages

setup(
    name="fileorganizer",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'fileorganizer=fileorganizer.cli:main',
        ],
    },
    author="XucroYuri",
    author_email="example@example.com",
    description="智能文件整理助手",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/XucroYuri/FileOrganizer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)