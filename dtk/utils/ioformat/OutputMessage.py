import sys


class OutputMessage:
    deprecation_list = list()

    def __init__(self, msg, style='regular'):

        self.style = style

        if self.style == 'deprecate':
            # Avoid warning the user multiple times
            if msg not in OutputMessage.deprecation_list:
                OutputMessage.deprecation_list.append(msg)
                self.deprecate(msg)
        else:
            func = getattr(self, style)
            func(msg)

    def bold(self, msg):
        print()
        print( "==================================================")
        print( msg.upper())
        print( "==================================================")
        print()

    def deprecate(self, msg):
        print( "/!\\ DEPRECATION WARNING /!\\")
        print( msg)

    def regular(self, msg):
        print()
        print( msg)
        print()

    def warning(self, msg):
        print()
        print( "/!\\ %s /!\\" % msg)
        print()

    def flushed(self, msg):
        sys.stdout.write('\r')
        sys.stdout.write(msg)
        sys.stdout.flush()
