#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name="notipy-fork",
    version="0.3.0",
    description="A minimalistic gtk3 notification daemon written in python.",
    author="Vinycius Maia",
    author_email="suportevg@uol.com.br",
    license="GPLv3",
    url="https://github.com/mrk3004/notipy/",
    scripts=["notipy"],
    data_files=[("/etc", ["notipy.conf"])]
    )
