
# [TODO]: may not need this class!
class StartModel(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '(start-model "{}")'.format(self.name)


class Species(object):
    def __init__(self, name, value=None):
        self.name = name
        self.value = str(value) if value else value

    def __repr__(self):
        if self.value:
            return "(species {} {})".format(self.name, self.value)
        else:
            return "(species {})".format(self.name)


class Observe(object):
    def __init__(self, label, func):
        self.label = label
        self.func = func

    def __repr__(self):
        return "(observe {} {})".format(self.label, self.func)


class Param(object):
    def __init__(self, name, value=None):
        self.name = name
        self.value = str(value) if value else value

    def __repr__(self):
        return "(param {} {})".format(self.name, self.value)


class Bool(object):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def __repr__(self):
        return "(bool {} {})".format(self.name, self.expr)


class Func(object):
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __repr__(self):
        return "(func {} {})".format(self.name, self.func)

    def to_model(self):
        pass


class StateEvent(object):
    def __init__(self, name, *pair_list):
        self.name = name
        self.pair_list = (str(p) for p in pair_list)

    def __repr__(self):
        return "(state-event {} predicate ({}))".format(self.name, ' '.join(self.pair_list))


class TimeEvent(object):
    def __init__(self, name, *pair_list):
        self.name = name
        self.pair_list = (str(p) for p in pair_list)

    def __repr__(self):
        return "(time-event {} time ({}))".format(self.name, ' '.join(self.pair_list))


class Reaction(object):
    def __init__(self, name, input, output, func):
        self.name = name
        self.input = input
        self.output = output
        self.func = func

    def __repr__(self):
        return "(reaction {} ({}) ({}) ({}))".format(self.name, self.input, self.output, self.func)


class Pair(object):
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __repr__(self):
        second = str(self.second).strip()
        if second.startswith('(') and second.endswith(')'):
            return "({} {})".format(self.first, second)
        else:
            return "({} ({}))".format(self.first, second)
