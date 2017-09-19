from ptypes import Point

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
            pass
            #message_box('Failed to open {}'.format(filename))

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
