from ptypes import Point, Rect
import config
import curses
import os

class Dialog(object):
    def __init__(self,width,height):
        self.width=width
        self.height=height
        
    def draw(self,app):
        cx=int(app.width/2)
        cy=int(app.height/2)
        y=int(cy - self.height/2)
        x=int(cx - self.width/2)
        self.rect=Rect(x,y,x+self.width,y+self.height)
        app.draw_frame(self.rect,4)
        app.fill_rect(Rect(self.rect).inflate(-1),' ',4)

class MessageBox(Dialog):
    def __init__(self,prompt):
        super(MessageBox,self).__init__(60,8)
        self.prompt=prompt
        self.actions={}

    def add_key(self,key,action):
        self.actions[key.lower()]=action
        self.actions[key.upper()]=action
        
    def process_key(self,key):
        if key in self.actions:
            return self.actions.get(key)
        return None

    def draw(self,app):
        super(MessageBox,self).draw(app)
        app.move(Point(self.rect.tl.x+4,self.rect.tl.y+4))
        app.write(self.prompt,4)
        
class FileDialog(Dialog):
    def __init__(self,action):
        super(FileDialog,self).__init__(60,20)
        self.dir=os.getcwd()
        self.browse_mode=True
        self.edit_text=''
        self.ofs=0
        self.cur=0
        self.items=[]
        self.fill_items()
        self.action=action
    
    def fill_items(self):
        l=os.listdir(self.dir)
        for i in range(0,len(l)):
            name=l[i]
            path=os.path.join(self.dir,name)
            if os.path.isdir(path):
                name=name+'/'
            l[i]=name
        l.insert(0,'../')
        self.items=l

    def draw(self,app):
        super(FileDialog,self).draw(app)
        pos=self.rect.tl+Point(1,1)
        app.move(pos)
        app.write(self.dir+'/',1)
        self.editpos=pos+(len(self.dir)+1,0)
        pos+=(2,1)
        for i in range(0,17):
            idx=i+self.ofs
            app.move(pos)
            if idx<len(self.items):
                attr=0
                if self.cur==idx:
                    attr=curses.A_REVERSE
                s=self.items[idx]
                if len(s)>50:
                    s=s[0:50]
                if len(s)<50:
                    s=s+' '*(50-len(s))
                app.write(s,4,attr)
            else:
                app.write(' '*50,4)
            pos+=(0,1)
        if not self.browse_mode:
            app.move(self.editpos)
            app.write(self.edit_text,1)
        
    def process_key(self,key):
        if self.browse_mode:
            if key=='\011': # tab
                self.browse_mode=False
            if key=='KEY_DOWN':
                self.cur=(self.cur+1)%len(self.items)
            if key=='KEY_UP':
                self.cur=(self.cur-1)%len(self.items)
            if key=='KEY_END':
                self.cur=len(self.items)-1
            if key=='KEY_HOME':
                self.cur=0
            if key=='KEY_PPAGE':
                self.cur=(self.cur-17)%len(self.items)
            if key=='KEY_NPAGE':
                self.cur=(self.cur+17)%len(self.items)
            if key=='\012': # Enter
                name=self.items[self.cur]
                path=os.path.abspath(os.path.join(self.dir,name))
                if name.endswith('/'):
                    self.dir=path
                    self.fill_items()
                else:
                    return lambda: self.action(path)
            if self.cur<self.ofs or self.cur>=(self.ofs+17):
                self.ofs=self.cur-8
                if self.ofs<0:
                    self.ofs=0
        else:
            if key=='\011': # tab
                self.browse_mode=True
            if len(key)==1 and ord(key)>32 and ord(key)<128:
                self.edit_text+=key
            if key=='KEY_BACKSPACE' and len(self.edit_text)>0:
                self.edit_text=self.edit_text[0:-1]
            if key=='\012':
                path=os.path.abspath(os.path.join(self.dir,self.edit_text))
                return lambda: self.action(path)
        return None
    

class ConfigDialog(Dialog):
    def __init__(self):
        super(ConfigDialog,self).__init__(60,20)

    def draw(self,app):
        super(ConfigDialog,self).draw(app)
        pos=self.rect.tl+Point(2,2)
        #for item in self.items:
            

class ColorConfigDialog(Dialog):
    def __init__(self):
        super(ColorConfigDialog,self).__init__(60,15)
        self.cur=1

    def draw(self,app):
        super(ColorConfigDialog,self).draw(app)
        pos=self.rect.tl+Point(2,2)
        for i in range(1,8):
            app.move(pos)
            attr=0
            if i==self.cur:
                attr=curses.A_REVERSE
            app.write('Color {}  '.format(i),4,attr)
            app.write('ABC',i)
            pos+=(0,1)
        pos+=Point(8,1)
        app.move(pos)
        app.write('Use left/right pgup/pgdn to change colors',4)
        app.move(pos+(0,1))
        app.write('Esc when done',4)
            
    def process_key(self,key):
        if key=='KEY_DOWN':
            self.cur=1+(self.cur%7)
        if key=='KEY_UP':
            self.cur=1+((self.cur-2)%7)

        fg=config.getint('fg{}'.format(self.cur))
        bg=config.getint('bg{}'.format(self.cur))
        if key=='KEY_LEFT':
            fg=(fg-1)%8
        if key=='KEY_RIGHT':
            fg=(fg+1)%8
        if key=='KEY_PPAGE':
            bg=(bg-1)%8
        if key=='KEY_NPAGE':
            bg=(bg+1)%8
        config.set('fg{}'.format(self.cur),fg)
        config.set('bg{}'.format(self.cur),bg)
        curses.init_pair(self.cur,fg,bg)
        return None
    
