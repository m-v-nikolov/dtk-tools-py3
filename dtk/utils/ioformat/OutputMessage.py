import sys 

class OutputMessage():
    
    def __init__(self, msg, style = 'regular'):

        self.style = style
        
        if self.style == 'bold':
            self.bold(msg)
            
        if self.style == 'regular':
            self.regular(msg)
            
        if self.style == 'flushed':
            self.flushed(msg)
        
    
    def bold(self, msg):
        
        print
        print "=================================================="
        print msg.upper()
        print "=================================================="
        print
        
        
        
    def regular(self, msg):
        print 
        print msg
        print
        
    
    def flushed(self, msg):
        sys.stdout.write('\r')
        sys.stdout.write(msg)
        sys.stdout.flush()