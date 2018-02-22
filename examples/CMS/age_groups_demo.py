from enum import Enum, EnumMeta
from typing import NamedTuple

import enum

from models.cms.core.CMSConfigBuilder import CMSConfigBuilder
from models.cms.core.CMS_Operator import EMODL


class AgeGroup:
    _group_id = 0

    def __init__(self, **kwargs):
        self.group_id = AgeGroup._group_id
        self.species = kwargs

        AgeGroup._group_id += 1

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            if item in self.species:
                return self.species[item]

        raise AttributeError("{} does not exist in this AgeGroup. Available species: {}"
                             .format(item, ",".join(self.species.keys())))

    def create_species(self, cb):
        for species, value in self.species.items():
            cb.add_species("{}_{}".format(species, self.group_id), value)


class AgeGroupCollection:
    species = None

    def __init__(self):
        self.age_groups = []
        self.available_species = set()
        self.items = []

    def add_age_group(self, age_group):
        self.available_species = self.available_species.union(age_group.species.keys())
        self.age_groups.append(age_group)
        AgeGroupCollection.species = Enum('Species', list(self.available_species))


    def create_item(self, *attributes):
        for a in self.age_groups:
            b = []
            for t in attributes:
                if isinstance(t, AgeGroupCollection.species):
                    b.append("{}_{}".format(t.name, a.group_id))
                else:
                    b.append(str(t))
            print(" ".join(b))


cb = CMSConfigBuilder.from_defaults()
a = AgeGroup(S=1000, I=2000, L=200)
a.create_species(cb)

b = AgeGroupCollection()
b.add_age_group(a)
#(reaction infection-latent   (S) (L) (* lambda (- 1 alpha) S))
b.create_item("reaction","infection-latent",b.species.S,b.species.L, EMODL.MULTIPLY("lambda", EMODL.SUBTRACT(1, "alpha"), b.species.S))
