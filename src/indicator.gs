[indent=4]

uses
    AppIndicator
    Gtk

class MainIndicator : Indicator

    show_menuitem : CheckMenuItem
    close_menuitem : MenuItem
    
    construct()
        GLib.Object(id:"kazam", icon_name:"indicator-messages", 
                    category:category_from_enum(Category.APPLICATION_STATUS))
        
    def category_from_enum(category: AppIndicator.Category): string
        var categ_class = (EnumClass) typeof(AppIndicator.Category).class_ref()
        return categ_class.get_value(category).value_nick

    init
        this.set_status(Status.ATTENTION)
        this.set_attention_icon ("indicator-messages-new")
    
        var menu = new Menu()
        
        show_menuitem = new CheckMenuItem.with_label("Show Kazam")
        show_menuitem.set_active(true)
        close_menuitem = new MenuItem.with_label("Quit")
        
        menu.append(show_menuitem)
        menu.append(close_menuitem)
        menu.show_all()
        this.set_menu(menu)

