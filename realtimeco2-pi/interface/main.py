from datetime import datetime

import prisma.engine.errors
from fastapi import FastAPI
from prisma import Prisma

app = FastAPI()


@app.get("/")
# date from 1 day ago to now by default
async def main(table: str, sort: str = "desc", rows: int = -1,
               from_date: datetime = datetime.fromtimestamp(-1),
               to_date: datetime = datetime.now()):
    db = Prisma()
    try:
        await db.connect()

        if table == "annualCo2Emissions":
            dbTable = db.annualco2emissions
        elif table == "totalCo2Emissions":
            dbTable = db.totalco2emissions
        elif table == "population":
            dbTable = db.population
        elif table == "populationBy":
            dbTable = db.populationby
        elif table == "co2EmissionsBy":
            dbTable = db.co2emissionsby
        elif table == "energyProductionBy":
            dbTable = db.energyproductionby
        else:
            toReturn = "Invalid table"

        if rows != -1:
            print("taking", rows)
            toReturn = await dbTable.find_many(
                order={"time": sort},
                take=rows
            )
        elif from_date != datetime.fromtimestamp(-1):
            print("taking from", from_date, "to", to_date)
            toReturn = await dbTable.find_many(
                where={"time": {"gte": from_date, "lte": to_date}},
                order={"time": sort}
            )
        else:
            print("taking 50")
            toReturn = await dbTable.find_many(
                order={"time": sort},
                take=50
            )
    except prisma.engine.errors.EngineConnectionError:
        toReturn = "Connection error"

    finally:
        await db.disconnect()

    return toReturn
