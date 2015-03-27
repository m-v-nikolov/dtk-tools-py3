import random

# Reduce available larval habitat in node-specific way
def scale_larval_habitats(cb, scales, target="ALL_HABITATS", variation=0):

    if variation > 1 or variation < 0:
        raise Exception("Variation is a fraction of the overall scale and cannot be set to less than zero or more than 1.")

    for (nodeIDs, scale) in scales:

        # A permanent node-specific scaling of larval habitat by habitat type
        habitat_reduction_event = { "class" : "CampaignEvent",
                                    "Start_Day": 0,
                                    "Event_Coordinator_Config": {
                                        "class": "NodeEventCoordinator",
                                        "Intervention_Config": {
                                            "Habitat_Scale": scale*random.uniform(1-variation,1+variation),
                                            "Habitat_Target": target, 
                                            "class": "ScaleLarvalHabitat"
                                         }
                                        },
                                    "Nodeset_Config": {
                                        "class": "NodeSetNodeList", 
                                        "Node_List": nodeIDs
                                        }
                                    }

        cb.add_event(habitat_reduction_event)
