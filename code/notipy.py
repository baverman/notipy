#!/usr/bin/env python
# -*- coding: utf-8 -*-

# depends on pygobject (or glib2?), dbus-python, gtk2 ?

import dbus.mainloop.glib
import dbus.service
import dbus
import gobject

from gi.repository import Gtk, Gdk

import collections
import itertools
import operator
import argparse
import logging
import warnings

# This is worth its weight in gold! Conversion from classic gtk to gobject stuff
# http://git.gnome.org/browse/pygobject/tree/pygi-convert.sh

class LayoutAnchor:
  NORTH_WEST, SOUTH_WEST, SOUTH_EAST, NORTH_EAST = range(4)


class LayoutDirection:
  VERTICAL, HORIZONTAL = range(2)


class Layout:
  @staticmethod
  def layout_north_west(margins, windows, direction):
    base = (Gdk.Screen.width() - margins[1], margins[0])

    for win in windows.itervalues():
      win.move(base[0] - win.get_size()[0], base[1])
      if direction == LayoutDirection.VERTICAL:
        base = (base[0]                    , base[1] + win.get_size()[1])
      else:
        base = (base[0] - win.get_size()[0], base[1])


  @staticmethod
  def layout_south_west(margins, windows, direction):
    base = (Gdk.Screen.width() - margins[1], Gdk.Screen.height() - margins[2])

    for win in windows.itervalues():
      win.move(base[0] - win.get_size()[0], base[1] - win.get_size()[1])
      if direction == LayoutDirection.VERTICAL:
        base = (base[0]                    , base[1] - win.get_size()[1])
      else:
        base = (base[0] - win.get_size()[0], base[1])


  @staticmethod
  def layout_south_east(margins, windows, direction):
    base = (margins[3], Gdk.Screen.height() - margins[2])

    for win in windows.itervalues():
      win.move(base[0]                    , base[1] - win.get_size()[1])
      if direction == LayoutDirection.VERTICAL:
        base = (base[0]                    , base[1] - win.get_size()[1])
      else:
        base = (base[0] + win.get_size()[0], base[1])


  @staticmethod
  def layout_north_east(margins, windows, direction):
    base = (margins[3], margins[0])

    for win in windows.itervalues():
      win.move(base[0], base[1])
      if direction == LayoutDirection.VERTICAL:
        base = (base[0]                    , base[1] + win.get_size()[1])
      else:
        base = (base[0] + win.get_size()[0], base[1])


