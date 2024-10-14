from datetime import date, datetime

import numpy
from fastapi import FastAPI
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split

import pandas as pd
import pickle
import time, os

DATA_FOLDER = os.getenv('DATA_FOLDER', 'data')
MODELS_FOLDER = os.getenv('MODELS_FOLDER', 'models')

poly = PolynomialFeatures(degree=2, include_bias=False)
app = FastAPI()


@app.get("/energyProductionBy/{year}")
async def energy_production_by_year(year: int, fossilEnergyTWh: float, renewableEnergyTWh: float,
                                    populationGrowth: int):
    totalFossilModel = pickle.load(open(f'{MODELS_FOLDER}/population_increase_vs_total_fossil_energy.pkl', 'rb'))
    totalRenewableModel = pickle.load(open(f'{MODELS_FOLDER}/population_increase_vs_total_renewable_energy.pkl', 'rb'))
    windModel = pickle.load(open(f'{MODELS_FOLDER}/population_increase_vs_wind.pkl', 'rb'))
    hydroModel = pickle.load(open(f'{MODELS_FOLDER}/population_increase_vs_hydropower.pkl', 'rb'))
    solarModel = pickle.load(open(f'{MODELS_FOLDER}/population_increase_vs_solar.pkl', 'rb'))
    otherModel = pickle.load(open(f'{MODELS_FOLDER}/population_increase_vs_other_renewables.pkl', 'rb'))

    populationGrowthPredicted = (await population_by_year(year))["populationGrowthPredicted"]

    totalFossilEnergyPredicted = int(totalFossilModel.predict([[populationGrowthPredicted]])[0])
    totalRenewableEnergyPredicted = int(totalRenewableModel.predict([[populationGrowthPredicted]])[0])
    windEnergyPredicted = int(windModel.predict([[populationGrowthPredicted]])[0])
    hydroEnergyPredicted = int(hydroModel.predict([[populationGrowthPredicted]])[0])
    solarEnergyPredicted = int(solarModel.predict([[populationGrowthPredicted]])[0])
    otherRenewablesEnergyPredicted = int(otherModel.predict([[populationGrowthPredicted]])[0])

    totalEnergyDataset = pd.read_csv(f'{DATA_FOLDER}/population_increase_vs_total_energy.csv')
    totalEnergyDataset = pd.concat(
        [totalEnergyDataset, pd.DataFrame([[populationGrowth, fossilEnergyTWh, renewableEnergyTWh]],
                                          columns=totalEnergyDataset.columns)], ignore_index=True)

    # update model - total energy
    populationIncreaseAxis = totalEnergyDataset[["Population Increase"]].values
    totalFossilEnergyAxis = totalEnergyDataset["Total Fossil Fuel (TWh, direct energy)"].values
    totalRenewableEnergyAxis = totalEnergyDataset["Total Renewable (TWh, direct energy)"].values

    populationIncreaseAxisTrain1, populationIncreaseAxisTest1, totalFossilEnergyAxisTrain, totalFossilEnergyAxisTest = train_test_split(
        populationIncreaseAxis, totalFossilEnergyAxis,
        test_size=0.15,
        random_state=0)
    populationIncreaseAxisTrain2, populationIncreaseAxisTest2, totalRenewableEnergyAxisTrain, totalRenewableEnergyAxisTest = train_test_split(
        populationIncreaseAxis, totalRenewableEnergyAxis,
        test_size=0.15,
        random_state=0)

    totalFossilModel.fit(populationIncreaseAxisTrain1, totalFossilEnergyAxisTrain)
    totalRenewableModel.fit(populationIncreaseAxisTrain2, totalRenewableEnergyAxisTrain)

    totalFossilEnergyAccuracy = totalFossilModel.score(populationIncreaseAxisTest1, totalFossilEnergyAxisTest)
    totalRenewableEnergyAccuracy = totalRenewableModel.score(populationIncreaseAxisTest2, totalRenewableEnergyAxisTest)

    # save model
    pickle.dump(totalFossilModel, open(f'{MODELS_FOLDER}/population_increase_vs_total_fossil_energy.pkl', 'wb'))
    pickle.dump(totalRenewableModel, open(f'{MODELS_FOLDER}/population_increase_vs_total_renewable_energy.pkl', 'wb'))

    totalEnergyDataset.to_csv(f'{DATA_FOLDER}/population_increase_vs_total_energy.csv', index=False)

    return {
        "year": year,
        "fossilEnergyTWh": fossilEnergyTWh,
        "renewableEnergyTWh": renewableEnergyTWh,
        "populationGrowth": populationGrowth,
        "totalFossilEnergyPredicted": totalFossilEnergyPredicted,
        "totalRenewableEnergyPredicted": totalRenewableEnergyPredicted,
        "windEnergyPredicted": windEnergyPredicted,
        "hydroEnergyPredicted": hydroEnergyPredicted,
        "solarEnergyPredicted": solarEnergyPredicted,
        "otherRenewablesEnergyPredicted": otherRenewablesEnergyPredicted,
        "totalFossilEnergyAccuracy": totalFossilEnergyAccuracy,
        "totalRenewableEnergyAccuracy": totalRenewableEnergyAccuracy
    }


