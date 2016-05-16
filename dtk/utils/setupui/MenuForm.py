import curses


class MenuForm():
    def set_menu_handlers(self, menu):
        self.menu = menu
        self.menu.add_handlers({curses.ascii.CR: self.h_select_menu,
                                curses.KEY_UP: self.h_go_up,
                                curses.KEY_DOWN: self.h_go_down})

    def h_go_up(self, ch):
        self.menu.h_cursor_line_up(ch)
        self.menu.h_select_exit(ch)

    def h_go_down(self, ch):
        self.menu.h_cursor_line_down(ch)
        self.menu.h_select_exit(ch)
