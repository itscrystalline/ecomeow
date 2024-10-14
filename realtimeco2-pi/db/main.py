from datetime import datetime

from prisma import Prisma
from fastapi import FastAPI
import aiohttp, os

AI_URL = os.getenv("AI_URL", "http://127.0.0.1:8000")

app = FastAPI()

URL_POPULATION = f"{AI_URL}/population?population=POPULATION&populationGrowthThisYear=POP_GROWTH_THIS_YEAR"
URL_ANNUAL_EMISSIONS = (f"{AI_URL}/annualEmissions?currentPopulationGrowth=POP_GROWTH_CURRENT&"
                        "endOfYearPopulationGrowth=POP_GROWTH_END_YEAR&currentCo2Emissions=CURR_CO2_EMISSIONS")
URL_TOTAL_EMISSIONS = f"{AI_URL}/totalEmissions?currentPopulation=POPULATION&endOfYearPopulation=END_POP"
URL_PREDICT_POPULATION = f"{AI_URL}/populationBy/YEAR?nowPopulation=POPULATION"
URL_PREDICT_TOTAL_EMISSIONS = f"{AI_URL}/totalCo2EmissionsBy/YEAR?nowTotalCo2Emissions=NOW_CO2_EMISSIONS"
URL_PREDICT_ANNUAL_EMISSIONS = f"{AI_URL}/annualEmissionsByYear?yearPopulationGrowth=POP_GROWTH"
URL_PREDICT_TEMP_ANOMALY = f"{AI_URL}/annualTempAnomaly/ANNUAL_EMISSIONS"
URL_ENERGY_PRODUCTION = (f"{AI_URL}/energyProductionBy/YEAR?fossilEnergyTWh=FOSSIL_ENERGY&renewableEnergyTWh"
                         f"=RENEWABLE_ENERGY&populationGrowth=POP_GROWTH_TODAY")

YEARS = ["2030", "2050"]


