import sys


class OutputMessage:
    deprecation_list = list()

    def __init__(self, msg, style='regular'):

        self.style = style

        if self.style == 'bold':
            self.bold(msg)

        elif self.style == 'regular':
            self.regular(msg)

        elif self.style == 'flushed':
            self.flushed(msg)

        elif self.style == 'deprecate':
            # Avoid warning the user multiple times
            if msg not in OutputMessage.deprecation_list:
                OutputMessage.deprecation_list.append(msg)
                self.deprecate(msg)

    def bold(self, msg):
        print
        print "=================================================="
        print msg.upper()
        print "=================================================="
        print

    def deprecate(self, msg):
        print "/!\\ DEPRECATION WARNING /!\\"
        print msg

    def regular(self, msg):
        print
        print msg
        print

    def flushed(self, msg):
        sys.stdout.write('\r')
        sys.stdout.write(msg)
        sys.stdout.flush()
