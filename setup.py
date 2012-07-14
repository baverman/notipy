#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name="notipy-fork-fork",
    version="0.5.0",
    description="A minimalistic gtk3 notification daemon written in python.",
    author="Anton Bobrov",
    author_email="bobrov@vl.ru",
    license="GPLv3",
    url="https://github.com/baverman/notipy/",
    scripts=["notipy"],
    data_files=[("/usr/share/notipy", ["notipyrc"])]
)
