from models.cms.core.CMS_ConfigBuider import CMS_ConfigBuilder
from models.cms.core.CMS_Object import *
from models.cms.core.CMS_Operator import EMODL


def test1():
    s = Species('S', 900)
    print(s)

    s2 = Species('R')
    print(s2)

    p = Param('v', 0.00000274)
    print(p)

    p = Pair('S', 'I R')
    print(p)

    p = Pair('S', 'I')
    print(p)

    p = Pair('v')
    print(p)

    p = Pair('v', None)
    print(p)

    p = Pair(None, 0.00000274)
    print(p)

    p = Pair()
    print(p)


def test2():
    r = Reaction('test', '(A::S)', '(A::I)', '(* Ki A::S A::I))')
    print(r)


def test3():
    p = Pair('S', '(* S 0.3)')
    p2 = Pair('S', EMODL.MULTIPLY('S', 0.3))
    print(p)
    print(p2)

    p3 = Pair('S', 'B')
    print(p3)


def test4():
    print(EMODL.ADD(1))
    print(EMODL.ADD('S', 3))
    print(EMODL.ADD('S', 'R', 7))

    print(EMODL.MULTIPLY(1))
    print(EMODL.MULTIPLY('S', 3))
    print(EMODL.MULTIPLY('S', 'R', 7))


def test_param_species():
    cms_cb = CMS_ConfigBuilder('test')

    # add species
    cms_cb.add_species('S', 900)
    cms_cb.add_species('E')

    # add param
    cms_cb.add_param('Ki', 0.0005)
    cms_cb.add_param('Kr', '(/ 1 7)')

    print(cms_cb.get_param('Ki'))
    print(cms_cb.get_species('S'))

    cms_cb.set_param('Ki', '(* 1 7)')
    cms_cb.set_species('S', 10)

    print(cms_cb.get_param('Ki'))
    print(cms_cb.get_species('S'))

    # print(cms_cb.param)
    # print(cms_cb.species)
    print('--------------------')

    # cms_cb.save_to_file('test')


def demo_general():
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
    cms_cb.add_observe('prevalenceB', EMODL.DIVIDE('A::I', EMODL.ADD('A::S', 'A::R')))          # test

    # add param
    cms_cb.add_param('Ki', 0.0005)
    cms_cb.add_param('Kl', 0.2)
    cms_cb.add_param('Kr', '(/ 1 7)')
    cms_cb.add_param('Kw', '(/ 1 135)')
    cms_cb.add_param('Kz', EMODL.DIVIDE(1, 135))     # test

    # add func
    cms_cb.add_func('pre_f', 6)

    # add bool
    cms_cb.add_bool('exitTimeEvent', '(== R 85)')

    # add reaction
    cms_cb.add_reaction('exposure', '(S I)', '(E I)', '(* Ki S I)')
    cms_cb.add_reaction('infection', '(E)', '(I)', '(* Kl E)')
    cms_cb.add_reaction('recovery', '(I)', '(R)', '(* Kr I)')
    cms_cb.add_reaction('waning', '(R)', '(S)', '(* Kw R)')

    # add state event
    cms_cb.add_state_event('test1', 'pre_f', '(S (* S 0.5))', '(V (/ S 2))')
    cms_cb.add_state_event('test2', 'pre_f', Pair('S', '* S 0.5'), Pair('V',  '/ S 2'))
    cms_cb.add_state_event('test3', 'pre_f', Pair('S', EMODL.MULTIPLY('S', 0.5)), Pair('V', EMODL.DIVIDE('S', 2)))

    cms_cb.add_param('temp', 0)
    cms_cb.add_state_event('whack-v', '(> I 25)', Pair('Kv', 0.02))
    cms_cb.add_state_event('whack-!', '(> I 50)', Pair('Kv', 0), Pair('temp', '(* S 0.5)'), Pair('S', '(- S temp)'), Pair('V', '(+ V temp)'))

    # add time event
    cms_cb.add_time_event('test4', 5, '(R (* S 0.3))', '(R (/ S 5))')
    cms_cb.add_time_event('test5', 5, Pair('R', '(* S 0.3)'), Pair('R',  '(/ S 5'))
    cms_cb.add_time_event('test6', 6, 3, Pair('R', EMODL.MULTIPLY('S', 0.3)), Pair('R', EMODL.DIVIDE('S', 5)))
    cms_cb.add_time_event('sia', 50.0, None, Pair('Kv', 0.02))
    cms_cb.add_time_event('end', 80.0, 6, Pair('Kv', 0))

    # output as string
    emodl = cms_cb.to_model()
    print(emodl)


