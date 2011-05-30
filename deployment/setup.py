#!/usr/bin/env python
# -*- coding: utf-8 -*-

import distutils.core

distutils.core.setup(
    name="notipy",
    version="0.1",
    description="A minimalistic gtk3 notification daemon written in python.",
    author="Timo Schmiade",
    author_email="the_isz@gmx.de",
    url="https://github.com/the-isz/notipy",
    scripts=["code/notipy.py"]
    )
