from setuptools import setup, PEP420PackageFinder

setup(
    name="rocketsonde",
    packages=PEP420PackageFinder.find("src"),
    package_dir={"": "src"},
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    install_requires=["psutil"],
    extras_require={"testing": ["pytest"]},
    entry_points={"console_scripts": []},
    zip_safe=False,
    classifiers=[
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Topic :: System :: Monitoring",
    ],
)
