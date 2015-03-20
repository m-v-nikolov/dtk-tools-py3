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
    "Reduced_Acquire": 0.556,  # phase III (5-17 mo.) efficacy against clinical disease in first year
    "Primary_Decay_Time_Constant": 365*3.0/math.log(2), # half-life-yr to mean-life-time-days
    "Cost_To_Consumer": 15 # 3 doses * $5/dose
})