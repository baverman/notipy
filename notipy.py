#!/usr/bin/env python
# -*- coding: utf-8 -*-

# depends on pygobject (or glib2?), dbus-python

# http://developer.gnome.org/notification-spec/

import dbus.mainloop.glib
import dbus.service
import dbus
import gobject


class NotificationDaemon(dbus.service.Object):
  def __init__(self, objectPath):
    bus_name = dbus.service.BusName("org.freedesktop.Notifications", dbus.SessionBus())
    dbus.service.Object.__init__(self, bus_name, objectPath)

    self.__lastID = 0


  @dbus.service.method(
      dbus_interface = "org.freedesktop.Notifications",
      in_signature = "",
      out_signature = "as")
  def GetCapabilities(self):
    """
    "action-icons"
    "actions"
    "body"
    "body-hyperlinks"
    "body-images"
    "body-markup"
    "icon-multi"
    "icon-static"
    "persistence"
    "sound"

    @returns: An array of strings
    """
    return ["body"]


  @dbus.service.method(
      dbus_interface = "org.freedesktop.Notifications",
      in_signature = "susssava{sv}i",
      out_signature = "u")
  def Notify(
      self, app_name, replaces_id, app_icon, summary,
      body, actions, hints, expire_timeout):
    """
    @param app_name: string
    @param replaces_id: unsigned int
    @param app_icon: string
    @param summary: string
    @param body: string
    @param actions: array (even: id (int), odd: localized string)
    @param hints: dict
    @param expire_timeout: int

    @returns: unsigned int
    """
    print("sum: {}\nbod: {}".format(summary, body))
    self.__lastID += 1
    return self.__lastID


  @dbus.service.method(
      dbus_interface = "org.freedesktop.Notifications",
      in_signature = "u",
      out_signature = "")
  def CloseNotification(self, id):
    """
    NotificationClosed signal or empty D-BUS error
    @param id: unsigned int
    """
    self.NotificationClosed(id)


  @dbus.service.method(
      dbus_interface = "org.freedesktop.Notifications",
      in_signature = "",
      out_signature = "ssss")
  def GetServerInformation(self):
    """
    @returns: a tuple containing the server name, the vendor name, the server
              version and the supported protocol version.
    """
    return ("Notifications", "freedesktop.org", "0.1", "0.7.1")

  # Signals

  @dbus.service.signal(
      dbus_interface = "org.freedesktop.Notifications",
      signature = "uu")
  def NotificationClosed(self, id, reason):
    """
    @param id: unsigned int
    @param reason: unsigned int
    """
    pass


  @dbus.service.signal(
      dbus_interface = "org.freedesktop.Notifications",
      signature = "us")
  def ActionInvoked(self, id, action_key):
    """
    @param id: unsigned int
    @param action_key: string
    """
    pass


def main():
  dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

  #signalMatch = .add_signal_handler(
  #    handler_func,
  #    "signal name" or None for all,
  #    dbus_interface or None for all interfaces,
  #    sender_bus_name or None for all senders,
  #    sender_object_path or None for all paths)

  loop = gobject.MainLoop()

  notDaemon = NotificationDaemon("/org/freedesktop/Notifications")

  try:
    loop.run()
  except KeyboardInterrupt:
    print("Exiting.")

  #print("Removing")
  #signalMatch.remove()


if __name__ == '__main__':
  main()
