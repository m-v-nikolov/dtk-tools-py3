# IRS parameters
irs_housingmod = { "class": "IRSHousingModification",
                   "Blocking_Rate": 0.0,  # i.e. repellency
                   "Killing_Rate": 0.7, 
                   "Durability_Time_Profile": "DECAYDURABILITY", 
                   "Primary_Decay_Time_Constant":   365,  # killing
                   "Secondary_Decay_Time_Constant": 365,  # blocking
                   "Cost_To_Consumer": 8.0
}