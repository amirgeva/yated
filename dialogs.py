from ptypes import Point, Rect


class Dialog(object):
    def __init__(self,prompt):
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
        w=app.width
        h=app.height
        y=int(h/2 - 4)
        rect=Rect(10,y,w-10,y+8)
        app.draw_frame(rect,4)
        app.fill_rect(Rect(rect).inflate(-1),' ',4)
        app.move(Point(14,y+4))
        app.write(self.prompt,4)