@app.get("/annualTempAnomaly/{emissionsAnnual}")
async def annual_temp_anomaly(emissionsAnnual: int):
    model = pickle.load(open(f'{MODELS_FOLDER}/annualtemp-annualco2.pkl', 'rb'))

    annualTempAnomalyPredicted = model.predict([[emissionsAnnual]])[0]

    return {
        "emissionsAnnual": emissionsAnnual,
        "annualTempAnomalyPredicted": annualTempAnomalyPredicted
    }


@app.get("/totalCo2EmissionsBy/{year}")
async def total_co2_emissions_by_year(year: int, nowTotalCo2Emissions: float = 0):
    model = pickle.load(open(f'{MODELS_FOLDER}/population_vs_total_co2.pkl', 'rb'))

    populationBy = (await population_by_year(year))["populationPredicted"]
    populationBy = numpy.array(populationBy).reshape(-1, 1)

    totalCo2EmissionsPredicted = int(model.predict(poly.fit_transform(populationBy))[0])

    return {
        "year": year,
        "totalCo2EmissionsPredicted": totalCo2EmissionsPredicted,
        "totalCo2EmissionsGrowthPercent": (
                                                  totalCo2EmissionsPredicted / nowTotalCo2Emissions) * 100 if nowTotalCo2Emissions != 0 else 0
    }


@app.get("/populationBy/{year}")
async def population_by_year(year: int, nowPopulation: int = 0):
    populationModel = pickle.load(open(f'{MODELS_FOLDER}/population.pkl', 'rb'))
    growthModel = pickle.load(open(f'{MODELS_FOLDER}/population-increase.pkl', 'rb'))

    nowTimeStamp = int(datetime.now().timestamp())
    yearTimeStamp = int(datetime(year, 12, 31).timestamp())
    previousYearTimeStamp = int(datetime(year - 1, 12, 31).timestamp())
    yearTimeStampArray = numpy.array([yearTimeStamp]).reshape(-1, 1)
    previousYearTimeStampArray = numpy.array([previousYearTimeStamp]).reshape(-1, 1)
    currentTimeStampArray = numpy.array([yearTimeStamp - previousYearTimeStamp]).reshape(-1, 1)
    fromNowTimeStampArray = numpy.array([yearTimeStamp - nowTimeStamp]).reshape(-1, 1)

    if nowPopulation == 0:
        nowPopulation = int(
            populationModel.predict(poly.fit_transform(numpy.array([nowTimeStamp]).reshape(-1, 1)))[0])

    populationPredicted = int(populationModel.predict(poly.fit_transform(yearTimeStampArray))[0])
    previousPopulationPredicted = int(populationModel.predict(poly.fit_transform(previousYearTimeStampArray))[0])
    populationGrowthPredicted = int(growthModel.predict(poly.fit_transform(currentTimeStampArray))[0])
    populationGrowthPredictedFromNow = int(growthModel.predict(poly.fit_transform(fromNowTimeStampArray))[0])

    return {
        "year": year,
        "populationPredicted": populationPredicted,
        "populationGrowthPredicted": populationGrowthPredicted,
        "populationGrowthCalculated": populationPredicted - previousPopulationPredicted,
        "populationGrowthPredictedFromNow": populationGrowthPredictedFromNow,
        "populationGrowthCalculatedFromNow": populationPredicted - nowPopulation,
        "populationGrowthPercent": (populationGrowthPredictedFromNow / nowPopulation) * 100,
        "calculatedPopulationGrowthPercent": ((populationPredicted - nowPopulation) / nowPopulation) * 100
    }