@app.post("/")
async def main(population: int, populationGrowthThisYear: int, populationGrowthToday: int, currentCo2Emissions: float,
               fossilEnergyMWh: float, renewableEnergyMWh: float):
    fossilEnergyTWh = fossilEnergyMWh / 1000000
    renewableEnergyTWh = renewableEnergyMWh / 1000000

    db = Prisma()
    await db.connect()

    accuracy = [0, 0, 0, 0, 0, 0]
    async with aiohttp.ClientSession() as session:
        url = URL_POPULATION.replace("POPULATION", str(population)).replace("POP_GROWTH_THIS_YEAR",
                                                                            str(populationGrowthThisYear))
        async with session.post(url) as response:
            prediction_population = await response.json()

            await db.population.create(
                {
                    "population": population,
                    "populationGrowthThisYear": populationGrowthThisYear,
                    "populationPredicted": prediction_population["populationPredicted"],
                    "populationGrowthThisYearPredicted": prediction_population["populationGrowthThisYearPredicted"],
                    "endOfYearPopulationPredicted": prediction_population["endOfYearPopulationPredicted"],
                    "endOfYearPopulationGrowthPredicted": prediction_population["endOfYearPopulationGrowthPredicted"],
                }
            )
            accuracy[0] = prediction_population["populationAccuracy"]
            accuracy[1] = prediction_population["growthAccuracy"]

        url = URL_ANNUAL_EMISSIONS.replace("POP_GROWTH_CURRENT", str(populationGrowthThisYear)).replace(
            "POP_GROWTH_END_YEAR", str(prediction_population["endOfYearPopulationGrowthPredicted"])).replace(
            "CURR_CO2_EMISSIONS", str(currentCo2Emissions)
        )
        async with session.post(url) as response:
            prediction_annualemissions = await response.json()

            await db.annualco2emissions.create(
                {
                    "Population": {
                        "connect": {"populationGrowthThisYear": populationGrowthThisYear}
                    },
                    "currentCo2Emissions": prediction_annualemissions["currentEmissions"],
                    "currentCo2EmissionsPredicted": prediction_annualemissions["currentEmissionsPredicted"],
                    "annualCo2EmissionsPredicted": prediction_annualemissions["endOfYearEmissionsPredicted"]
                }
            )
            accuracy[2] = prediction_annualemissions["accuracy"]

        url = URL_TOTAL_EMISSIONS.replace("POPULATION", str(population)).replace("END_POP",
                                                                                 str(prediction_population[
                                                                                         "endOfYearPopulationPredicted"]))
        async with session.post(url) as response:
            prediction_totalemissions = await response.json()

            await db.totalco2emissions.create(
                {
                    "Population": {
                        "connect": {"population": population}
                    },
                    "totalCo2EmissionsPredicted": prediction_totalemissions["totalCo2EmissionsPredicted"],
                    "endOfYearTotalCo2EmissionsPredicted": prediction_totalemissions[
                        "endOfYearTotalCo2EmissionsPredicted"]
                }
            )
            accuracy[3] = prediction_totalemissions["accuracy"]

        for year in YEARS:
            url = URL_ENERGY_PRODUCTION.replace("YEAR", year).replace("FOSSIL_ENERGY", str(fossilEnergyTWh)).replace(
                "RENEWABLE_ENERGY", str(renewableEnergyTWh)).replace("POP_GROWTH_TODAY",
                                                                     str(populationGrowthToday))
            async with session.get(url) as response:
                prediction_energy = await response.json()

                await db.energyproductionby.create(
                    {
                        "year": int(year),
                        "totalFossilFuelProduction": prediction_energy["totalFossilEnergyPredicted"],
                        "totalRenewableProduction": prediction_energy["totalRenewableEnergyPredicted"],
                        "hydropowerProduction": prediction_energy["hydroEnergyPredicted"],
                        "windPowerProduction": prediction_energy["windEnergyPredicted"],
                        "solarPowerProduction": prediction_energy["solarEnergyPredicted"],
                        "otherRenewablePowerProduction": prediction_energy["otherRenewablesEnergyPredicted"],
                    }
                )

                accuracy[4] = prediction_energy["totalFossilEnergyAccuracy"]
                accuracy[5] = prediction_energy["totalRenewableEnergyAccuracy"]

            url = URL_PREDICT_POPULATION.replace("YEAR", year).replace("POPULATION", str(population))
            async with session.get(url) as response:
                prediction_population = await response.json()

                await db.populationby.create(
                    {
                        "year": int(year),
                        "populationPredicted": prediction_population["populationPredicted"],
                        "populationGrowthPredicted": prediction_population["populationGrowthPredicted"],
                        "populationGrowthCalculated": prediction_population["populationGrowthCalculated"],
                        "populationGrowthPredictedFromNow": prediction_population["populationGrowthPredictedFromNow"],
                        "populationGrowthCalculatedFromNow": prediction_population["populationGrowthCalculatedFromNow"],
                        "populationGrowthPercent": prediction_population["populationGrowthPercent"],
                        "calculatedPopulationGrowthPercent": prediction_population["calculatedPopulationGrowthPercent"]
                    }
                )

            url = URL_PREDICT_TOTAL_EMISSIONS.replace("YEAR", str(year)).replace("NOW_CO2_EMISSIONS", str(
                prediction_totalemissions["totalCo2EmissionsPredicted"]))

            async with session.get(url) as response:
                prediction_totalemission_future = await response.json()

            url_annual_emissions = URL_PREDICT_ANNUAL_EMISSIONS.replace("YEAR", str(year)).replace("POP_GROWTH",
                                                                                                   str(
                                                                                                       prediction_population[
                                                                                                           "populationGrowthCalculated"]))

            async with session.get(url_annual_emissions) as response:
                prediction_annualemission_future = await response.json()

            url_temp_anomaly = URL_PREDICT_TEMP_ANOMALY.replace("ANNUAL_EMISSIONS", str(
                prediction_annualemission_future["emissionsPredicted"]))

            async with session.get(url_temp_anomaly) as response:
                prediction_temp_anomaly = await response.json()

            await db.co2emissionsby.create(
                {
                    "year": int(year),
                    "totalCo2EmissionsPredicted": prediction_totalemission_future["totalCo2EmissionsPredicted"],
                    "annualCo2EmissionsPredicted": prediction_annualemission_future["emissionsPredicted"],
                    "tempAnomalyPredicted": prediction_temp_anomaly["annualTempAnomalyPredicted"]
                }
            )

        await db.predictorstats.create(
            {
                "populationPrecision": accuracy[0],
                "populationGrowthPrecision": accuracy[1],
                "annualCo2EmissionsPrecision": accuracy[2],
                "totalCo2EmissionsPrecision": accuracy[3],
                "totalFossilEnergyAccuracy": accuracy[4],
                "totalRenewableEnergyAccuracy": accuracy[5]
            }
        )

    await db.disconnect()
    return {"status": "ok"}
