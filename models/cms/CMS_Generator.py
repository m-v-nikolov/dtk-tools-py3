from models.cms.core.CMS_ConfigBuider import CMS_ConfigBuilder
from models.cms.core.CMS_Object import *
from models.cms.core.CMS_Operator import EMODL


def demo1():
    s = Species('S', 900)
    print(s)

    s2 = Species('R')
    print(s2)


def demo2():
    r = Reaction('test', 'A::S', 'A::I', '* Ki A::S A::I)')
    print(r)


def demo3():
    p = Pair('S', '* S 0.3')
    p2 = Pair('S', EMODL.MULTIPLY('S', 0.3))
    print(p)
    print(p2)


def demo4():
    print(EMODL.ADD(1))
    print(EMODL.ADD('S', 3))
    print(EMODL.ADD('S', 'R', 7))

    print(EMODL.MULTIPLY(1))
    print(EMODL.MULTIPLY('S', 3))
    print(EMODL.MULTIPLY('S', 'R', 7))



def main():
    cms_cb = CMS_ConfigBuilder('seir.emodl')
    # print(cms_cb)

    # add species
    cms_cb.add_species('S', 900)
    cms_cb.add_species('E')
    cms_cb.add_species('I', 10)
    cms_cb.add_species('R')

    # add observe
    cms_cb.add_observe('susceptible', 'S')
    cms_cb.add_observe('exposed', 'E')
    cms_cb.add_observe('infectious', 'I')
    cms_cb.add_observe('recovered', 'R')
    cms_cb.add_observe('prevalenceA', '(/ A::I (sum A::S A::R))')                               # test
    cms_cb.add_observe('prevalenceB', EMODL.DIVIDE('A::I', EMODL.ADD('A::S', 'A::R', True)))    # test

    # add param
    cms_cb.add_param('Ki', 0.0005)
    cms_cb.add_param('Kl', 0.2)
    cms_cb.add_param('Kr', '(/ 1 7)')
    cms_cb.add_param('Kw', '(/ 1 135)')
    cms_cb.add_param('Kz', EMODL.DIVIDE(1, 135))     # test

    # add start event
    cms_cb.add_state_event('test1', '(S (* S 0.5))', '(V (/ S 2))')
    cms_cb.add_state_event('test2', Pair('S', '* S 0.5'), Pair('V',  '/ S 2'))
    cms_cb.add_state_event('test3', Pair('S', EMODL.MULTIPLY('S', 0.5)), Pair('V', EMODL.DIVIDE('S', 2)))

    # add time event
    cms_cb.add_time_event('test4', '(R (* S 0.3))', '(R (/ S 5))')
    cms_cb.add_time_event('test5', Pair('R', '* S 0.3 '), Pair('R',  '/ S 5'))
    cms_cb.add_time_event('test6', Pair('R', EMODL.MULTIPLY('S', 0.3)), Pair('R', EMODL.DIVIDE('S', 5)))

    # add reaction
    cms_cb.add_reaction('exposure', 'S I', 'E I', '* Ki S I')
    cms_cb.add_reaction('infection', 'E', 'I', '* Kl E')
    cms_cb.add_reaction('recovery', 'I', 'R', '* Kr I')
    cms_cb.add_reaction('waning', 'R', 'S', '* Kw R')

    # output as string
    emodl = cms_cb.to_model()
    print(emodl)


if __name__ == "__main__":
    main()

    # demo1()
    # demo2()
    # demo3()
    # demo4()
    pass