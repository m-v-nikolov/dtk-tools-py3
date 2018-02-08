from models.cms.core.CMS_Object import *


class CMS_ConfigBuilder(object):
    def __init__(self, start_model_name):
        self.start_model_name = start_model_name
        self.species = {}
        self.param = {}
        self.func = {}
        self.bool = {}
        self.observe = []
        self.reaction = []
        self.time_event = []
        self.state_event = []

    @staticmethod
    def clean_value(value):
        if isinstance(value, float):
            return "{:.10f}".format(value).rstrip('0')

        return value

    @staticmethod
    def clean_in_out(value):
        return "({})".format(str(value).strip(')( '))

    def add_species(self, name, value=None):
        self.species[name] = Species(name, value)

    def set_species(self, name, value=None):
        self.species[name] = Species(name, value)

    def get_species(self, name):
        return self.species[name].value

    def add_time_event(self, name, *pair_list):
        self.time_event.append(TimeEvent(name, *pair_list))

    def add_state_event(self, name, *pair_list):
        self.state_event.append(StateEvent(name, *pair_list))

    def add_reaction(self, name, input, output, func):
        input = self.clean_in_out(input)
        output = self.clean_in_out(output)
        self.reaction.append(Reaction(name, input, output, func))

    def add_param(self, name, value):
        value = self.clean_value(value)
        self.param[name] = Param(name, value)

    def set_param(self, name, value):
        value = self.clean_value(value)
        self.param[name] = Param(name, value)

    def get_param(self, name):
        return self.param[name].value

    def add_func(self, name, func):
        self.func[name] = Func(name, func)

    def set_func(self, name, func):
        self.func[name] = Func(name, func)

    def get_func(self, name):
        return self.func[name].value

    def add_observe(self, label, func):
        self.observe.append(Observe(label, func))

    def add_bool(self, name, expr):
        self.bool[name] = Bool(name, expr)

    def set_bool(self, name, expr):
        self.bool[name] = Bool(name, expr)

    def get_bool(self, name, expr):
        return self.bool[name].value

    def to_model(self):
        out_list = []

        def add_to_display(objs):
            if objs:
                out_list.append('\n')
                if isinstance(objs, dict):
                    out_list.extend(objs.values())
                elif isinstance(objs, list):
                    out_list.extend(objs)

        out_list.append('(import (rnrs) (emodl cmslib))')
        out_list.append('(start-model "{}")'.format(self.start_model_name))

        add_to_display(self.species)

        add_to_display(self.param)

        add_to_display(self.func)

        add_to_display(self.bool)

        add_to_display(self.observe)

        add_to_display(self.reaction)

        add_to_display(self.state_event)

        add_to_display(self.time_event)

        out_list.append('\n')
        out_list.append('(end-model)')

        out_list = [str(i) if i != '\n' else i for i in out_list]
        return '\n'.join(out_list)

    def save_to_file(self, filename):
        f = open('{}.emodl'.format(filename), 'w')
        f.write(self.to_model())
        f.close()
