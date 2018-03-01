import collections
import copy
from enum import Enum

from models.cms.core.CMS_Operator import EMODL


class Group:
    def __init__(self, species, parameters, name):
        self.species = species
        self.parameters = parameters
        self.name = name

class GroupManager:
    def __init__(self, groups):
        self.groups = []
        self.available_species = set()
        self.available_parameters = set()
        self.species= None
        self.parameters = None

        for g in groups:
            self.add_group(g)

    def create_species(self):
        for g in self.groups:
            for species, value in g.species.items():
                print("{}_{} = {}".format(species,g.name, value))

    def add_group(self,group):
        self.available_species = self.available_species.union(group.species.keys())
        self.available_parameters = self.available_parameters.union(group.parameters.keys())
        self.groups.append(group)
        self.species = Enum('Species', list(self.available_species))
        self.parameters = Enum('Parameters', list(self.available_parameters))

    def create_item(self, *attributes):
        for group in self.groups:
            g = []
            for attr in attributes:
                a = copy.deepcopy(attr)
                g.append(self.transform_emodl(a, group.name))

            print(g)

    def transform_emodl(self, element, group_name):
        if type(element) in EMODL.all_options():
            for attr, value in element.__dict__.items():
                if not isinstance(value, str) and isinstance(value, collections.Iterable):
                    setattr(element, attr, list(map(lambda e: self.transform_emodl(e, group_name), value)))
                else:
                    setattr(element, attr, self.transform_emodl(value, group_name))
            return element

        if isinstance(element, self.species) or isinstance(element, self.parameters):
            return "{}_{}".format(element.name, group_name)

        return element


g = Group(
    species={"S":1000, "I":200, "R":300},
    parameters={"alpha":10, "beta":20},
    name="0_5"
)

g1 = Group(
    species={"S":200, "I":10, "R":5},
    parameters={"alpha":3, "beta":4},
    name="5_10"
)


a = GroupManager(
    groups=(g, g1)
)

a.create_species()
a.create_item("reaction","infection-latent",a.species.S,a.species.R, EMODL.MULTIPLY("lambda", EMODL.SUBTRACT(a.parameters.alpha, "3"), a.species.S))