def demo1():
    """
    simplemodel.emodl
    """
    cms_cb = CMS_ConfigBuilder('seir.emodl')

    # add species
    cms_cb.add_species('S', 990)
    cms_cb.add_species('E')
    cms_cb.add_species('I', 10)
    cms_cb.add_species('R')

    # add observe
    cms_cb.add_observe('susceptible', 'S')
    cms_cb.add_observe('exposed', 'E')
    cms_cb.add_observe('infectious', 'I')
    cms_cb.add_observe('recovered', 'R')

    # add param
    cms_cb.add_param('Ki', 0.0005)
    cms_cb.add_param('Kl', 0.2)
    cms_cb.add_param('Kr', '(/ 1 7)')
    cms_cb.add_param('Kw', '(/ 1 135)')

    # add reaction
    cms_cb.add_reaction('exposure', '(S I)', '(E I)', '(* Ki S I)')
    cms_cb.add_reaction('infection', '(E)', '(I)', '(* Kl E)')
    cms_cb.add_reaction('recovery', '(I)', '(R)', '(* Kr I)')
    cms_cb.add_reaction('waning', '(R)', '(S)', '(* Kw R)')

    # output as string
    emodl = cms_cb.to_model()
    print(emodl)


def demo2():
    """
    seirv-sia.emodl
    """

    cms_cb = CMS_ConfigBuilder('seirv-sia.emodl')

    # add species
    cms_cb.add_species('S', 990)
    cms_cb.add_species('E')
    cms_cb.add_species('I', 10)
    cms_cb.add_species('R')
    cms_cb.add_species('V')

    # add observe
    cms_cb.add_observe('susceptible', 'S')
    cms_cb.add_observe('exposed', 'E')
    cms_cb.add_observe('infectious', 'I')
    cms_cb.add_observe('recovered', 'R')
    cms_cb.add_observe('vaccinated', 'V')

    # add param
    cms_cb.add_param('Ki', 0.0005)
    cms_cb.add_param('Kl', 0.2)
    cms_cb.add_param('Kr', 0.143)
    cms_cb.add_param('Kw', 0.0074)
    cms_cb.add_param('Kv', 0)

    # add reaction
    cms_cb.add_reaction('exposure', '(S I)', '(E I)', '(* Ki S I)')
    cms_cb.add_reaction('infection', '(E)', '(I)', '(* Kl E)')
    cms_cb.add_reaction('recovery', '(I)', '(R)', '(* Kr I)')
    cms_cb.add_reaction('waning', '(R)', '(S)', '(* Kw R)')
    cms_cb.add_reaction('vaccination', '(S)', '(V)', '(* Kv S)')

    # add time_event
    cms_cb.add_time_event('sia', 50.0, None, Pair('Kv', 0.02))
    cms_cb.add_time_event('end', 80.0, 6, Pair('Kv', 0))

    # output as string
    emodl = cms_cb.to_model()
    print(emodl)


