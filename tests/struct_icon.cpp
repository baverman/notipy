// Compile with:
// g++ -Wall -lnotify -lboost_program_options -o struct_icon struct_icon.cpp $(pkg-config --cflags --libs glib-2.0) $(pkg-config --cflags --libs gtk+-3.0)

#include <libnotify/notify.h>
#include <libnotify/notification.h>

#include <gdk-pixbuf/gdk-pixbuf.h>
#include <gdk-pixbuf/gdk-pixbuf-core.h>

#include <boost/shared_ptr.hpp>
#include <boost/bind.hpp>
#include <boost/program_options.hpp>
namespace po = boost::program_options;

#include <iostream>
#include <string>

namespace
{
  void
  printHelp (const char* const progName, const po::options_description& desc)
  {
    std::cout
      << progName << " [options] <icon_file> <summary> <body>" << std::endl
      << std::endl
      << desc << std::endl;
  }
}


int
main (int argc, char** const argv)
{
  po::options_description desc("Options");
  desc.add_options()
    ("help"   , "print this help message and exit.");

  po::options_description positional_desc("Positional");
  positional_desc.add_options()
    ("icon"   , "icon file.")
    ("summary", "message summary.")
    ("body"   , "message body (may contain pango markup)");

  po::options_description all_desc("Options");
  all_desc.add(desc).add(positional_desc);

  po::positional_options_description pd;
  pd.add("icon", 1).add("summary", 1).add("body", 1);

  po::variables_map vm;
  po::store(
      po::command_line_parser(argc, argv).options(all_desc).positional(pd).run(),
      vm);
  po::notify(vm);

  if (vm.count("help"))
  {
    ::printHelp(argv[0], desc);
    return 0;
  }

  if (0 == vm.count("icon") || 0 == vm.count("summary") || 0 == vm.count("body"))
  {
    ::printHelp(argv[0], desc);
    return -1;
  }

  if (!notify_init("struct_icon"))
  {
    std::cout << "Couldn't initialize libnotify." << "\n";
    return -1;
  }

  GError* error = 0;

  boost::shared_ptr<NotifyNotification> notify(
      notify_notification_new(
        vm["summary"].as<std::string>().c_str(),
        vm["body"].as<std::string>().c_str(),
        ""),
      &g_object_unref);

  boost::shared_ptr<GdkPixbuf> pixbuf(
      gdk_pixbuf_new_from_file(vm["icon"].as<std::string>().c_str(), &error),
      &gdk_pixbuf_unref);

  if (0 == pixbuf.get() && error)
  {
    std::cerr << "Unable to open icon file: " << error->message << "\n";
    g_error_free(error);
    error = 0;
    return -1;
  }

  notify_notification_set_icon_from_pixbuf(notify.get(), pixbuf.get());
  notify_notification_show(notify.get(), 0);
  notify_uninit();

  return 0;
}
