#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus
import time

def main():
    sessionBus = dbus.SessionBus()
    notificationDaemon = \
            sessionBus.get_object(
                    "org.freedesktop.Notifications",
                    "/org/freedesktop/Notifications")
    ndIFace = dbus.Interface(
            notificationDaemon,
            "org.freedesktop.Notifications")

    ndIFace.Notify("test", 0, "info", "sum1", "body1", "", "", 10000)
    secondId = ndIFace.Notify("test", 0, "info", "sum2", "body2", "", "", 10000)
    ndIFace.Notify("test", 0, "info", "sum3", "body3", "", "", 10000)

    time.sleep(5)

    retId = ndIFace.Notify("test", secondId, "error", "woo", "hoo", "", "", 3000)

    assert(secondId == retId)

    time.sleep(4)

    ndIFace.Notify("test", secondId, "info", "honka", "hey", "", "", 3000)

if __name__ == '__main__':
  main()
