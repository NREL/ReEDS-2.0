import os
import pandas as pd

DEFAULT_CATEGORY_FILES = {
    'TechCost_file': 'tech_costs_2021update.csv',
    'FuelLimit_file': 'fuel_limit.csv',
    'MinLoad_file': 'minloadfrac0.csv',
    'RECapMandate_file': 'recap_mandate_2030.csv',
    'RECapManTech_file': 'capmandate_tech_set.csv',
    'RECapFracMandate_file': 'recapfrac_mandate_2030.csv',
    'REGenMandate_file': 'regen_mandate_2030.csv',
    'REGenManTech_file': 'genmandate_tech_set.csv',
    "PRM_file": 'prm_region.csv'
}

FILE_KEYS =[
    'HourlyLoadFile', 
    'FuelLimit_file', # included
    'FuelPrice_file', 
    'TechCost_file', # included
    'MinLoad_file',  # included
    'Hours_file',  # included
    'Load_file', # included
    'PeakDemRegion_file', # included
    'IVT_file', 
    'RECapMandate_file', # included
    'RECapManTech_file', # included
    'RECapFracMandate_file', # included
    'REGenMandate_file', # included
    'REGenManTech_file', # included
    'PRM_file', # included
    'yearset'
]

DEFAULT_FILE_NAMES = {
    "TechCost_file": {
        "Low Solar Cost": "tech_costs_low_UPV_2022.csv",
        "Low Wind Cost": "tech_costs_low_wind_2022.csv",
        "Low Battery Cost": "tech_costs_low_battery_2022.csv"
    },
    "FuelLimit_file": {
        "New Gas": "fuel_limit_NewGas.csv"
    }
}

DEFAULT_FILE_TO_CATEGORY = {
    "TechCost_file": {
        "tech_costs_low_UPV_2022.csv": "Low Solar Cost",
        "tech_costs_low_wind_2022.csv":"Low Wind Cost",
        "tech_costs_low_battery_2022.csv": "Low Battery Cost" 
    },
    "FuelLimit_file": {
        "fuel_limit_NewGas.csv": "New Gas"
    }
}



FILE_LOCATION = {
    'HourlyLoadFile': 'demand', 
    'FuelLimit_file': 'fuels', # included
    'FuelPrice_file': 'fuels', 
    'TechCost_file' : 'generators', # included
    'MinLoad_file': 'reserves',  # included
    'Hours_file' : 'demand',  # included
    'Load_file': 'demand', # included
    'PeakDemRegion_file': 'demand', # included
    'IVT_file': 'generators', 
    'RECapMandate_file': 'generators', 
    'RECapManTech_file': 'sets',
    'RECapFracMandate_file': 'generators',
    'REGenMandate_file': 'generators',
    'REGenManTech_file': 'sets',
    'PRM_file': 'reserves',
    'yearset': 'sets'
}

CASE_ROWS = [
    'timetype', 
    'solver', 
    'augur_workers', 
    'yearset',  # included
    'endyear',  # included
    'HourlyLoadFile', 
    'PRM_file', # included
    'FuelLimit_file', # included
    'FuelPrice_file', 
    'TechCost_file', # included
    'MinLoad_file',  # included
    'Hours_file',  # included
    'Load_file', # included
    'PeakDemRegion_file', # included
    'IVT_file', 
    'RECapMandate_file', # included 
    'RECapManTech_file', # included 
    'RECapFracMandate_file', # included
    'REGenMandate_file', # included
    'REGenManTech_file', # included
    'numclass', 
    'numhintage', 
    'carbonpolicystartyear',  # included
    'retireyear',  # included
    'Rediversity',  # included
    'CC/Curtailment Iterations', # included
    'GSw_MinCF', 
    'GSw_MinCFCon', 
    'GSw_GrowthRel', # included
    'GSw_GrowthAbs', # included 
    'GSw_OpRes', # included
    'GSw_OpResTrade', # included
    'GSw_Refurb', # included
    'GSw_PRM',  # included
    'GSw_PRMTrade', # included
    'GSw_Storage', # included
    'GSw_CurtStorage',  # included
    'GSw_StorCC', 
    'GSw_StorOpres', 
    'GSw_CurtFlow', 
    'GSw_Int_CC', 
    'GSw_Int_Curt', 
    'GSw_FuelSupply', # included 
    'GSw_Prescribed', # included
    'GSw_RECapMandate', # included
    'GSw_RECapFracMandate', # included
    'GSw_REGenMandate', # included
    'GSw_TechPhaseOut', # included
    'GSw_Retire', # included
    'GSw_REdiversity', # included
    'GSw_MinGen', # included
    'GSw_CarbonTax', # included
    'GSw_CO2Limit', # included
    'GSw_SAsia_Trade', 
    'GSw_SAsia_PRM', 
    'GSw_ValStr',  # included
    'GSw_CCcurtAvg', 
    'GSw_Loadpoint',  # included
    'GSw_gopt',  # included
    'GSw_SolarPlusStorage', 
    'GSw_StorHAV'
]