def demo3():
    """
    seirv-whack.emodl
    """

    cms_cb = CMS_ConfigBuilder('seirv-sia.emodl')

    # add species
    cms_cb.add_species('S', 990)
    cms_cb.add_species('E')
    cms_cb.add_species('I', 10)
    cms_cb.add_species('R')
    cms_cb.add_species('V')

    # add observe
    cms_cb.add_observe('susceptible', 'S')
    cms_cb.add_observe('exposed', 'E')
    cms_cb.add_observe('infectious', 'I')
    cms_cb.add_observe('recovered', 'R')
    cms_cb.add_observe('vaccinated', 'V')

    # add param
    cms_cb.add_param('Ki', 0.0005)
    cms_cb.add_param('Kl', 0.2)
    cms_cb.add_param('Kr', 0.143)
    cms_cb.add_param('Kw', 0.0074)
    cms_cb.add_param('Kv', 0)

    # add reaction
    cms_cb.add_reaction('exposure', '(S I)', '(E I)', '(* Ki S I)')
    cms_cb.add_reaction('infection', '(E)', '(I)', '(* Kl E)')
    cms_cb.add_reaction('recovery', '(I)', '(R)', '(* Kr I)')
    cms_cb.add_reaction('waning', '(R)', '(S)', '(* Kw R)')
    cms_cb.add_reaction('vaccination', '(S)', '(V)', '(* Kv S)')

    # add state_event
    cms_cb.add_param('temp', 0)
    cms_cb.add_state_event('whack-v', '(> I 25)', Pair('Kv', 0.02))
    cms_cb.add_state_event('whack-!', '(> I 50)', Pair('Kv', 0), Pair('temp', '(* S 0.5)'), Pair('S', '(- S temp)'), Pair('V', '(+ V temp)'))

    # output as string
    emodl = cms_cb.to_model()
    print(emodl)


def demo4():
    """
    garki-delay.emodl
    """

    cms_cb = CMS_ConfigBuilder('garki-delay.emodl')

    # add species
    cms_cb.add_species('X1', '(defaults "populations.X1")')
    cms_cb.add_species('X3')
    cms_cb.add_species('Y1', '(defaults "populations.Y1")')
    cms_cb.add_species('Y2')
    cms_cb.add_species('Y3')

    # add func
    cms_cb.add_func('totalpop', '(sum X1 X3 Y1 Y2 Y3)')

    # add observe
    cms_cb.add_observe('susceptible', 'X1')
    cms_cb.add_observe('infectious', 'Y1')
    cms_cb.add_observe('recovered', 'Y2')
    cms_cb.add_observe('immune', '(+ X3 Y3)')
    cms_cb.add_observe('totalpopulation', 'totalpop')

    # add param
    cms_cb.add_param('a', '(defaults "parameters.bitingrate")')
    cms_cb.add_param('alpha1', '(defaults "parameters.infectivityloss")')
    cms_cb.add_param('alpha2', '(defaults "parameters.transitiontofast")')
    cms_cb.add_param('delta', '(defaults "parameters.birthrate")')
    cms_cb.add_param('g', '(defaults "parameters.susceptibility"))')
    cms_cb.add_param('r1', '(defaults "parameters.slowrecovery")')
    cms_cb.add_param('r2', '(defaults "parameters.fastrecovery")')

    cms_cb.add_param('N', 15)       # incubation in human
    cms_cb.add_param('n', 10)       # incubation in mosquito

    # add func
    # seasonal parameter
    cms_cb.add_func('C', '(* 0.2 (+ 1.0 (sin (* (/ time 365) 2 pi))))')
    # infection rate
    cms_cb.add_func('h', '(+ (* g (- 1 (exp (/ (* (- C) Y1) totalpop)))) 0.0001)')

    # seasonal parameter
    cms_cb.add_func('C_test', EMODL.MULTIPLY(0.2, EMODL.ADD(1.0, EMODL.SIN(EMODL.MULTIPLY(EMODL.DIVIDE('time', 365), 2, 'pi')))))

    # infection rate
    cms_cb.add_func('h_test', EMODL.ADD(EMODL.MULTIPLY('g', EMODL.SUBTRACT(1, EMODL.EXP(EMODL.DIVIDE(EMODL.MULTIPLY(EMODL.NEGATE('C'), 'Y1'), 'totalpop')))), 0.0001))

    # add reaction
    cms_cb.add_reaction('birth', '()', '(X1)', '(* delta totalpop)')
    cms_cb.add_reaction('deathX1', '(X1)', '()', '(* X1 delta)')
    cms_cb.add_reaction('deathX3', '(X3)', '()', '(* X3 delta)')
    cms_cb.add_reaction('deathY1', '(Y1)', '()', '(* Y1 delta)')
    cms_cb.add_reaction('deathY2', '(Y2)', '()', '(* Y2 delta)')
    cms_cb.add_reaction('deathY3', '(Y3)', '()', '(* Y3 delta)')
    cms_cb.add_reaction('infectX1', '(X1)', '(Y1)', '(* X1 h) N')
    cms_cb.add_reaction('recoveryY2', '(Y2)', '(X1)', '(/ (* Y2 h) (- (exp (/ h r1)) 1))')
    cms_cb.add_reaction('lossinfectY1', '(Y1)', '(Y2)', '(* Y1 alpha1)')
    cms_cb.add_reaction('acquireimmunityY2', '(Y2)', '(Y3)', '(* Y2 alpha2)')
    cms_cb.add_reaction('recoveryY3', '(Y3)', '(X3)', '(/ (* Y3 h) (- (exp (/ h r2)) 1))')
    cms_cb.add_reaction('infectX3', '(X3)', '(Y3)', '(* X3 h) N')

    # output as string
    emodl = cms_cb.to_model()
    print(emodl)


