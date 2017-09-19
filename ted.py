#!/usr/bin/env python3
import curses
import sys
import utils
from ptypes import Point, Rect
from doc import Document
from view import View

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
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1,curses.COLOR_YELLOW,curses.COLOR_BLUE)
        curses.init_pair(2,curses.COLOR_WHITE,curses.COLOR_GREEN)
        curses.init_pair(3,curses.COLOR_BLACK,curses.COLOR_WHITE)
        sys.stdout.write('\033]12;yellow\007')

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
        
    def write(self,text,clr):
        clr=curses.color_pair(clr)|curses.A_BOLD
        for i in range(0,len(text)):
            c=text[i]
            self.scr.addch(c,clr)
        
    def refresh(self):
        self.scr.refresh()
        
    def getkey(self):
        ch=self.scr.getch()
        curses.ungetch(ch)
        key=self.scr.getkey()
        self.keylog.write('{} {}\n'.format(key,ch))
        self.keylog.flush()
        return key
        
    def close(self):
        curses.nocbreak()
        self.scr.keypad(0)
        curses.echo()
        curses.endwin()
        self.scr=None

def message_box(text):
    pass

            
    

def main():
    app=Application()
    doc=Document()
    doc.load('fff')
    view=View(app,doc)
    view.render()
    try:
        while view.process_input():
            view.render()
    except utils.ExitException:
        pass
    
    app.close()


if __name__=='__main__':
    main()
