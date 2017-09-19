import collections
from ptypes import Point, Rect
from clip import copy,paste
import utils


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
        #if c==27:
        #    raise utils.ExitException()
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
        if key=='KEY_F(12)':
            raise utils.ExitException()
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

    def on_copy(self):
        pass

    def on_cut(self):
        pass

    def on_paste(self):
        pass

    def on_file_open(self):
        pass


