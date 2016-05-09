class OutputMessage():
    
    def __init__(self, msg, style = 'regular'):

        self.style = style
        
        if self.style == 'bold':
            self.bold(msg)
            
        if self.style == 'regular':
            self.regular(msg)
        
    
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
        