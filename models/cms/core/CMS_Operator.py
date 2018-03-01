import inspect


class EMODL:

    @classmethod
    def all_options(cls):
        return (cls_attribute for cls_attribute in cls.__dict__.values()
                if inspect.isclass(cls_attribute))

    class ADD:
        def __init__(self, *kwargs):
            self.values = kwargs

        def __repr__(self):
            if len(self.values) == 1:
                return "{}".format(self.values[0])
            if len(self.values) == 2:
                return "(+ {} {})".format(*self.values)
            return "(sum {})".format(" ".join((str(v) for v in self.values)))

    class SUBTRACT:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __repr__(self):
            return "(- {} {})".format(self.x, self.y)

    class MULTIPLY:
        def __init__(self, *kwargs):
            self.values = kwargs

        def __repr__(self):
            if len(self.values) == 1:
                return "{}".format(self.values[0])

            return "(* {})".format(" ".join((str(v) for v in self.values)))

    class DIVIDE:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __repr__(self):
            return "(/ {} {})".format(self.x,self.y)

    class POWER:
        def __init__(self, x, y, p=False):
            self.x = x
            self.y = y
            self.p = p

        def __repr__(self):
            if self.p:
                return "(pow {} {})".format(self.x,self.y)
            else:
                return "(^ {} {})".format(self.x, self.y)

    class MIN:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __repr__(self):
            return "(min {} {})".format(self.x,self.y)

    class MAX:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __repr__(self):
            return "(max {} {})".format(self.x, self.y)

    class UNIFORM:
        def __init__(self, min, max):
            self.min = min
            self.max = max

        def __repr__(self):
            return "(uniform {} {})".format(self.min, self.max)

    class NORMAL:
        def __init__(self, mean, var, g=False):
            self.mean = min
            self.var = max
            self.g = g

        def __repr__(self):
            if self.g:
                return "(gaussian {} {})".format(self.mean, self.var)
            else:
                return "(normal {} {})".format(self.mean, self.var)

    class NEGATE:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(- {})".format(self.x)

    class EXP:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(exp {})".format(self.x)

    class LOG:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(ln {})".format(self.x)

    class SIN:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(sin {})".format(self.x)

    class COS:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(cos {})".format(self.x)

    class ABS:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(abs {})".format(self.x)

    class FLOOR:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(floor {})".format(self.x)

    class CEIL:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(ceil {})".format(self.x)

    class SQRT:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(sqrt {})".format(self.x)

    class STEP:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "(step {})".format(self.x)

    class EMPIRICAL:
        def __init__(self, filename):
            self.filename = filename

        def __repr__(self):
            return '(empirical "{}"'.format(self.filename)


def test():
    # print(EMODL.ADD(EMODL.DIVIDE(3, 4), EMODL.POWER(2, 5)))
    # print(EMODL.ADD('S', 'R'))
    # print(EMODL.ADD(2, 3, 'S', 'R', 4))

    a = EMODL.all_options()
    print(type(a))
    print(a)

    print('-------------------------------------')
    for r in a:
        print(r)


if __name__ == "__main__":
    test()


