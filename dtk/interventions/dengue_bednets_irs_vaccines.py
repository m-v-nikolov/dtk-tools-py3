dengue_campaign = {
     "Use_Defaults": 1,
     "Campaign_Name": "Campaign - Bednets, IRS and Vaccines",
     "Events": [
          {
               "Event_Coordinator_Config": {
                    "Intervention_Config": {
                         "Strain_Id_Name": "Strain_1",
                         "class": "OutbreakIndividualDengue"
                    },
                    "Target_Age_Min": 0,
                    "Target_Age_Max": 1.725,
                    "Target_Demographic": "ExplicitAgeRanges",
                    "class": "StandardInterventionDistributionEventCoordinator"
               },
               "Nodeset_Config": {
                    "class": "NodeSetAll"
               },
               "Start_Day": 100,
               "class": "CampaignEvent"
          },
          {
               "Event_Coordinator_Config": {
                    "Intervention_Config": {
                         "Strain_Id_Name": "Strain_2",
                         "class": "OutbreakIndividualDengue"
                    },
                    "Demographic_Coverage": 0,
                    "Target_Demographic": "Everyone",
                    "class": "StandardInterventionDistributionEventCoordinator"
               },
               "Nodeset_Config": {
                    "class": "NodeSetAll"
               },
               "Start_Day": 5000,
               "class": "CampaignEvent"
          },
          {
               "Event_Coordinator_Config": {
                    "Intervention_Config": {
                         "Strain_Id_Name": "Strain_3",
                         "class": "OutbreakIndividualDengue"
                    },
                    "Demographic_Coverage": 0,
                    "Target_Demographic": "Everyone",
                    "class": "StandardInterventionDistributionEventCoordinator"
               },
               "Nodeset_Config": {
                    "class": "NodeSetAll"
               },
               "Start_Day": 5000,
               "class": "CampaignEvent"
          },
          {
               "Event_Coordinator_Config": {
                    "Intervention_Config": {
                         "Strain_Id_Name": "Strain_4",
                         "class": "OutbreakIndividualDengue"
                    },
                    "Demographic_Coverage": 0,
                    "Target_Demographic": "Everyone",
                    "class": "StandardInterventionDistributionEventCoordinator"
               },
               "Nodeset_Config": {
                    "class": "NodeSetAll"
               },
               "Start_Day": 5000,
               "class": "CampaignEvent"
          }
     ]
}
