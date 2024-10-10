import time

import os
import requests
from playwright.sync_api import sync_playwright

from worldometerApi import Api

DATA_URL = os.getenv("DATA_URL", "http://127.0.0.1:8001")

with sync_playwright() as p:
    api = Api(p)

    while True:
        data = api.get_data()
        population = data["current_population"]["last_value"]
        populationGrowth = data["absolute_growth_year"]["last_value"]
        populationGrowthToday = data["absolute_growth"]["last_value"]
        currentCo2Emissions = data["co2_emissions"]["last_value"]
        fossilEnergyMWh = data["energy_nonren"]["last_value"]
        renewableEnergyMWh = data["energy_ren"]["last_value"]

        print("Population:", population, "Population Growth:", populationGrowth, "Current Co2 Emissions:",
              currentCo2Emissions)

        url = (
            f"{DATA_URL}/?population={population}&populationGrowthThisYear={populationGrowth}"
            f"&populationGrowthToday={populationGrowthToday}&currentCo2Emissions={currentCo2Emissions}"
            f"&fossilEnergyMWh={fossilEnergyMWh}&renewableEnergyMWh={renewableEnergyMWh}")
        requests.post(url)

        time.sleep(5)
