#!/usr/bin/env python3
import curses
import sys
import utils
from ptypes import Point, Rect
from doc import Document
from view import View
from menus import Menu

class Application:
    def __init__(self):
        self.scr=curses.initscr()
        self.keylog=open('key.log','w')
        curses.noecho()
        curses.raw()
        self.scr.keypad(1)
        mx=self.scr.getmaxyx()
        self.width=mx[1]
        self.height=mx[0]
        self.rect=Rect(0,0,self.width,self.height)
        self.menu_bar=Menu('')
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1,curses.COLOR_YELLOW,curses.COLOR_BLUE)
        curses.init_pair(2,curses.COLOR_WHITE,curses.COLOR_GREEN)
        curses.init_pair(3,curses.COLOR_BLACK,curses.COLOR_WHITE)
        sys.stdout.write('\033]12;yellow\007')
        
    def set_menu(self,bar):
        self.menu_bar=bar

    def move(self,pos):
        if not isinstance(pos,Point):
            pos=Point(pos)
        if self.rect.is_point_inside(pos):
            self.scr.move(pos.y,pos.x)
            return True
        return False
        
    def fill(self,x0,y0,w,h,c,clr):
        for y in range(y0,y0+h):
            self.move((x0,y))
            for x in range(x0,x0+w):
                self.scr.addch(c,curses.color_pair(clr))
        
    def write(self,text,clr,attr=curses.A_BOLD):
        clr=curses.color_pair(clr)|attr
        for i in range(0,len(text)):
            c=text[i]
            self.scr.addch(c,clr)
        
    def refresh(self):
        self.scr.refresh()
        
    def getkey(self):
        #ch=self.scr.getch()
        #curses.ungetch(ch)
        key=self.scr.getkey()
        if len(key)==1 and ord(key[0])==27:
            self.scr.nodelay(True)
            key="Alt+"+self.scr.getkey()
            self.scr.nodelay(False)
        self.keylog.write('{}\n'.format(key))
        self.keylog.flush()
        return key
        
    def close(self):
        curses.nocbreak()
        self.scr.keypad(0)
        curses.echo()
        curses.endwin()
        self.scr=None
        
    def draw_menu(self):
        self.move((0,0))
        self.write(' ',2)
        for item in self.menu_bar.items:
            title=item[0].title
            self.write('[',2)
            rev=False
            for c in title:
                if c=='&':
                    rev=True
                else:
                    attr=curses.A_BOLD
                    if rev:
                        attr=curses.A_REVERSE
                        rev=False
                    self.write(c,2,attr)
            self.write('] ',2)

def message_box(text):
    pass

def fill_menu(menu,desc):
    for item in desc:
        title=item[0]
        action=item[1]
        if isinstance(action,list):
            m=Menu(title)
            fill_menu(m,action)
            menu.add_item(m)
        else:
            menu.add_item(title,action)
            

def create_menu(view):
    desc=[ ('&File',[ ('&Open',view.on_file_open)
                    ]),
           ('&Edit',[ ('&Copy',view.on_copy),
                      ('C&ut',view.on_cut),
                      ('&Paste',view.on_paste)
                    ]) 
         ]
    bar=Menu('')
    fill_menu(bar,desc)
    return bar

def main():
    app=Application()
    doc=Document()
    doc.load('fff')
    view=View(app,doc)
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


if __name__=='__main__':
    main()