@app.post("/population")
async def population(population: int, populationGrowthThisYear: int):
    populationModel = pickle.load(open(f'{MODELS_FOLDER}/population.pkl', 'rb'))
    growthModel = pickle.load(open(f'{MODELS_FOLDER}/population-increase.pkl', 'rb'))

    nowTimeStamp = int(datetime.now().timestamp())
    previousYearTimeStamp = int(datetime(date.today().year - 1, 12, 31).timestamp())
    nowTimeStampArray = numpy.array([nowTimeStamp]).reshape(-1, 1)
    endOfYearTimeStamp = int(datetime(date.today().year, 12, 31).timestamp())
    yearEndTimeStampArray = numpy.array([endOfYearTimeStamp]).reshape(-1, 1)
    endOfYearTimeStampArray = numpy.array([endOfYearTimeStamp - previousYearTimeStamp]).reshape(-1, 1)
    currentTimeStampArray = numpy.array([nowTimeStamp - previousYearTimeStamp]).reshape(-1, 1)

    nowPopulationPredicted = int(
        populationModel.predict(poly.fit_transform(nowTimeStampArray))[0])
    nowPopulationGrowthPredicted = int(
        growthModel.predict(poly.fit_transform(currentTimeStampArray))[0])
    endOfYearPopulationPredicted = int(
        populationModel.predict(poly.fit_transform(yearEndTimeStampArray))[0])
    endOfYearPopulationGrowthPredicted = int(
        growthModel.predict(poly.fit_transform(endOfYearTimeStampArray))[0])

    # write new data to csv
    populationData = pd.read_csv(f'{DATA_FOLDER}/population.csv')
    growthData = pd.read_csv(f'{DATA_FOLDER}/population-increase.csv')
    populationData = pd.concat(
        [populationData, pd.DataFrame([[nowTimeStamp, population]], columns=populationData.columns)], ignore_index=True)
    growthData = pd.concat(
        [growthData,
         pd.DataFrame([[nowTimeStamp - previousYearTimeStamp, populationGrowthThisYear]], columns=growthData.columns)],
        ignore_index=True)

    # update model - population
    timeAxis = populationData.iloc[:, :-1].values
    populationAxis = populationData.iloc[:, 1].values

    timeAxis = poly.fit_transform(timeAxis.reshape(-1, 1))

    timeAxisTrain, timeAxisTest, populationAxisTrain, populationAxisTest = train_test_split(timeAxis, populationAxis,
                                                                                            test_size=0.15,
                                                                                            random_state=0)
    populationModel.fit(timeAxisTrain, populationAxisTrain)
    populationAccuracy = populationModel.score(timeAxisTest, populationAxisTest)

    # save model
    pickle.dump(populationModel, open(f'{MODELS_FOLDER}/population.pkl', 'wb'))
    populationData.to_csv(f'{DATA_FOLDER}/population.csv', index=False)

    # update model - growth
    timeAxis = growthData.iloc[:, :-1].values
    growthAxis = growthData.iloc[:, 1].values

    timeAxis = poly.fit_transform(timeAxis.reshape(-1, 1))

    timeAxisTrain, timeAxisTest, growthAxisTrain, growthAxisTest = train_test_split(timeAxis, growthAxis,
                                                                                    test_size=0.15,
                                                                                    random_state=0)

    growthModel.fit(timeAxisTrain, growthAxisTrain)
    growthAccuracy = growthModel.score(timeAxisTest, growthAxisTest)

    # save model
    pickle.dump(growthModel, open(f'{MODELS_FOLDER}/population-increase.pkl', 'wb'))
    growthData.to_csv(f'{DATA_FOLDER}/population-increase.csv', index=False)

    return {
        "population": population,
        "populationGrowthThisYear": populationGrowthThisYear,
        "populationPredicted": nowPopulationPredicted,
        "populationGrowthThisYearPredicted": nowPopulationGrowthPredicted,
        "endOfYearPopulationPredicted": endOfYearPopulationPredicted,
        "endOfYearPopulationGrowthPredicted": endOfYearPopulationGrowthPredicted,
        "populationAccuracy": populationAccuracy,
        "growthAccuracy": growthAccuracy
    }


@app.get("/annualEmissionsByYear")
async def annualEmissionsByYear(yearPopulationGrowth: int):
    model = pickle.load(open(f'{MODELS_FOLDER}/population_increase_vs_annual_co2.pkl', 'rb'))

    emissionsPredicted = int(model.predict([[yearPopulationGrowth]])[0])

    return {
        "yearPopulationGrowth": yearPopulationGrowth,
        "emissionsPredicted": emissionsPredicted
    }


