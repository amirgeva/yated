#import


class Menu(object):
    def __init__(self,title):
        self.title=title
        self.items=[]
        
    def add_item(self,title,action=None):
        self.items.append((title,action))
        
