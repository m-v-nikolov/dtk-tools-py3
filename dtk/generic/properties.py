import os
import json
import datetime

from simtools.SetupParser import SetupParser
from simtools.Utilities.LocalOS import LocalOS

def set_property(property, values, initial):
    """
    Set the value of a property.

     .. code-block:: python

        set_property('Accessibility', ['Easy', 'Hard'], [0.5, 0.5])

    :param property: The property to set
    :param values: A list of different values this property can take
    :param initial: The initial distribution
    :return: A dictionary representing the property ready for DTK
    """
    return {'Property': property, 'Values': values, 'Initial_Distribution': initial, 'Transitions': []}


def init_access(**kwargs):
    """
    A shortcut function allowing to set the initial distribution of the Accessibility property.

     .. code-block:: python

        init_access(Easy=0.5, Hard=0.5)

    :param kwargs: A list of key,value pairs representing the property value and initial distribution
    :return: A dictionary representing the property ready for DTK
    """
    return set_property('Accessibility', kwargs.keys(), kwargs.values())


def add_properties_overlay(cb, properties, directory=None, tag=''):
    """
    Creates a property overlay with the given properties.

    :param cb: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` containing the configuration
    :param properties: The list of properties to add
    :param directory: The directory where the demographics file is stored
    :param tag: Properties tag
    :return: Nothing
    """
    if directory is None:
        directory = SetupParser.get('input_root')

    filenames = cb.get_param('Demographics_Filenames')
    demogfiles = [f for f in filenames if 'demographics' in f]

    if len(demogfiles) != 1:
        print(demogfiles)
        raise Exception('add_properties_overlay function is expecting exactly one base demographics file.')

    demog_filename = demogfiles[0]

    if not os.path.exists(os.path.join(directory, demog_filename)):
        raise OSError('No demographics file %s in local input directory %s' % (demog_filename, directory))

    with open(os.path.join(directory, demog_filename)) as f:
        j = json.loads(f.read())

    metadata = j['Metadata']
    metadata.update({'Author': LocalOS.username,
                     'DateCreated': datetime.datetime.now().strftime('%a %b %d %X %Y'),
                     'Tool': os.path.basename(__file__)})

    overlay_content = {'Metadata': metadata,
                       'Defaults': {'IndividualProperties': properties},
                       'Nodes': [{'NodeID': n['NodeID']} for n in j['Nodes']]}

    prefix = demog_filename.split('.')[0]
    immune_init_name = prefix.replace('demographics', 'properties' + tag, 1)
    cb.add_demog_overlay(os.path.basename(immune_init_name), overlay_content)
    cb.enable('Property_Output')
