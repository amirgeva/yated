import collections
import curses
from ptypes import Point, Rect
from dialogs import Dialog
from clip import copy,paste
import utils


class View:
    def __init__(self,app,doc):
        self.app=app
        self.rect=Rect(self.app.rect.tl+Point(0,1),self.app.rect.br-Point(0,2))
        self.doc=doc
        self.active_menu=None
        self.active_dialog=None
        self.offset=Point(0,0)
        self.cursor=Point(0,0)
        self.rownum_width=0
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
        if c==3:
            self.on_copy()
        if c==22:
            text=paste()
            if len(text)>0:
                self.doc.start_compound()
                if not self.selection is None:
                    self.delete_selection()
                movement=self.doc.add_text(text,self.cursor,self.insert)
                self.doc.stop_compound()
        if c==26:
            movement=self.doc.undo()
        if c==ord('/') and not self.selection is None:
            sel=self.normalized_selection()
            inc=0
            if sel.br.x>0:
                inc=1
            self.doc.start_compound()
            for y in range(sel.tl.y,sel.br.y+inc):
                row=self.doc.get_row(y)
                if row.startswith('//'):
                    self.doc.delete_block(y,0,2)
                else:
                    self.doc.add_text('//',Point(0,y),True)
            self.doc.stop_compound()
        elif c>=32 and c<127:
            if not self.selection is None:
                self.delete_selection()
            if self.doc.add_char(chr(c),self.cursor,self.insert):
                movement=(1,0)
        if c==9:
            self.doc.start_compound()
            if not self.selection is None:
                sel=self.normalized_selection()
                inc=0
                if sel.br.x>0:
                    inc=1
                for y in range(sel.tl.y,sel.br.y+inc):
                    self.doc.add_text(' '*self.tabsize,Point(0,y),self.insert)
            else:
                movement=self.doc.add_text(' '*self.tabsize,self.cursor,self.insert)
            self.doc.stop_compound()
        if c==10:
            if not self.selection is None:
                self.delete_selection()
            row=self.doc.get_row(self.cursor.y)
            indent=0
            for i in range(0,len(row)):
                if row[i]==' ':
                    indent+=1
                else:
                    break
            movement=self.doc.new_line(self.cursor)
            self.doc.insert_block(' '*indent,self.cursor+movement)
            movement+=Point(indent,0)
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
        if key=='KEY_BACKSPACE':
            if not self.selection is None:
                self.delete_selection()
            else:
                if self.cursor.x>0:
                    self.doc.delete_char(self.cursor-Point(1,0))
                    movement=(-1,0)
                elif self.cursor.y>0:
                    y=self.cursor.y-1
                    movement=(len(self.doc.get_row(y))-self.cursor.x,-1)
                    self.doc.join_next_row(self.cursor.y-1)
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
            self.doc.start_compound()
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
            self.doc.stop_compound()
        self.selection=None
        
    def process_app_shortcuts(self,key):
        if key in self.app.shortcuts:
            self.active_menu=self.app.shortcuts.get(key)
            
    def process_menu_keys(self,key):
        menu_index=self.app.menu_bar.items.index(self.active_menu)
        n=len(self.app.menu_bar.items)
        if key=='KEY_LEFT':
            self.active_menu=self.app.menu_bar.items[(menu_index-1)%n]
        if key=='KEY_RIGHT':
            self.active_menu=self.app.menu_bar.items[(menu_index+1)%n]
        if key=='ESC':
            self.active_menu=None
            return
        for item in self.active_menu.items:
            if key.lower()==item.key.lower():
                item.activate()
                self.active_menu=None
                return
                
    def process_dialog_keys(self,key):
        action=self.active_dialog.process_key(key)
        if isinstance(action, collections.Callable):
            action()
        
    def process_input(self):
        key=self.app.getkey()
        if key=='KEY_F(12)':
            raise utils.ExitException()
        self.process_app_shortcuts(key)
        if not self.active_menu is None:
            self.process_menu_keys(key)
        elif not self.active_dialog is None:
            self.process_dialog_keys(key)
        else:
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

    def line_number_width(self):
        s=str(len(self.doc.text))
        return len(s)

    def render(self):
        if not self.doc.valid:
            x0=self.line_number_width()
            self.rownum_width=x0
            w=self.app.width-x0
            sel = self.normalized_selection()
            i0=self.offset.y-1
            j0=self.offset.x
            for y in range(1,self.app.height-1):
                row_index=i0+y
                self.app.move(Point(0,y))
                rownum=str(row_index+1)
                rownum=' '*(x0-len(rownum))+rownum
                if row_index>=self.doc.rows_count():
                    rownum=' '*len(rownum)
                self.app.write(rownum,2)
                self.app.move(Point(x0,y))
                row=' '*w
                if row_index>=0 and row_index<self.doc.rows_count():
                    row=str(self.doc.get_row(row_index))
                    row=row[j0:]
                    if len(row)>w:
                        row=row[0:w]
                    if len(row)<w:
                        row=row+' '*(w-len(row))
                    if not sel is None:
                        if row_index>=sel.tl.y and row_index<=sel.br.y:
                            x=0
                            if row_index==sel.tl.y:
                                x=sel.tl.x
                                self.app.write(row[0:x],1)
                            limit=len(row)
                            if row_index==sel.br.y:
                                limit=sel.br.x
                            self.app.write(row[x:limit],3)
                            if limit<len(row):
                                self.app.write(row[limit:],1)
                        else:
                            self.app.write(row, 1)
                    else:
                        self.app.write(row,1)
                else:
                    self.app.write(row,2)
        self.draw_cursor()
        if not self.active_menu is None:
            self.active_menu.draw(self.app)
        if not self.active_dialog is None:
            self.active_dialog.draw(self.app)
        self.app.refresh()

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
        p=self.cursor-self.offset+Point(self.rownum_width,1)
        self.app.move(p)

    def on_copy(self):
        if not self.selection is None:
            copy(self.get_selected_text())
            return True
        return False

    def on_cut(self):
        if self.on_copy():
            self.delete_selection()

    def on_paste(self):
        curses.ungetch(22)

    def on_file_open(self):
        pass

    def on_file_save(self):
        self.doc.save()

    def on_file_save_as(self):
        pass

    def on_file_exit(self):
        if self.doc.modified:
            self.active_dialog=Dialog('Save File? Y/N')
            self.active_dialog.add_key('Y',self.on_file_save_exit)
            self.active_dialog.add_key('N',self.on_file_discard)
        else:
            raise utils.ExitException()
            
    def on_file_save_exit(self):
        self.doc.save()
        self.on_file_exit()
            
    def on_file_discard(self):
        self.doc.modified=False
        self.on_file_exit()

    def on_help_about(self):
        pass
