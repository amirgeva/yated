#!/usr/bin/env python
import curses

flog=open('log','w')

class Application:
    def __init__(self):
        self.scr=curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.scr.keypad(1)
        mx=self.scr.getmaxyx()
        self.width=mx[1]
        self.height=mx[0]
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1,curses.COLOR_WHITE,curses.COLOR_BLUE)
        #for i in range(0, curses.COLORS):
        #    curses.init_pair(i + 1, i, -1)

        
    def fill(self,x0,y0,w,h,c,clr):
        for y in xrange(y0,y0+h):
            self.scr.move(y,x0)
            for x in xrange(x0,x0+w):
                self.scr.addch(c,curses.color_pair(clr))
        
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

def main():
    app=Application()
    app.stub()
    app.close()


if __name__=='__main__':
    main()