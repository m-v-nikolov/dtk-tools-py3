import random

def scale_larval_habitats(cb, scales, target="ALL_HABITATS", variation=0, start_day=0):
    """
    Reduce available larval habitat in a node-specific way.

    :param cb: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` object
    :param scales: Dictionary associating a nodeID with the larval habitat scale
    :param target: the target habitat affected by the reduction
    :param variation: Faction of the overall scale used when randomizing the scale
    :return: Nothing
    """

    if variation > 1 or variation < 0:
        raise Exception("Variation is a fraction of the overall scale and cannot be set to less than zero or more than 1.")

    rando = 1
    for (nodeIDs, scale) in scales:

        if variation > 0 :
            rando = random.uniform(1-variation,1+variation)
        # A permanent node-specific scaling of larval habitat by habitat type
        habitat_reduction_event = { "class" : "CampaignEvent",
                                    "Start_Day": start_day,
                                    "Event_Coordinator_Config": {
                                        "class": "NodeEventCoordinator",
                                        "Intervention_Config": {
                                            "Habitat_Scale": float(scale)*rando,
                                            "Habitat_Target": target, 
                                            "class": "ScaleLarvalHabitat"
                                         }
                                        },
                                    "Nodeset_Config": {
                                        "class": "NodeSetNodeList", 
                                        "Node_List": [int(x) for x in nodeIDs]
                                        }
                                    }

        cb.add_event(habitat_reduction_event)
