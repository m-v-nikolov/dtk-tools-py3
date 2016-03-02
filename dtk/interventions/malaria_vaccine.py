import copy, math

# Pre-erythrocytic simple vaccine
preerythrocytic_vaccine = {
    "class": "SimpleVaccine",
    "Vaccine_Type": "AcquisitionBlocking",
    "Vaccine_Take": 1.0,
    "Reduced_Acquire": 0.9,
    "Durability_Time_Profile": "DECAYDURABILITY",
    "Primary_Decay_Time_Constant": 365*5,
    "Cost_To_Consumer": 15 
}

# Transmission-blocking sexual-stage vaccine
sexual_stage_vaccine = copy.deepcopy(preerythrocytic_vaccine)
sexual_stage_vaccine.update({
    "Vaccine_Type": "TransmissionBlocking",
    "Reduced_Transmit": 0.9
})

# RTS,S simple vaccine
rtss_simple_vaccine = copy.deepcopy(preerythrocytic_vaccine)
rtss_simple_vaccine.update({
    "Reduced_Acquire": 0.8, # 80% initial infection-blocking efficacy
    "Primary_Decay_Time_Constant": 365*1.125/math.log(2), # 13.5 month half-life
    "Cost_To_Consumer": 15 # 3 doses * $5/dose
})