def demo5():
    """
    figure-1a.emodl
    """

    cms_cb = CMS_ConfigBuilder('tb-core-model')

    # add species
    cms_cb.add_species('S', 15000000)           # 15,000,000
    cms_cb.add_species('L')
    cms_cb.add_species('I', 405000)             # 0.45 * 900,000 = 405,000
    cms_cb.add_species('N', 495000)             # 0.55 * 900,000 = 495,000

    cms_cb.add_species('B')                     # track births
    cms_cb.add_species('D')                     # track natural deaths
    cms_cb.add_species('DD')                    # track disease deaths

    # add param
    cms_cb.add_param('alpha', 0.115)            # proportion of infections developing primary TB [p.18]
    cms_cb.add_param('sigma', 0.45)             # proportion of cases developing smear positive TB [p.19]
    cms_cb.add_param('v', 0.00000274)           # rate at which latently infected individuals develop active TB (0.10%/year) [p.18]
    cms_cb.add_param('x', 0.65)                 # protection provided by prior infection [p.18-19]
    cms_cb.add_param('theta', 0.000041)         # rate of conversion from smear negative to smear positive TB (1.5%/year) [p.20]

    cms_cb.add_param('gamma', 0.0022)           # screening rate (80%/year)
    cms_cb.add_param('sei', 0.9)                # sensitivity of screening, smear positive (0.44-1.0)
    cms_cb.add_param('sen', 0.9)                # sensitivity of screening, smear negative (0.44-1.0)
    cms_cb.add_param('eta', 0.8)                # proportion linked to care
    cms_cb.add_param('tau', 0.9)                # treatment success
    cms_cb.add_param('r', 0.000548)             # self cure rate (20%/year) [p.20-21]
    cms_cb.add_param('d', 0.2)                  # relative screening rate of smear-negative cases

    cms_cb.add_param('omega', 0.00003425)       # birth rate
    cms_cb.add_param('mu', 0.00003425)          # natural mortality rate
    cms_cb.add_param('mui', 0.00003425)         # mortality rate, smear positive (1x natural rate, additive)
    cms_cb.add_param('mun', 0.00003425)         # mortality rate, smear negative (1x natural rate, additive)

    cms_cb.add_param('beta', 0.0603)            # effective contact rate (22/year) [p.23]
    cms_cb.add_param('c', 22)                   # relative infectiousness of smear-negative cases [p.19]

    # add func
    cms_cb.add_func('pop', '(+ S L I N)')
    cms_cb.add_func('lambda', '(/ (* beta (+ I (* c N))) pop)')

    # add reaction
    cms_cb.add_reaction('infection-latent', '(S)', '(L)', '(* lambda (- 1 alpha) S)')
    cms_cb.add_reaction('infection-positive', '(S)', '(I)', '(* lambda alpha sigma S)')
    cms_cb.add_reaction('infection-negative', '(S)', '(N)', '(* lambda alpha (- 1 sigma) S)')

    cms_cb.add_reaction('reactivation-positive', '(L)', '(I)', '(* v sigma L)')
    cms_cb.add_reaction('reinfection-positive', '(L)', '(I)', '(* lambda alpha (- 1 x) sigma L)')
    cms_cb.add_reaction('reactivation-negative ', '(L)', '(I)', '(* v (- 1 sigma) L)')
    cms_cb.add_reaction('reinfection-negative', '(L)', '(I)', '(* lambda alpha (- 1 x) (- 1 sigma) L)')

    cms_cb.add_reaction('conversion', '(N)', '(I)', '(* theta N)')

    cms_cb.add_reaction('treatment-positive', '(I)', '(L)', '(* gamma sei eta tau I)')
    cms_cb.add_reaction('natural-positive', '(I)', '(L)', '(* r I)')
    cms_cb.add_reaction('treatment-negative', '(N)', '(L)', '(* gamma sen eta tau d N)')
    cms_cb.add_reaction('natural-negative', '(N)', '(L)', '(* r N)')

    cms_cb.add_reaction('birth', '()', '(S B)', '(* omega pop)')
    cms_cb.add_reaction('death-s', '(S)', '(D)', '(* mu S)')
    cms_cb.add_reaction('death-l', '(L)', '(D)', '(* mu L)')
    cms_cb.add_reaction('death-i', '(I)', '(D)', '(* mu I)')
    cms_cb.add_reaction('disease-death-i', '(I)', '(DD)', '(* mui I)')
    cms_cb.add_reaction('death-n', '(N)', '(D)', '(* mu N)')
    cms_cb.add_reaction('disease-death-n', '(N)', '(DD)', '(* mun N)')

    # add observe
    cms_cb.add_observe('population', 'pop')

    cms_cb.add_observe('susceptible', 'S')
    cms_cb.add_observe('latent', 'L')
    cms_cb.add_observe('smear-positive', 'I')
    cms_cb.add_observe('smear-negative', 'N')

    cms_cb.add_observe('births', 'B')
    cms_cb.add_observe('deaths', 'D')
    cms_cb.add_observe('tb-deaths', 'DD')

    # output as string
    emodl = cms_cb.to_model()
    print(emodl)


