from ptypes import Point, Rect
import config
import curses

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
    
    