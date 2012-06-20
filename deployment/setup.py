#!/usr/bin/env python
# -*- coding: utf-8 -*-

import distutils.core

distutils.core.setup(
    name="notipy-fork",
    version="0.3.0",
    description="A minimalistic gtk3 notification daemon written in python.",
    author="Vinycius Maia",
    author_email="suportevg@uol.com.br",
    url="https://github.com/mrk3004/notipy/",
    scripts=["code/notipy.py"]
    )
