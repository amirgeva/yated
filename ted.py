#!/usr/bin/env python3
import curses
import sys
#import os
from ptypes import Point, Rect
import collections
from clip import copy, paste
import utils

class ExitException(Exception):
    pass

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

class View:
    def __init__(self,scr,doc):
        self.scr=scr
        self.rect=Rect(self.scr.rect.tl+Point(0,1),self.scr.rect.br-Point(0,2))
        self.doc=doc
        self.offset=Point(0,0)
        self.cursor=Point(0,0)
        self.selection=None
        self.lastx=0
        self.tabsize=4
        self.insert=True
        self.shifted_moves={'KEY_SLEFT':'KEY_LEFT',
                            'KEY_SRIGHT':'KEY_RIGHT',
                            'KEY_SF':'KEY_DOWN',
                            'KEY_SR':'KEY_UP',
                            'KEY_SPREVIOUS':'KEY_PPAGE',
                            'KEY_SNEXT':'KEY_NPAGE',
                            'KEY_SHOME':'KEY_HOME',
                            'KEY_SEND':'KEY_END',
                            'kRIT6':'kRIT5',
                            'kLFT6':'kLFT5'
                            }
        self.movement_keys={'KEY_LEFT':(-1,0),
                            'KEY_RIGHT':(1,0),
                            'KEY_DOWN':(0,1),
                            'KEY_UP':(0,-1),
                            'KEY_PPAGE':(0,-self.rect.height()),
                            'KEY_NPAGE':(0,self.rect.height()),
                            'KEY_HOME':lambda v:(-v.cursor.x,0),
                            'KEY_END':(99999,0),
                            'kRIT5':lambda v:v.doc.word_right(v.cursor)-v.cursor,
                            'kLFT5':lambda v:v.doc.word_left(v.cursor)-v.cursor,
                            'kEND5':lambda v:(0,v.doc.rows_count()),
                            'kHOM5':lambda v:(-v.cursor.x,-v.cursor.y)
                            }

    def process_text_input(self,c):
        movement=None
        if c==27:
            raise ExitException()
        if c==3 and not self.selection is None:
            copy(self.get_selected_text())
        if c==22:
            text=paste()
            if len(text)>0:
                if not self.selection is None:
                    self.delete_selection()
                movement=self.doc.add_text(text,self.cursor,self.insert)
        if c==ord('/') and not self.selection is None:
            sel=self.normalized_selection()
            inc=0
            if sel.br.x>0:
                inc=1
            for y in range(sel.tl.y,sel.br.y+inc):
                row=self.doc.get_row(y)
                if row.startswith('//'):
                    self.doc.delete_block(y,0,2)
                else:
                    self.doc.add_text('//',Point(0,y),True)
        elif c>=32 and c<127:
            if not self.selection is None:
                self.delete_selection()
            if self.doc.add_char(chr(c),self.cursor,self.insert):
                movement=(1,0)
        if c==9:
            if not self.selection is None:
                sel=self.normalized_selection()
                inc=0
                if sel.br.x>0:
                    inc=1
                for y in range(sel.tl.y,sel.br.y+inc):
                    self.doc.add_text(' '*self.tabsize,Point(0,y),self.insert)
            else:
                movement=self.doc.add_text(' '*self.tabsize,self.cursor,self.insert)
        if c==10:
            if not self.selection is None:
                self.delete_selection()
            if self.doc.new_line(self.cursor,self.insert):
                movement=(-self.cursor.x,1)
        return movement

    def process_movement(self,movement):
        movement=Point(movement)
        new_cursor=self.doc.set_cursor(self.cursor+movement)
        if movement.x!=0:
            self.lastx=new_cursor.x
        else:
            new_cursor=self.doc.set_cursor(Point(self.lastx,new_cursor.y))
        if not self.selection is None:
            self.selection.br = new_cursor
        self.cursor=new_cursor
        self.scroll_display()
        
    def scroll_display(self):
        scr_pos=self.cursor-self.offset
        if not self.rect.is_point_inside(scr_pos):
            if scr_pos.x>=self.rect.br.x:
                self.offset.x=self.cursor.x-self.rect.width()
            if scr_pos.x<self.rect.tl.x:
                self.offset.x=self.cursor.x
            if scr_pos.y>=self.rect.br.y or scr_pos.y<self.rect.tl.y:
                self.offset.y=self.cursor.y-int(self.rect.height()/2)
                if self.offset.y<0:
                    self.offset.y=0
            self.doc.invalidate()
        
        
    def process_movement_key(self,key):
        movement=None
        shift=False
        if key in self.shifted_moves:
            if self.selection is None:
                self.selection=Rect(self.cursor,self.cursor)
            key=self.shifted_moves.get(key)
            shift=True
        if key in self.movement_keys:
            m=self.movement_keys.get(key)
            if isinstance(m, collections.Callable):
                movement=m(self)
            else:
                movement=m
            if not shift:
                self.selection=None
        return movement
        
    def process_special_keys(self,key):
        movement=None
        if key=='KEY_DC':
            if not self.selection is None:
                self.delete_selection()
            else:
                self.doc.delete_char(self.cursor)
        if key=='KEY_BACKSPACE' and self.cursor.x>0:
            if not self.selection is None:
                self.delete_selection()
            else:
                self.doc.delete_char(self.cursor-Point(1,0))
                movement=(-1,0)
        if key=='KEY_BTAB' and not self.selection is None:
            sel=self.normalized_selection()
            inc=0
            if sel.br.x>0:
                inc=1
            for y in range(sel.tl.y,sel.br.y+inc):
                row=self.doc.get_row(y)
                n=utils.count_leading_spaces(row)
                if n>self.tabsize:
                    n=self.tabsize
                if n>0:
                    self.doc.delete_block(y,0,n)
        return movement

    def delete_selection(self):
        if not self.selection is None:
            sel=self.normalized_selection()
            if sel.tl.y==sel.br.y:
                self.doc.delete_block(sel.tl.y,sel.tl.x,sel.br.x)
            else:
                self.doc.delete_block(sel.tl.y,sel.tl.x,-1)
                self.doc.delete_block(sel.br.y,0,sel.br.x)
                for y in range(sel.tl.y+1,sel.br.y):
                    self.doc.delete_row(sel.tl.y+1)
                self.doc.join_next_row(sel.tl.y)
            self.cursor=sel.tl
        self.selection=None
        
    def process_input(self):
        key=self.scr.getkey()
        movement=self.process_movement_key(key)
        if not movement:
            movement=self.process_special_keys(key)
        if not movement and len(key)==1:
            movement=self.process_text_input(ord(key[0]))
        if movement:
            self.process_movement(movement)
        return True

    def normalized_selection(self):
        if self.selection is None:
            return None
        sel=self.selection
        if sel.tl.y > sel.br.y:
            sel = Rect(sel.br, sel.tl)
        if sel.tl.y == sel.br.y and sel.tl.x > sel.br.x:
            sel = Rect(sel.br, sel.tl)
        return sel

    def render(self):
        if not self.doc.valid:
            sel = self.normalized_selection()
            i0=self.offset.y-1
            j0=self.offset.x
            for y in range(1,self.scr.height-1):
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
                    color=1
                    if not sel is None:
                        if row_index>=sel.tl.y and row_index<=sel.br.y:
                            x=0
                            if row_index==sel.tl.y:
                                x=sel.tl.x
                                self.scr.write(row[0:x],1)
                            limit=len(row)
                            if row_index==sel.br.y:
                                limit=sel.br.x
                            self.scr.write(row[x:limit],3)
                            if limit<len(row):
                                self.scr.write(row[limit:],1)
                        else:
                            self.scr.write(row, 1)
                    else:
                        self.scr.write(row,1)
                else:
                    self.scr.write(row,2)
        self.draw_cursor()
        self.scr.refresh()

    def get_selected_text(self):
        sel = self.normalized_selection()
        res=[]
        for row_index in range(sel.tl.y,sel.br.y+1):
            row=self.doc.get_row(row_index)
            x=0
            limit=len(row)
            if row_index==sel.tl.y:
                x=sel.tl.x
            if row_index==sel.br.y:
                limit=sel.br.x
            res.append(row[x:limit])
        return '\n'.join(res)

    def draw_cursor(self):
        p=self.cursor-self.offset+Point(0,1)
        self.scr.move(p)

            
    
