import copy

# ------- Default block for an AntimalarialDrug --------
malaria_drug_param_block = {

    # Drug PkPd
    "Drug_Cmax": 1000, 
    "Drug_Decay_T1": 1, 
    "Drug_Decay_T2": 1, 
    "Drug_Vd": 10, 
    "Drug_PKPD_C50": 100, 

    # Treatment regimen
    "Drug_Fulltreatment_Doses": 3, 
    "Drug_Dose_Interval": 1, 

    # These are daily parasite killing rates for:
    "Drug_Gametocyte02_Killrate": 0,   # ... gametocyte - early stages
    "Drug_Gametocyte34_Killrate": 0,   # ...            - late stages
    "Drug_GametocyteM_Killrate":  0,   # ...            - mature
    "Drug_Hepatocyte_Killrate":   0,   # ... hepatocytes
    "Max_Drug_IRBC_Kill":         0    # ... asexual parasites

}

# ------- Modifications for specific drug types --------
AL_param_block = copy.deepcopy(malaria_drug_param_block)
AL_mod_params = {
    "Drug_Gametocyte02_Killrate": 2.30,
    "Drug_Gametocyte34_Killrate": 2.30,
    "Drug_GametocyteM_Killrate":  2.30,
    "Max_Drug_IRBC_Kill":         4.61
}
AL_param_block.update(AL_mod_params)

AM_param_block = copy.deepcopy(AL_param_block)

CQ_param_block = copy.deepcopy(malaria_drug_param_block)
CQ_mod_params = {
    "Drug_Decay_T1": 4,
    "Drug_Decay_T2": 15, 
    "Drug_Vd": 3,
    "Max_Drug_IRBC_Kill": 3.45
}
CQ_param_block.update(CQ_mod_params)

PE_param_block = copy.deepcopy(malaria_drug_param_block)
PE_param_block["Drug_Hepatocyte_Killrate"] = 2

TB_param_block = copy.deepcopy(malaria_drug_param_block)
TB_mod_params = {
    "Drug_Gametocyte02_Killrate": 2.3,
    "Drug_Gametocyte34_Killrate": 2.3,
    "Drug_GametocyteM_Killrate":  2.3
}
TB_param_block.update(TB_mod_params)

PQ_param_block = copy.deepcopy(TB_param_block)
PQ_param_block["Drug_Hepatocyte_Killrate"] = 1
PQ_param_block["Max_Drug_IRBC_Kill"] = 3.45

QN_param_block = copy.deepcopy(malaria_drug_param_block)
QN_mod_params = {
    "Drug_Decay_T1": 7,
    "Drug_Decay_T2": 7, 
    "Max_Drug_IRBC_Kill": 2.3
}
QN_param_block.update(QN_mod_params)

SP_param_block = copy.deepcopy(malaria_drug_param_block)
SP_param_block["Max_Drug_IRBC_Kill"] = 2.3

TQ_param_block = copy.deepcopy(PQ_param_block)

# ------- Default parameter table for all supported drug types --------
malaria_drug_params = {
    "Artemether_Lumefantrine": AL_param_block,
    "Artemisinin": AM_param_block,
    "Chloroquine": CQ_param_block,
    "GenPreerythrocytic": PE_param_block,
    "GenTransBlocking": TB_param_block,
    "Primaquine": PQ_param_block,
    "Quinine": QN_param_block,
    "SP": SP_param_block,
    "Tafenoquine": TQ_param_block
}