class NotificationDaemon(dbus.service.Object):
  """
  Implements the gnome Desktop Notification Specification [1] to display popup
  information.

  [1] http://developer.gnome.org/notification-spec/
  """

  def __init__(self, objectPath):
    bus_name = dbus.service.BusName("org.freedesktop.Notifications", dbus.SessionBus())
    dbus.service.Object.__init__(self, bus_name, objectPath)

    self.__lastID = 0
    self.__windows = collections.OrderedDict()
    self.max_expire_timeout = 10000
    self.margins = [0 for x in range(4)]
    self.layoutAnchor = LayoutAnchor.NORTH_WEST
    self.layoutDirection = LayoutDirection.VERTICAL


  def set_max_expire_timeout(self, max_expire_timeout):
    if max_expire_timeout < 1:
      warnings.warn("Ignoring max_expire_timeout value < 1.")
      return
    self.__max_expire_timeout = max_expire_timeout


  def max_expire_timeout(self):
    return self.__max_expire_timeout


  max_expire_timeout = property(max_expire_timeout, set_max_expire_timeout, \
      doc = "Maximum time for notifications to be shown in [ms]. "
            "Default: 10000.")


  def set_margins(self, margins):
    try:
      newMargins = [int(x) for x in itertools.islice(margins, 4)]
      self.__margins = newMargins
    except ValueError:
      warnings.warn(
          "Ignoring margins value because not all values could be converted to"
          " integer values.")
    except TypeError:
      warnings.warn("Ignoring margins value because it is not subscriptable.")
    except IndexError:
      warnings.warn("Ignoring margins value because it doesn't have enough values.")


  def margins(self):
    return self.__margins


  margins = property(margins, set_margins,
      doc = "Margins for top, right, bottom and left side of the screen.")


  def set_layout_anchor(self, layoutAnchor):
    try:
      self.__layoutAnchorFunc = \
          {
              LayoutAnchor.NORTH_WEST : Layout.layout_north_west,
              LayoutAnchor.SOUTH_WEST : Layout.layout_south_west,
              LayoutAnchor.SOUTH_EAST : Layout.layout_south_east,
              LayoutAnchor.NORTH_EAST : Layout.layout_north_east,
          }[layoutAnchor]
    except KeyError:
      warnings.warn("Ignoring invalid layoutAnchor setting.")
      return

    self.__layoutAnchor = layoutAnchor


  def layout_anchor(self):
    return self.__layoutAnchor


  layoutAnchor = property(layout_anchor, set_layout_anchor,
      doc = "Layout origin for the notification windows.")


  def set_layout_direction(self, layoutDirection):
    if layoutDirection not in \
        [LayoutDirection.VERTICAL, LayoutDirection.HORIZONTAL]:
      warnings.warn("Ignoring invalid layoutDirection setting.")
      return

    self.__layoutDirection = layoutDirection


  def layout_direction(self):
    return self.__layoutDirection


  layoutDirection = property(layout_direction, set_layout_direction,
      doc = "Layout direction for the notification windows.")


  def __update_layout(self):
    """
    Recalculates the layout of all notification windows.
    """
    self.__layoutAnchorFunc(self.margins, self.__windows, self.layoutDirection)


  def __create_win(self, summary, body):
    win = Gtk.Window(type = Gtk.WindowType.POPUP)

    frame = Gtk.Frame()
    win.add(frame)

    vBox = Gtk.VBox()
    frame.add(vBox)

    summaryLabel = Gtk.Label(label = summary)
    vBox.pack_start_defaults(summaryLabel)

    separator = Gtk.HSeparator()
    vBox.pack_start_defaults(separator)

    bodyLabel = Gtk.Label()
    bodyLabel.set_markup(str(body))
    vBox.pack_start_defaults(bodyLabel)

    # The window's size has default values before showing it.
    win.show_all()

    return win


  def __notification_expired(self, id):
    """
    Callback called when a notification expired.

    @param id: the ID of the notification.
    @returns: False
    """
    self.__close_notification(id, 1)
    return False # Don't repeat timeout


  def __window_clicked(self, widget, event, id):
    self.__close_notification(id, 2)


  def __close_notification(self, id, reason):
    """
    Closes a notification and emits NotificationClosed if the notification
    exists.

    @param id: the ID of the notification.
    @param reason: the reason for closing the notification.
    @returns: True if a notification with this id existed, False otherwise.
    """
    if id in self.__windows:
      win = self.__windows.pop(id)
      win.hide_all()
      win.destroy()
      self.__update_layout()
      self.NotificationClosed(id, reason)
      return True
    else:
      # Silently ignore. This will (correctly) happen every time the user clicks
      # a non-0 timeout notification to get rid of it, as the respective timeout
      # will still trigger.
      return False


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
    return ["body", "body-markup", "persistence"]


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
    logging.debug("summary: \"{}\", body: \"{}\"".format(summary, body))
    self.__lastID += 1
    logging.debug("Notification ID: {}".format(self.__lastID))

    # FIXME: Implement handling of replaces_id.

    try:
      win = self.__create_win(summary, body)
      win.window.set_events(
          win.window.get_events() | Gdk.EventMask.BUTTON_PRESS_MASK)
      win.connect("button-press-event", self.__window_clicked, self.__lastID)
      self.__windows[self.__lastID] = win
      self.__update_layout()

      if 0 != expire_timeout:
        timeout = \
            (self.max_expire_timeout if -1 == expire_timeout else \
            min(expire_timeout, self.max_expire_timeout)) / 1000

        logging.debug("Will close notification {} after {} seconds.".format(
          self.__lastID, timeout))

        gobject.timeout_add_seconds(
            timeout,
            self.__notification_expired,
            self.__lastID)

    except Exception as e:
      logging.exception("Exception occured during window creation.")

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
    if not self.__close_notification(id, 3):
      # Don't know what sending back an empty D-BUS error message is supposed to
      # mean...
      pass


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
    reason is one of:
    1 - The notification expired.
    2 - The notification was dismissed by the user.
    3 - The notification was closed by a call to CloseNotification.
    4 - Undefined/reserved reasons.

    @param id: unsigned int
    @param reason: unsigned int
    """
    logging.debug("Successfully closed notification {}. Reason: {}".format(
      id, reason))


  @dbus.service.signal(
      dbus_interface = "org.freedesktop.Notifications",
      signature = "us")
  def ActionInvoked(self, id, action_key):
    """
    @param id: unsigned int
    @param action_key: string
    """
    pass


def create_argument_parser():
  parser = argparse.ArgumentParser(
      description = "A notification server implementing the specification from "
                    "http://developer.gnome.org/notification-spec/.")

  parser.add_argument(
      "-l", "--loglevel",
      dest = "loglevel",
      default = "WARNING",
      type = lambda value: value.upper(),
      choices = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
      help = "set the logging level")

  parser.add_argument(
      "-t", "--expire-timeout",
      dest = "expireTimeout",
      default = 10000,
      type = int,
      help = "set the maximum/default timeout for notifications in [ms]")

  parser.add_argument(
      "-m", "--margins",
      dest = "margins",
      default = "0,0,0,0",
      type = lambda value: [int(x) for x in value.split(",")],
      help = "set screen margins for top, right, bottom and left side of the "
             "screen in pixels")

  parser.add_argument(
      "-a", "--layout-anchor",
      dest = "layoutAnchor",
      default = "NORTH_WEST",
      type = lambda value: getattr(LayoutAnchor, value),
      choices = ["NORTH_WEST", "SOUTH_WEST", "SOUTH_EAST", "NORTH_EAST"],
      help = "set the origin for the notifications")

  parser.add_argument(
      "-d", "--layout-direction",
      dest = "layoutDirection",
      default = "VERTICAL",
      type = lambda value: getattr(LayoutDirection, value),
      choices = ["VERTICAL", "HORIZONTAL"],
      help = "set the direction for the notifications")

  return parser


def main():
  parser = create_argument_parser()
  parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
  args = parser.parse_args()

  logging.basicConfig(level = getattr(logging, args.loglevel))

  dbus.mainloop.glib.DBusGMainLoop(set_as_default = True)

  loop = gobject.MainLoop()

  notDaemon = NotificationDaemon("/org/freedesktop/Notifications")
  notDaemon.max_expire_timeout = args.expireTimeout
  notDaemon.margins            = args.margins
  notDaemon.layoutAnchor       = args.layoutAnchor
  notDaemon.layoutDirection    = args.layoutDirection

  try:
    loop.run()
  except KeyboardInterrupt:
    logging.info("Exiting.")


if __name__ == '__main__':
  main()
