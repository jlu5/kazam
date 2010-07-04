[indent=4]

uses
    Gtk
    
class StartWindow : GLib.Object

    builder : Builder
    window : Window
    
    video_combobox : ComboBox
    
    construct(vbuilder:Builder)
        builder = vbuilder

    init 
        var window = builder.get_object("start_window") as Window
        
        video_combobox = builder.get_object("video_combobox") as ComboBox
        
        window.show_all()
        
        
