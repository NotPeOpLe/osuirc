import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="osuirc", # 
    version="0.0.4",
    author="NotPeOpLe",
    author_email="code840@outlook.com",
    description="專門給osu使用的簡易客戶端",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NotPeOpLe/osuirc",
    license="MIT",
    packages=["osuirc", "osuirc.utils", "osuirc.objects"],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)