#!/usr/bin/env python
import curses
import sys
from ptypes import Point, Rect

class Application:
    def __init__(self):
        self.scr=curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.scr.keypad(1)
        mx=self.scr.getmaxyx()
        self.width=mx[1]
        self.height=mx[0]
        self.rect=Rect(0,0,self.width,self.height)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1,curses.COLOR_YELLOW,curses.COLOR_BLUE)
        sys.stdout.write('\033]12;yellow\007')
        #for i in range(0, curses.COLORS):
        #    curses.init_pair(i + 1, i, -1)

    def move(self,pos):
        if not isinstance(pos,Point):
            pos=Point(pos)
        if self.rect.is_point_inside(pos):
            self.scr.move(pos.y,pos.x)
        
    def fill(self,x0,y0,w,h,c,clr):
        for y in xrange(y0,y0+h):
            self.move((x0,y))
            for x in xrange(x0,x0+w):
                self.scr.addch(c,curses.color_pair(clr))
        
    def write(self,text,clr):
        clr=curses.color_pair(clr)|curses.A_BOLD
        for i in xrange(0,len(text)):
            c=text[i]
            self.scr.addch(c,clr)
        
    def refresh(self):
        self.scr.refresh()
        
    def getch(self):
        return self.scr.getch()
        
    def stub(self):
        #self.fill(0,0,self.width,1,curses.ACS_BOARD)
        self.fill(0,1,self.width,self.height-2,' ',1) #curses.ACS_CKBOARD)
        self.scr.refresh()
        self.scr.getch()

    def close(self):
        curses.nocbreak()
        self.scr.keypad(0)
        curses.echo()
        curses.endwin()
        self.scr=None

def message_box(text):
    pass
        
class View:
    def __init__(self,scr,doc):
        self.scr=scr
        self.doc=doc
        self.offset=Point(0,0)
        self.cursor=Point(0,0)
        
    def process_input(self):
        c=self.scr.getch()
        if c==ord('q'):
            return False
        if c==curses.KEY_RIGHT:
            self.cursor+=(1,0)
        if c==curses.KEY_LEFT and self.cursor.x>0:
            self.cursor-=(1,0)
        if c==curses.KEY_UP and self.cursor.y>0:
            self.cursor-=(0,1)
        if c==curses.KEY_DOWN:
            self.cursor+=(0,1)
        return True
        
    def render(self):
        if not self.doc.valid:
            i0=self.offset.y-1
            j0=self.offset.x
            for y in xrange(1,self.scr.height-1):
                row_index=i0+y
                self.scr.move(Point(0,y))
                row=' '*self.scr.width
                if row_index>=0 and row_index<self.doc.rows_count():
                    row=str(self.doc.get_row(row_index))
                    row=row[j0:]
                    if len(row)>self.scr.width:
                        row=row[0:self.scr.width]
                    if len(row)<self.scr.width:
                        row=row+' '*(self.scr.width-len(row))
                    self.scr.write(row,1)
                else:
                    self.scr.write(row,1)
        self.draw_cursor()
        self.scr.refresh()
        
    def draw_cursor(self):
        p=self.cursor-self.offset+Point(0,1)
        self.scr.move(p)

            
    
class Document:
    def __init__(self):
        self.text=[]
        self.valid=False
        
    def load(self,filename):
        try:
            self.text=open(filename,'r').readlines()
            self.text=[row.replace('\n','') for row in self.text]
            self.invalidate()
        except IOError:
            message_box('Failed to open {}'.format(filename))
            
    def rows_count(self):
        return len(self.text)
        
    def get_row(self,index):
        if index<0 or index>=self.rows_count():
            return ''
        return self.text[index]
            
    def invalidate(self):
        self.valid=False
        
    def validate(self):
        self.valid=True

def main():
    app=Application()
    #app.stub()
    doc=Document()
    doc.load('fff')
    view=View(app,doc)
    view.render()
    while view.process_input():
        view.render()
    
    app.close()


if __name__=='__main__':
    main()