class Document:
    def __init__(self):
        self.text=['']
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
        
    def join_next_row(self,row_index):
        if row_index>=0 and row_index<(self.rows_count()-1):
            row=self.get_row(row_index)
            next=self.get_row(row_index+1)
            del self.text[row_index+1]
            self.text[row_index]=row+next

    def delete_block(self,row_index,x0,x1):
        if row_index>=0 and row_index<self.rows_count():
            row=self.get_row(row_index)
            if x1<0:
                x1=len(row)
            self.text[row_index]=row[0:x0]+row[x1:]
            
    def delete_row(self,row_index):
        if row_index>=0 and row_index<self.rows_count():
            del self.text[row_index]

    def word_right(self,cursor):
        if cursor.y<0 or cursor.y>=self.rows_count():
            return cursor
        row=self.get_row(cursor.y)
        x=cursor.x
        space_found=False
        while x<len(row):
            if not row[x].isalnum():
                space_found=True
            if row[x].isalnum() and space_found:
                break
            x=x+1
        return Point(x,cursor.y)

    def word_left(self,cursor):
        if cursor.y<0 or cursor.y>=self.rows_count():
            return cursor
        row=self.get_row(cursor.y)
        x=cursor.x
        while x>0:
            x-=1
            if x>0 and row[x].isalnum() and not row[x-1].isalnum():
                break
        return Point(x,cursor.y)
        
    def set_cursor(self,cursor):
        if cursor.y<0:
            return Point(0,0)
        if cursor.y>=self.rows_count():
            return Point(0,self.rows_count()-1)
        row=self.get_row(cursor.y)
        x=cursor.x
        if x<0:
            x=0
        if x>len(row):
            x=len(row)
        return Point(x,cursor.y)
        
    def delete_char(self,cursor):
        if cursor.x<0 or cursor.y<0 or cursor.y>=self.rows_count():
            return False
        row=self.text[cursor.y]
        if cursor.x<len(row):
            row=row[0:cursor.x]+row[cursor.x+1:]
            self.text[cursor.y]=row
            self.invalidate()
        return True
            
    def add_char(self,c,cursor,insert):
        if cursor.x<0 or cursor.y<0 or cursor.y>=self.rows_count():
            return False
        row=self.text[cursor.y]
        if cursor.x>len(row):
            row=row+' '*(cursor.x-len(row))
        rest=cursor.x
        if not insert:
            rest+=1
        row=row[0:cursor.x]+c+row[rest:]
        self.text[cursor.y]=row
        self.invalidate()
        return True
        
    def add_text(self, text, cursor, insert):
        cx=cursor.x
        res=Point(0,0)
        if cursor.x<0 or cursor.y<0 or cursor.y>=self.rows_count():
            return res
        for c in text:
            if ord(c)==10:
                self.new_line(cursor,insert)
                cursor=Point(0,cursor.y+1)
                res=Point(-cx,res.y+1)
            else:
                self.add_char(c,cursor,insert)
                cursor=cursor+Point(1,0)
                res+=(1,0)
        return res
    
    def new_line(self, cursor, insert):
        if cursor.x<0 or cursor.y<0:
            return False
        if cursor.y>=self.rows_count():
            while cursor.y>=self.rows_count():
                self.text.append('')
        else:
            row=self.get_row(cursor.y)
            cur=[row[0:cursor.x],row[cursor.x:]]
            self.text=self.text[0:cursor.y]+cur+self.text[cursor.y+1:]
        return True

    def invalidate(self):
        self.valid=False
        
    def validate(self):
        self.valid=True

def main():
    app=Application()
    doc=Document()
    doc.load('fff')
    view=View(app,doc)
    view.render()
    try:
        while view.process_input():
            view.render()
    except ExitException:
        pass
    
    app.close()


if __name__=='__main__':
    main()
