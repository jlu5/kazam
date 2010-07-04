[indent=4]

uses
    Gtk
   
class Main : GLib.Object
    
    start_window : GLib.Object
    indicator : MainIndicator

    init
        try
            var builder = new Builder()
            builder.add_from_file("./data/ui/kazam.ui")
            builder.connect_signals(null)
            
            var window = builder.get_object("start_window") as Window
        
            start_window = new StartWindow(builder)
            
            indicator = new MainIndicator()
            
        except e : GLib.Error
            error_string:string = "%s".printf(e.message)
            new_error_dialog("An error occured", error_string)
            Gtk.main_quit()
    
init
    Gtk.init(ref args)
    var m = new Main()
    Gtk.main()