@app.post("/annualEmissions")
async def annualEmissions(currentPopulationGrowth: int, endOfYearPopulationGrowth: int, currentCo2Emissions: float):
    model = pickle.load(open(f'{MODELS_FOLDER}/population_increase_vs_annual_co2.pkl', 'rb'))

    currentEmissionsPredicted = int(model.predict([[currentPopulationGrowth]])[0])
    endOfYearEmissionsPredicted = int(model.predict([[endOfYearPopulationGrowth]])[0])

    # write new data to csv
    populationIncrease_annualco2_data = pd.read_csv(f'{DATA_FOLDER}/population_increase_vs_annual_co2.csv')

    populationIncrease_annualco2_data = pd.concat(
        [populationIncrease_annualco2_data, pd.DataFrame([[currentPopulationGrowth, currentCo2Emissions]],
                                                         columns=populationIncrease_annualco2_data.columns)],
        ignore_index=True)

    # update model
    populationIncreaseAxis = populationIncrease_annualco2_data.iloc[:, :-1].values
    annualEmissionsAxis = populationIncrease_annualco2_data.iloc[:, 1].values

    populationIncreaseAxisTrain, timeAxisTest, annualEmissionsTrain, annualEmissionsTest = train_test_split(
        populationIncreaseAxis, annualEmissionsAxis,
        test_size=0.15,
        random_state=0)
    model.fit(populationIncreaseAxisTrain, annualEmissionsTrain)
    accuracy = model.score(timeAxisTest, annualEmissionsTest)

    # save model
    pickle.dump(model, open(f'{MODELS_FOLDER}/population_increase_vs_annual_co2.pkl', 'wb'))
    populationIncrease_annualco2_data.to_csv(f'{DATA_FOLDER}/population_increase_vs_annual_co2.csv', index=False)

    return {
        "currentPopulationGrowth": currentPopulationGrowth,
        "currentEmissions": currentCo2Emissions,
        "endOfYearPopulationGrowth": endOfYearPopulationGrowth,
        "currentEmissionsPredicted": currentEmissionsPredicted,
        "endOfYearEmissionsPredicted": endOfYearEmissionsPredicted,
        "accuracy": accuracy
    }


@app.post("/totalEmissions")
async def totalEmissions(currentPopulation: int, endOfYearPopulation: int):
    model = pickle.load(open(f'{MODELS_FOLDER}/population_vs_total_co2.pkl', 'rb'))

    currentPopulationGrowthArray = numpy.array([currentPopulation]).reshape(-1, 1)
    endOfYearPopulationGrowthArray = numpy.array([endOfYearPopulation]).reshape(-1, 1)

    currentTotalEmissionsPredicted = int(model.predict(poly.fit_transform(currentPopulationGrowthArray))[0])
    endOfYearTotalEmissionsPredicted = int(model.predict(poly.fit_transform(endOfYearPopulationGrowthArray))[0])

    # write new data to csv
    population_totalco2_data = pd.read_csv(f'{DATA_FOLDER}/population_vs_total_co2.csv')

    # update model
    populationAxis = population_totalco2_data.iloc[:, :-1].values
    totalEmissionsAxis = population_totalco2_data.iloc[:, 1].values

    populationAxis = poly.fit_transform(populationAxis.reshape(-1, 1))

    populationAxisTrain, populationAxisTest, totalEmissionsAxisTrain, totalEmissionsAxisTest = train_test_split(
        populationAxis, totalEmissionsAxis,
        test_size=0.3,
        random_state=0)
    model.fit(populationAxisTrain, totalEmissionsAxisTrain)
    accuracy = model.score(populationAxisTest, totalEmissionsAxisTest)

    # save model
    pickle.dump(model, open(f'{MODELS_FOLDER}/population_vs_total_co2.pkl', 'wb'))
    population_totalco2_data.to_csv(f'{DATA_FOLDER}/population_vs_total_co2.csv', index=False)

    return {
        "currentPopulation": currentPopulation,
        "endOfYearPopulation": endOfYearPopulation,
        "totalCo2EmissionsPredicted": currentTotalEmissionsPredicted,
        "endOfYearTotalCo2EmissionsPredicted": endOfYearTotalEmissionsPredicted,
        "accuracy": accuracy
    }