SCEN_DESCRIPTION = {
    "Reference": "Standard assumptions about technology costs, policies, and regulations for the power sector through 2050",
    "toy": "Toy model based on a subset of model years with no relative growth constraint",
    "LowerPeak": "Growth in peak electricity demand is slower than forecast",
    "LowBatCost": "Installed costs for BESS start lower and decline faster compared to the Reference scenario",
    "PSH50": "Installed cost for PSH are 50% lower than in the Reference scenario",
    "NoStorCC": "Energy storage is not valued or compensated for its contribution to resource adequacy",
    "NoStorHAV": "Energy storage is not valued or compensated for shifting energy supply to different times of day",
    "NoNewFossil": "No new investments in fossil-fueled capacity above what is currently planned",
    "NoSouthAsia": "No electricity trade with Nepal, Bhutan, and Bangladesh",
    "NoStorOpres":	"Energy storage does not provide operating reserves",
    "NoNewGas":	"No new investments in gas-fired capacity above what is currently planned",
    "HighBatCost":	"Installed costs for BESS start higher and decline slower compared to the Reference scenario",
    "LCS-LCB":	"Combined LowSolarCost and LowBatCost scenario",
    "NNG-LCB":	"Combined NoNewGas and LowBatCost scenario",
    "NoBattery": "No new investments in BESS",
    "PSH10": "Installed cost for PSH are 10% lower than in the Reference scenario",
    "PSH20": "Installed cost for PSH are 20% lower than in the Reference scenario",
    "PSH30": "Installed cost for PSH are 30% lower than in the Reference scenario",
    "PSH40": "Installed cost for PSH are 40% lower than in the Reference scenario"
}

def get_file_location(file_type, category):
    
    file_name = None
    if category not in ['Default', 'Custom Upload']:
        file_name = DEFAULT_FILE_NAMES[file_type][category]
    
    if category == 'Default':
        file_name = DEFAULT_CATEGORY_FILES[file_type]

    return file_name

def get_technologies():

    tech_file = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs',  'inputs', 'sets', 'gen_tech_set.csv')
    df = pd.read_csv(tech_file, names=['tech'])
    technologies = df['tech'].tolist()

    return technologies

TECHNOLOGIES = get_technologies()
TECHNOLOGIES = TECHNOLOGIES + ['NEPAL_STORAGE']
CSV_SCHEMA = {
    'TechCost_file': {
        'allt': {'type': 'integer', 'min': 2017, 'max': 2050},
        'i': {'type': 'string', 'allowed': TECHNOLOGIES },
        'cost_cap': {'type': 'float', 'min': 0, 'max': 100000000000000},
        'cost_fom': {'type': 'float', 'min': 0, 'max': 100000000000000},
        'cost_vom': {'type': 'float', 'min': 0, 'max': 100000000000000},
        'heat_rate': {'type': 'float', 'min': 0, 'max': 100000000000000}
    },
    "FuelLimit_file": {
        "first": {'type': 'string'},
        "second": {'type': 'integer', 'min': 2017, 'max': 2050},
        "third": {'type': 'float', 'min': 0, 'max': 100000000000000}
    },
    "MinLoad_file": {
        "first": {'type': 'string', 'allowed': TECHNOLOGIES},
        "second": {'type': 'float', 'min': 0.0, 'max': 1.0}
    },
    "RECapMandate_file": {
        "first": {'type': 'integer', 'min': 2017, 'max': 2050},
        "second": {'type': 'float', 'min':0, 'max': 100000000000000}
    },
    "RECapFracMandate_file": {
        "first": {'type': 'integer', 'min': 2017, 'max': 2050},
        "second": {'type': 'float', 'min':0, 'max': 1.0}
    },
    "RECapManTech_file": {
        "first": {'type': 'string', 'allowed': TECHNOLOGIES}
    },
    "REGenMandate_file": {
        "first": {'type': 'integer', 'min': 2017, 'max': 2050},
        "second": {'type': 'float', 'min':0, 'max': 1.0}
    },
    "REGenManTech_file": {
        "first": {'type': 'string', 'allowed': TECHNOLOGIES}
    },
    "PRM_file": {
        "first": {'type': 'string'},
        "second": {'type': 'integer', 'min': 2017, 'max': 2050},
        "third": {'type': 'float', 'min':0, 'max': 1.0}
    }

}

CSV_FILE_HEADERS = {
    'FuelLimit_file': ['first', 'second', 'third'],
    'MinLoad_file': ['first', 'second'],
    'RECapMandate_file': ['first', 'second'],
    'RECapFracMandate_file': ['first', 'second'],
    'RECapManTech_file': ['first'],
    'REGenMandate_file': ['first', 'second'],
    'REGenManTech_file': ['first'],
    'PRM_file': ['first','second','third']
}