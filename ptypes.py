#!/usr/bin/env python


class Point(object):
    def __init__(self,*args):
        if len(args)==2:
            self.x=args[0]
            self.y=args[1]
        elif len(args)==1:
            if isinstance(args[0],Point):
                self.x=args[0].x
                self.y=args[0].y
            elif isinstance(args[0],tuple):
                self.x=args[0][0]
                self.y=args[0][1]
            else:
                raise TypeError()
                
    def __str__(self):
        return '{},{}'.format(self.x,self.y)
        
    def __eq__(self,p):
        if not isinstance(p,Point):
            p=Point(p)
        return self.x==p.x and self.y==p.y
        
    def __ne__(self,p):
        return not (self==p)

    def __iadd__(self,p):
        if not isinstance(p,Point):
            p=Point(p)
        self.x+=p.x
        self.y+=p.y
        return self

    def __isub__(self,p):
        if not isinstance(p,Point):
            p=Point(p)
        self.x-=p.x
        self.y-=p.y
        return self

    def __add__(self,p):
        if not isinstance(p,Point):
            p=Point(p)
        return Point(self.x+p.x,self.y+p.y)
    
    def __sub__(self,p):
        if not isinstance(p,Point):
            p=Point(p)
        return Point(self.x-p.x,self.y-p.y)

class Rect(object):
    def __init__(self,*args):
        if len(args)==2 and isinstance(args[0],Point) and isinstance(args[1],Point):
            self.tl=args[0]
            self.br=args[1]
        elif len(args)==4:
            self.tl=Point(args[0],args[1])
            self.br=Point(args[2],args[3])
        elif len(args)==1 and isinstance(args[0],Rect):
            self.tl=args[0].tl
            self.br=args[0].br
        else:
            raise TypeError()
            
    def is_point_inside(self,p):
        if not isinstance(p,Point):
            p=Point(p)
        return p.x>=self.tl.x and p.y>=self.tl.y and p.x<self.br.x and p.y<self.br.y

def unit_test():
    p1=Point(1,2)
    p2=Point((1,2))
    p3=Point(p1)
    s1=str(p1)
    s2=str(p2)
    s3=str(p3)
    if s1!=s2 or s1!=s3:
        print "Mismatch"
    print p1+p2
                
if __name__=='__main__':
    unit_test()
    