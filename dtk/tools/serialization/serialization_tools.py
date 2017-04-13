from __future__ import print_function
import dtkFileToolsToo as dtk

STATE_ADULT = 1         # implies female, I believe
STATE_INFECTED = 2
STATE_INFECTIOUS = 3

_endings = [ 'th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th' ]

# functions need comments and/or cleaning.


def zero_infections(source_filename, dest_filename, ignore_nodes=[], keep_individuals=[]):

    print('Ignoring nodes {0}'.format(ignore_nodes))
    print('Keeping infections in humans {0}'.format(keep_individuals))

    print("Reading file: '{0}'".format(source_filename))
    source = dtk.DtkFile(source_filename)

    for index in range(0, len(source.nodes)):
        print('Reading {0}{1} node'.format(index, _endings[index%10]), end='\n')
        obj = source.nodes[index]
        node = obj.node
        print(', externalId = {0}'.format(node.externalId))
        if node.externalId not in ignore_nodes:
            print('Zeroing vector infections')
            zero_vector_infections(node.m_vectorpopulations)
            print('Zeroing human infections')
            zero_human_infections(node.individualHumans, keep_individuals)
            print('Saving updated node')
            source.nodes[index] = obj
        else:
            print('Ignoring node {0}'.format(index))

    print("Writing file: '{0}'".format(dest_filename))
    source.write(dest_filename)

    return


def zero_vector_infections(vectors, remove=False):

    for vector_population in vectors:
        class_name = vector_population['__class__']
        if class_name == 'VectorPopulation' or class_name == 'VectorPopulationAging':
            if not remove:
                vector_population.AdultQueues.extend(vector_population.InfectedQueues)
                vector_population.AdultQueues.extend(vector_population.InfectiousQueues)
            vector_population.InfectedQueues = []
            vector_population.InfectiousQueues = []
        elif class_name == 'VectorPopulationIndividual':
            if not remove:
                for cohort in vector_population.AdultQueues:
                    assert(cohort['__class__'] == 'VectorCohortIndividual')
                    state = cohort.state
                    if state == STATE_INFECTED or state == STATE_INFECTIOUS:
                        cohort.state = STATE_ADULT
            else:
                adults = vector_population.AdultQueues
                vector_population.AdultQueues = [cohort for cohort in adults if cohort.state != STATE_INFECTED and cohort.state != STATE_INFECTIOUS]
        else:
            raise RuntimeError("Encountered unknown vector population class - '{0}'".format(class_name))

    return


def zero_human_infections(humans, keep_ids=[]):
    for person in humans:
        if person.suid.id not in keep_ids:
            person.infections = []
            person.infectiousness = 0
            person.m_is_infected = False
            person.m_female_gametocytes = 0
            person.m_female_gametocytes_by_strain = []
            person.m_male_gametocytes = 0
            person.m_male_gametocytes_by_strain = []
            person.m_gametocytes_detected = 0
            person.m_new_infection_state = 0
            person.m_parasites_detected_by_blood_smear = 0
            person.m_parasites_detected_by_new_diagnostic = 0

    return


def remove_vectors_by_nodeid(source_filename, dest_filename, removal_nodes):

    print("Reading file: '{0}'".format(source_filename))
    source = dtk.DtkFile(source_filename)

    for index in range(0, len(source.nodes)):
        print('Reading {0}{1} node'.format(index, _endings[index%10]), end='\n')
        obj = source.nodes[index]
        node = obj.node
        if node.externalId in removal_nodes:
            node.m_vectorpopulations = []
            source.nodes[index] = obj
        else:
            print('Ignoring node {0}'.format(index))

    print("Writing file: '{0}'".format(dest_filename))
    source.write(dest_filename)

    return


def remove_humans_by_nodeid(source_filename, dest_filename, removal_nodes):

    print("Reading file: '{0}'".format(source_filename))
    source = dtk.DtkFile(source_filename)

    for index in range(0, len(source.nodes)):
        print('Reading {0}{1} node'.format(index, _endings[index%10]), end='\n')
        obj = source.nodes[index]
        node = obj.node
        if node.externalId in removal_nodes:
            for person in node.individualHumans:
                if person.home_node_id.id == node.suid.id:
                    node.individualHumans.remove(person)
            source.nodes[index] = obj
        else:
            print('Ignoring node {0}'.format(index))

    print("Writing file: '{0}'".format(dest_filename))
    source.write(dest_filename)

    return


def remove_unused_campaign_events(cb, ser_date, last_date=100000) :

    gone_list = []
    for event in cb.campaign['Events'] :
        if "Start_Day" in event :
            if event["Start_Day"] < ser_date or event["Start_Day"] > last_date :
                gone_list.append(event)
    for event in gone_list :
        cb.campaign['Events'].remove(event)
