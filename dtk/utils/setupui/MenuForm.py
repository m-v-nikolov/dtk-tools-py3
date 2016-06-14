import curses


class MenuForm():
    """
    Base class allowing to add the handlers to a menu.
    A menu should be a radio list and this class will automatically select the highlighted radio.
    Also will store the passed menu in self.
    """

    def set_menu_handlers(self, menu, select_function):
        """
        Set the handlers:
        - Enter: Select the item
        - Up/Down key: go up/down and check the item

        :param menu: The npyscreen element used as menu
        :param select_function: Callback function to be called when Enter key is pressed on an item
        """
        self.menu = menu
        self.menu.add_handlers({curses.ascii.CR: select_function,
                                curses.KEY_UP: self.h_go_up,
                                curses.KEY_DOWN: self.h_go_down,
                                curses.KEY_LEFT: self.h_go_up,
                                curses.KEY_RIGHT: self.h_go_down})

    def h_go_up(self, ch):
        """
        Go up an item.
        Just call the normal go up method but also select the element
        """
        self.menu.h_cursor_line_up(ch)
        self.menu.h_select_exit(ch)

    def h_go_down(self, ch):
        """
        Go down an item.
        Just call the normal go down method but also select the element
        """
        self.menu.h_cursor_line_down(ch)
        self.menu.h_select_exit(ch)
