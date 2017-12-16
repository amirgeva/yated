import curses
from ptypes import Point


class MenuItem(object):
    def __init__(self, title, action=None):
        self.title = title
        self.action = action
        self.key = ''
        
    def activate(self):
        if self.action is not None:
            self.action()


class Menu(object):
    def __init__(self, title):
        self.title = title
        self.pos = Point(0, 0)
        self.key = ''
        self.cur = 0
        self.items = []
        self.width = 4
        
    def add_item(self, *args):  # title, action = None):
        if len(args) == 1 and isinstance(args[0], MenuItem):
            item = args[0]
        elif len(args) == 1 and isinstance(args[0], Menu):
            item = args[0]
        elif len(args) == 1 and isinstance(args[0], str):
            item = MenuItem(args[0])
        elif len(args) == 2:
            item = MenuItem(args[0], args[1])
        else:
            raise TypeError()
        self.items.append(item)
        self.width = max(self.width, 4+len(item.title))
        
    def select_next(self):
        self.cur = (self.cur+1) % len(self.items)

    def select_prev(self):
        self.cur = (self.cur-1) % len(self.items)
        
    def activate_current(self):
        self.items[self.cur].activate()
        
    def draw(self, scr):
        color = 4
        pos = Point(self.pos)
        scr.move(pos)
        scr.write(curses.ACS_ULCORNER, color)
        for i in range(0, self.width-2):
            scr.write(curses.ACS_HLINE, color)
        scr.write(curses.ACS_URCORNER, color)
        index = 0
        for item in self.items:
            color = 4
            pos += (0, 1)
            scr.move(pos)
            scr.write(curses.ACS_VLINE, color)
            scr.write(' ', color)
            rev = False
            n = 0
            if index == self.cur:
                color = 3
            for c in item.title:
                if c == '&':
                    rev = True
                else:
                    attr = 0
                    if rev:
                        attr = curses.A_REVERSE
                        rev = False
                        item.key = c
                    scr.write(c, color, attr)
                    n = n+1
            s = ' '*(self.width-4-n)
            scr.write(s, color)
            color = 4
            scr.write(' ', color)
            scr.write(curses.ACS_VLINE, color)
            index += 1
        pos += (0, 1)
        scr.move(pos)
        scr.write(curses.ACS_LLCORNER, color)
        for i in range(0, self.width-2):
            scr.write(curses.ACS_HLINE, color)
        scr.write(curses.ACS_LRCORNER, color)

