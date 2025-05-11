from setuptools import find_packages, setup

setup(
    name="Backend API for AES",
    version="0.1.0",
    author="Maxim Andreyko",
    author_email="max_andreyko@mail.ru",
    description="Backend API for Automated Essay Scoring with Feedback. Serves prediction endpoints for web services",
    packages=find_packages(include=["src", "src.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
