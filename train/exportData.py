from time import sleep
from playwright.sync_api import sync_playwright
from worldometerApi import Api

ROWS = 500  # Number of rows to write to the file

with sync_playwright() as p:
    api = Api(p)
    with open("data.csv", "w") as file:
        oldPopulation = 0
        oldCo2Emissions = 0

        for _ in range(ROWS + 1):
            data = api.get_data()
            population = data["absolute_growth_year"]['last_value']
            co2Emissions = data["co2_emissions"]["last_value"]

            # Write the data to the file
            file.write(f"{population},{co2Emissions}\n")
            print(f"{population},{co2Emissions}")

            sleep(5)
