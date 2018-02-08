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
    def __init__(self, name, value):
        self.name = name
        self.value = str(value)

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


class StateEvent(object):
    def __init__(self, name, predicate, *pair_list):
        self.name = name
        self.predicate = predicate
        self.pair_list = (str(p) for p in pair_list)

    def __repr__(self):
        return "(state-event {} {} ({}))".format(self.name, self.predicate, ' '.join(self.pair_list))


class TimeEvent(object):
    def __init__(self, name, time, iterations=None, *pair_list):
        self.name = name
        self.time = time
        self.iterations = iterations
        self.pair_list = (str(p) for p in pair_list)

    def __repr__(self):
        if self.iterations:
            return "(time-event {} {} {} ({}))".format(self.name, self.time, self.iterations, ' '.join(self.pair_list))
        else:
            return "(time-event {} {} ({}))".format(self.name, self.time, ' '.join(self.pair_list))


class Reaction(object):
    def __init__(self, name, input, output, func):
        self.name = name
        self.input = input
        self.output = output
        self.func = func

    def __repr__(self):
        return "(reaction {} {} {} {})".format(self.name, self.input, self.output, self.func)


class Pair(object):
    def __init__(self, first=None, second=None):
        self.first = first
        self.second = second

        if (first and second is None) or (second and first is None):
            print('')

    def __repr__(self):
        second = str(self.second).strip()
        if self.first and self.second is None:
            return "({})".format(self.first)
        elif self.second and self.first is None:
            return "({})".format(self.second)
        elif self.first is None and self.second is None:
            return "()"
        else:
            return "({} {})".format(self.first, second)


class Locale(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "(locale {})".format(self.name)
