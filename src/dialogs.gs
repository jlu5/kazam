[indent=4]

uses
    Gtk
    
def new_error_dialog(primary:string, secondary:string) : int
    var dialog = new MessageDialog(null, 0, MessageType.ERROR, ButtonsType.OK, primary)
    dialog.format_secondary_text(secondary)
    var result = dialog.run()
    Gtk.main_quit()
    return result