def demo5_test():
    """
    figure-1a.emodl
    """

    cms_cb = CMS_ConfigBuilder('tb-core-model')

    # add species
    cms_cb.add_species('S', 15000000)           # 15,000,000
    cms_cb.add_species('L')
    cms_cb.add_species('I', 405000)             # 0.45 * 900,000 = 405,000
    cms_cb.add_species('N', 495000)             # 0.55 * 900,000 = 495,000

    cms_cb.add_species('B')                     # track births
    cms_cb.add_species('D')                     # track natural deaths
    cms_cb.add_species('DD')                    # track disease deaths

    # add param
    cms_cb.add_param('alpha', 0.115)            # proportion of infections developing primary TB [p.18]
    cms_cb.add_param('sigma', 0.45)             # proportion of cases developing smear positive TB [p.19]
    cms_cb.add_param('v', 0.00000274)           # rate at which latently infected individuals develop active TB (0.10%/year) [p.18]
    cms_cb.add_param('x', 0.65)                 # protection provided by prior infection [p.18-19]
    cms_cb.add_param('theta', 0.000041)         # rate of conversion from smear negative to smear positive TB (1.5%/year) [p.20]

    cms_cb.add_param('gamma', 0.0022)           # screening rate (80%/year)
    cms_cb.add_param('sei', 0.9)                # sensitivity of screening, smear positive (0.44-1.0)
    cms_cb.add_param('sen', 0.9)                # sensitivity of screening, smear negative (0.44-1.0)
    cms_cb.add_param('eta', 0.8)                # proportion linked to care
    cms_cb.add_param('tau', 0.9)                # treatment success
    cms_cb.add_param('r', 0.000548)             # self cure rate (20%/year) [p.20-21]
    cms_cb.add_param('d', 0.2)                  # relative screening rate of smear-negative cases

    cms_cb.add_param('omega', 0.00003425)       # birth rate
    cms_cb.add_param('mu', 0.00003425)          # natural mortality rate
    cms_cb.add_param('mui', 0.00003425)         # mortality rate, smear positive (1x natural rate, additive)
    cms_cb.add_param('mun', 0.00003425)         # mortality rate, smear negative (1x natural rate, additive)

    cms_cb.add_param('beta', 0.0603)            # effective contact rate (22/year) [p.23]
    cms_cb.add_param('c', 22)                   # relative infectiousness of smear-negative cases [p.19]

    # add func
    cms_cb.add_func('pop', '(+ S L I N)')
    cms_cb.add_func('pop', EMODL.ADD('S', 'L', 'I', 'N'))

    cms_cb.add_func('lambda', '(/ (* beta (+ I (* c N))) pop)')
    cms_cb.add_func('lambda', EMODL.DIVIDE(EMODL.MULTIPLY('beta', EMODL.ADD('I', EMODL.MULTIPLY('c', 'N'))), 'pop'))

    # add reaction
    cms_cb.add_reaction('infection-latent', '(S)', '(L)', '(* lambda (- 1 alpha) S)')
    cms_cb.add_reaction('infection-latent', '(S)', '(L)', EMODL.MULTIPLY('lambda', EMODL.SUBTRACT(1, 'alpha'), 'S'))

    cms_cb.add_reaction('infection-positive', '(S)', '(I)', '(* lambda alpha sigma S)')
    cms_cb.add_reaction('infection-positive', '(S)', '(I)', EMODL.MULTIPLY('lambda', 'alpha', 'sigma', 'S'))

    cms_cb.add_reaction('infection-negative', '(S)', '(N)', '(* lambda alpha (- 1 sigma) S)')
    cms_cb.add_reaction('infection-negative', '(S)', '(N)', EMODL.MULTIPLY('lambda', 'alpha', EMODL.SUBTRACT(1, 'sigma'), 'S'))

    cms_cb.add_reaction('reactivation-positive', '(L)', '(I)', '(* v sigma L)')
    cms_cb.add_reaction('reactivation-positive', '(L)', '(I)', EMODL.MULTIPLY('v', 'sigma', 'L'))

    cms_cb.add_reaction('reinfection-positive', '(L)', '(I)', '(* lambda alpha (- 1 x) sigma L)')
    cms_cb.add_reaction('reinfection-positive', '(L)', '(I)', EMODL.MULTIPLY('lambda', 'alpha', EMODL.SUBTRACT(1, 'x'), 'sigma', 'L'))

    cms_cb.add_reaction('reactivation-negative ', '(L)', '(I)', '(* v (- 1 sigma) L)')
    cms_cb.add_reaction('reactivation-negative ', '(L)', '(I)', EMODL.MULTIPLY('v', EMODL.SUBTRACT(1, 'sigma'), 'L'))

    cms_cb.add_reaction('reinfection-negative', '(L)', '(I)', '(* lambda alpha (- 1 x) (- 1 sigma) L)')
    cms_cb.add_reaction('reinfection-negative', '(L)', '(I)', EMODL.MULTIPLY('lambda', 'alpha', EMODL.SUBTRACT(1, 'x'), EMODL.SUBTRACT(1, 'sigma'), 'L'))

    cms_cb.add_reaction('conversion', '(N)', '(I)', '(* theta N)')
    cms_cb.add_reaction('conversion', '(N)', '(I)', EMODL.MULTIPLY('theta', 'N'))

    cms_cb.add_reaction('treatment-positive', '(I)', '(L)', '(* gamma sei eta tau I)')
    cms_cb.add_reaction('treatment-positive', '(I)', '(L)', EMODL.MULTIPLY('gamma', 'sei', 'eta', 'tau', 'I'))

    cms_cb.add_reaction('natural-positive', '(I)', '(L)', '(* r I)')
    cms_cb.add_reaction('natural-positive', '(I)', '(L)', EMODL.MULTIPLY('r', 'I'))

    cms_cb.add_reaction('treatment-negative', '(N)', '(L)', '(* gamma sen eta tau d N)')
    cms_cb.add_reaction('treatment-negative', '(N)', '(L)', EMODL.MULTIPLY('gamma', 'sen', 'eta', 'tau', 'd', 'N'))

    cms_cb.add_reaction('natural-negative', '(N)', '(L)', '(* r N)')
    cms_cb.add_reaction('natural-negative', '(N)', '(L)', EMODL.MULTIPLY('r', 'N'))

    cms_cb.add_reaction('birth', '()', '(S B)', '(* omega pop)')
    cms_cb.add_reaction('birth', '()', Pair('S', 'B'), EMODL.MULTIPLY('omega', 'pop'))

    cms_cb.add_reaction('death-s', '(S)', '(D)', '(* mu S)')
    cms_cb.add_reaction('death-s', '(S)', '(D)', EMODL.MULTIPLY('mu', 'S'))

    cms_cb.add_reaction('death-l', '(L)', '(D)', '(* mu L)')
    cms_cb.add_reaction('death-l', '(L)', '(D)', EMODL.MULTIPLY('mu', 'L'))

    cms_cb.add_reaction('death-i', '(I)', '(D)', '(* mu I)')
    cms_cb.add_reaction('death-i', '(I)', '(D)', EMODL.MULTIPLY('mu', 'I'))

    cms_cb.add_reaction('disease-death-i', '(I)', '(DD)', '(* mui I)')
    cms_cb.add_reaction('disease-death-i', '(I)', '(DD)', EMODL.MULTIPLY('mui', 'I'))

    cms_cb.add_reaction('death-n', '(N)', '(D)', '(* mu N)')
    cms_cb.add_reaction('death-n', '(N)', '(D)', EMODL.MULTIPLY('mu', 'N'))

    cms_cb.add_reaction('disease-death-n', '(N)', '(DD)', '(* mun N)')
    cms_cb.add_reaction('disease-death-n', '(N)', '(DD)', EMODL.MULTIPLY('mun', 'N'))

    # add observe
    cms_cb.add_observe('population', 'pop')

    cms_cb.add_observe('susceptible', 'S')
    cms_cb.add_observe('latent', 'L')
    cms_cb.add_observe('smear-positive', 'I')
    cms_cb.add_observe('smear-negative', 'N')

    cms_cb.add_observe('births', 'B')
    cms_cb.add_observe('deaths', 'D')
    cms_cb.add_observe('tb-deaths', 'DD')

    # output as string
    emodl = cms_cb.to_model()
    print(emodl)


def test():
    # test1()
    # test2()
    # test3()
    # test4()
    # test_param_species()
    pass


def demo():
    # demo1()           # simplemodel.emodl
    # demo2()           # seirv-sia.emodl
    # demo3()           # seirv-whack.emodl
    # demo4()           # garki-delay.emodl
    demo5()           # figure-1a.emodl
    # demo5_test()
    # demo_general()
    pass


if __name__ == "__main__":

    test()
    demo()
    pass