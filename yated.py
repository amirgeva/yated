#!/usr/bin/env python3
import curses
import sys
import utils
import config
from ptypes import Point, Rect
from doc import Document
from view import View
from menus import Menu


class Application(object):
    def __init__(self):
        self.scr = curses.initscr()
        self.keylog = None
        curses.noecho()
        curses.raw()
        self.scr.keypad(1)
        mx = self.scr.getmaxyx()
        self.width = mx[1]
        self.height = mx[0]
        self.rect = Rect(0, 0, self.width, self.height)
        self.menu_bar = Menu('')
        self.shortcuts = {}
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, config.getint('fg1', curses.COLOR_YELLOW),
                         config.getint('bg1', curses.COLOR_BLUE))
        curses.init_pair(2, config.getint('fg2', curses.COLOR_WHITE),
                         config.getint('bg2', curses.COLOR_GREEN))
        curses.init_pair(3, config.getint('fg3', curses.COLOR_BLACK),
                         config.getint('bg3', curses.COLOR_WHITE))
        curses.init_pair(4, config.getint('fg4', curses.COLOR_BLACK),
                         config.getint('bg4', curses.COLOR_CYAN))
        curses.init_pair(5, config.getint('fg5', curses.COLOR_YELLOW),
                         config.getint('bg5', curses.COLOR_BLUE))
        curses.init_pair(6, config.getint('fg6', curses.COLOR_YELLOW),
                         config.getint('bg6', curses.COLOR_BLUE))
        curses.init_pair(7, config.getint('fg7', curses.COLOR_WHITE),
                         config.getint('bg7', curses.COLOR_RED))
        sys.stdout.write('\033]12;yellow\007')

    def set_menu(self, bar):
        self.menu_bar = bar
        if len(bar.items) > 0:
            self.shortcuts['KEY_F(10)'] = bar.items[0]

    def move(self, pos):
        if not isinstance(pos, Point):
            pos = Point(pos)
        if self.rect.is_point_inside(pos):
            self.scr.move(pos.y, pos.x)
            return True
        return False

    def fill_rect(self, rect, c, clr):
        self.fill(rect.tl.x, rect.tl.y, rect.width(), rect.height(), c, clr)

    def fill(self, x0, y0, w, h, c, clr):
        for y in range(y0, y0 + h):
            self.move((x0, y))
            self.write(c * w, clr)
            # for x in range(x0, x0 + w):
            # self.scr.addch(c, curses.color_pair(clr))

    def write(self, text, clr, attr=curses.A_BOLD):
        clr = curses.color_pair(clr | (attr & 0x7FFF))
        if isinstance(text, str):
            for i in range(0, len(text)):
                c = text[i]
                self.scr.addstr(c, clr)
        else:
            self.scr.addch(text, clr)

    def draw_frame(self, rect, color):
        self.move(rect.tl)
        self.write(curses.ACS_ULCORNER, color)
        for i in range(0, rect.width() - 2):
            self.write(curses.ACS_HLINE, color)
        self.write(curses.ACS_URCORNER, color)
        for y in range(rect.tl.y + 1, rect.br.y):
            self.move(Point(rect.tl.x, y))
            self.write(curses.ACS_VLINE, color)
            self.move(Point(rect.br.x - 1, y))
            self.write(curses.ACS_VLINE, color)
        self.move(Point(rect.tl.x, rect.br.y - 1))
        self.write(curses.ACS_LLCORNER, color)
        for i in range(0, rect.width() - 2):
            self.write(curses.ACS_HLINE, color)
        self.write(curses.ACS_LRCORNER, color)

    def refresh(self):
        self.scr.refresh()

    def getkey(self):
        try:
            self.scr.nodelay(False)
            key = self.scr.getkey()
            if len(key) == 1 and ord(key[0]) == 27:
                self.scr.nodelay(True)
                key = "Alt+" + self.scr.getkey()
                self.scr.nodelay(False)
        except curses.error:
            key = 'ESC'
        if key == 'KEY_F(24)':  # For debugging purposes
            self.keylog = open('/tmp/key.log', 'w')
        if self.keylog is not None:
            self.keylog.write('{}   {}\n'.format(key, hex(ord(key[0]))))
            self.keylog.flush()
        return key

    def close(self):
        curses.nocbreak()
        self.scr.keypad(0)
        curses.echo()
        curses.endwin()
        self.scr = None

    def draw_menu(self):
        color = 4
        self.move((0, 0))
        self.write(' ' * self.width, color)
        self.move((1, 0))
        pos = Point(2, 1)
        for item in self.menu_bar.items:
            title = item.title
            item.pos = Point(pos)
            pos += Point(len(title) - title.count('&') + 3, 0)
            self.write('[', color)
            rev = False
            char_color = color
            for c in title:
                if c == '&':
                    char_color = color + 1
                    rev = True
                else:
                    attr = curses.A_BOLD
                    if rev:
                        rev = False
                        self.shortcuts['Alt+' + c.upper()] = item
                        self.shortcuts['Alt+' + c.lower()] = item
                    self.write(c, char_color, attr)
                    char_color = color
            self.write('] ', color)


def message_box(text):
    pass


def fill_menu(menu, desc):
    for item in desc:
        title = item[0]
        action = item[1]
        if isinstance(action, list):
            m = Menu(title)
            fill_menu(m, action)
            menu.add_item(m)
        else:
            menu.add_item(title, action)


def create_menu(view):
    desc = [('&File', [('&New     Ctrl+N', view.on_file_new),
                       ('&Open    Ctrl+O', view.on_file_open),
                       ('&Save    Ctrl+S', view.on_file_save),
                       ('Save &As', view.on_file_save_as),
                       ('&Exit    Ctrl+Q', view.on_file_exit)
                       ]),
            ('&Edit', [('&Copy          Ctrl+C', view.on_copy),
                       ('C&ut           Ctrl+X', view.on_cut),
                       ('&Paste         Ctrl+V', view.on_paste),
                       ('&Find          Ctrl+F', view.on_find_replace),
                       ('Find &Again        F3', view.on_find_again),
                       ('&Record Macro  Ctrl+R', view.toggle_macro_record),
                       ('P&lay Macro    Ctrl+P', view.play_macro),
                       ]),
            ('&Options', [('&Colors', view.on_colors),
                          ('&Editor', view.on_cfg_editor),
                          ]),
            ('&Help', [('&About', view.on_help_about),
                       ]),
            ]
    bar = Menu('')
    fill_menu(bar, desc)
    return bar


def main():
    app = Application()
    filename = ''
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    doc = Document(filename)
    doc.load(filename)
    view = View(app, doc)
    app.set_menu(create_menu(view))
    app.draw_menu()
    view.render()
    try:
        while view.process_input():
            app.draw_menu()
            view.render()
    except utils.ExitException:
        pass

    app.close()


if __name__ == '__main__':
    main()
