from models.cms.core.CMS_Object import *


class CMS_ConfigBuilder(object):
    def __init__(self, start_model_name):
        # self.start_model = StartModel(start_model_name)       # [TODO]: delete if no need StartModel class
        self.start_model_name = start_model_name
        self.species = []
        self.time_event = []
        self.state_event = []
        self.reaction = []
        self.param = []
        self.func = []
        self.bool = []
        self.observe = []

    def add_species(self, name, value=None):
        self.species.append(Species(name, value))

    def add_time_event(self, name, *pair_list):
        self.time_event.append(TimeEvent(name, *pair_list))

    def add_state_event(self, name, *pair_list):
        self.state_event.append(StateEvent(name, *pair_list))

    def add_reaction(self, name, input, output, func):
        self.reaction.append(Reaction(name, input, output, func))

    def add_param(self, name, value):
        self.param.append(Param(name, value))

    def add_func(self, name, func):
        self.func.append(Func(name, func))

    def add_observe(self, label, func):
        self.observe.append(Observe(label, func))

    def add_bool(self, name, expr):
        self.bool.append(Bool(name, expr))

    def to_model(self):
        out_list = []

        def add_to_display(obj_list):
            if obj_list:
                out_list.append('\n')
            for o in obj_list:
                out_list.append(o)

        out_list.append('(import (rnrs) (emodl cmslib))')
        # out_list.append(self.start_model)     # [TODO]: may not need to define StartModle class
        out_list.append('(start-model "{}")'.format(self.start_model_name))

        add_to_display(self.species)

        add_to_display(self.param)

        add_to_display(self.func)

        add_to_display(self.observe)

        add_to_display(self.state_event)

        add_to_display(self.time_event)

        add_to_display(self.reaction)

        out_list.append('\n')
        out_list.append('(end-model)')

        # print(out_list)
        out_list = [str(i) if i != '\n' else i for i in out_list]
        # print('\n'.join(out_list))

        return '\n'.join(out_list)
