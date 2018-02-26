import os
import re


class CMSParser(object):
    """
    With current version it only supports the following key CMS components:
     - start-model
     - reaction
     - param
     - func
     - bool
     - observe
     - species
     - time-event
     - state-event
    """

    re_map = {
        'start-model': """\((?P<key>start-model)\s+(?P<quote>['"])(?P<name>\S+)(?P=quote)\s*\)""",
        'param': r'\((?P<key>param)\s+(?P<name>\S+)\s+(?P<value>.*)\)',
        'func': r'\((?P<key>func)\s+(?P<name>\S+)\s+(?P<func>.*)\)',
        'bool': r'\((?P<key>bool)\s+(?P<name>\S+)\s+(?P<expr>.*)\)',
        'observe': r'\((?P<key>observe)\s+(?P<label>\S+)\s+(?P<func>.*)\)',
        'species': r'\((?P<key>species)\s+(?P<name>\w+)\s+(?P<value>\w+)\s*\)',
        'species2': r'\((?P<key>species)\s+(?P<name>\w+)\s*\)',
        'reaction': r'\((?P<key>reaction)\s+(?P<name>\S+)\s+(?P<input>\(.*?\))\s+(?P<output>\(.*?\))\s+(?P<func>.*)\)',
        'time-event': r'\((?P<key>time-event)\s+(?P<name>\S+)\s+(?P<time>\S+)\s+(?P<iteration>\S+)\s+\((?P<pairs>\(.*\))\)',
        'time-event2': r'\((?P<key>time-event)\s+(?P<name>\S+)\s+(?P<time>\S+)\s+\((?P<pairs>\(.*\))\)',
        'state-event': r'\((?P<key>state-event)\s+(?P<name>\S+)\s+(?P<predicate>.*?)\s+\((?P<pairs>.*)\)\)'
    }

    reg_pair = r'(\(.*\))+'

    def parse_model_from_file(model_file, cb):
        """
        parse model and build up cb
        """
        # normalize the paths
        model_file = os.path.abspath(os.path.normpath(model_file))

        # read the model file
        model = open(model_file, 'r').read()

        # clean model file
        model = CMSParser.clean_model(model)

        # parse the model
        CMSParser.parse_model(model, cb)

    def parse_model(model, cb):
        """
        parse model and populate cb properties
        """
        for exp in CMSParser.re_map.values():
            reg = re.compile(exp)

            matches = reg.finditer(model)
            for match in matches:
                term = match.groups()
                # print(term)
                # for g in term:
                #     print(g)
                if term[0] == 'start-model':
                    cb.start_model_name = term[2]
                elif term[0] == 'species':
                    if len(term) == 3:
                        cb.add_species(term[1], term[2])
                    else:
                        cb.add_species(term[1])
                elif term[0] == 'param':
                    cb.add_param(term[1], term[2])
                elif term[0] == 'func':
                    cb.add_func(term[1], term[2])
                elif term[0] == 'bool':
                    cb.add_bool(term[1], term[2])
                elif term[0] == 'observe':
                    cb.add_observe(term[1], term[2])
                elif term[0] == 'reaction':
                    cb.add_reaction(term[1], term[2], term[3], term[4])
                elif term[0] == 'time-event':
                    if len(term) == 5:
                        cb.add_time_event(term[1], term[2], term[3], *CMSParser.parse_pairs(term[4]))
                    else:
                        cb.add_time_event(term[1], term[2], None, *CMSParser.parse_pairs(term[3]))
                elif term[0] == 'state-event':
                    cb.add_state_event(term[1], term[2], *CMSParser.parse_pairs(term[3]))
                else:
                    raise Exception('{} is not supported at moment.'.format([0]))

    def parse_pairs(line):
        """
        parse pair string and return as a list
        """
        reg = re.compile(CMSParser.reg_pair)
        matches = reg.finditer(line)

        pairs = []
        for match in matches:
            pairs.extend(list(match.groups()))

        return pairs

    def clean_model(model):
        """
        remove comments
        """
        return re.sub(r';.*', '', model)
