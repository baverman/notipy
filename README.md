# notipy #

A minimalistic gtk3 notification daemon written in python.

## Introduction ##

notipy is an implementation of the [Desktop Notification Specification](http://developer.gnome.org/notification-spec/). It shows
message popups using gtk3, allowing for pango marked up message bodies and icons
that can be specified in various ways.

![notipy in action](https://github.com/mrk3004/notipy/raw/master/screen.png)
![Other example](https://github.com/mrk3004/notipy/raw/master/screen2.png)

The design goals of notipy include a minimalistic implementation (following the
unix philosophy "do one thing and do it well") and having as little as possible
dependencies.

## Installation ##

notipy requires the following libraries to work:

* `gtk3`
* `pygobject`
* `dbus-python`
* `libcanberra`

Installation is simply done via:

	./setup.py install [--root=<root dir> --prefix=<prefix dir>]

## Configuration ##

Until now, notipy is configured via command-line arguments or via configuration file (notipy.conf). 

For configuration via command-line options, read notipy --help

For configuration via file, read info in /etc/notipy.conf

## Roadmap ##

* Python3 support
