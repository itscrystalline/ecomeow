import pickle

totalFossilModel = pickle.load(open(f'population_increase_vs_total_fossil_energy.pkl', 'rb'))
totalRenewableModel = pickle.load(open(f'population_increase_vs_total_renewable_energy.pkl', 'rb'))
windModel = pickle.load(open(f'population_increase_vs_wind.pkl', 'rb'))
hydroModel = pickle.load(open(f'population_increase_vs_hydropower.pkl', 'rb'))
solarModel = pickle.load(open(f'population_increase_vs_solar.pkl', 'rb'))
otherModel = pickle.load(open(f'population_increase_vs_other_renewables.pkl', 'rb'))