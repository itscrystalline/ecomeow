import { PrismaClient } from '@prisma/client'
import {QueryParams} from "~/types/api";

export default defineEventHandler(async (event) => {
    const req = getRouterParam(event, 'req')
    const query: QueryParams = getQuery(event)

    const prisma = new PrismaClient()

    const format = (data: any) => {
        data.forEach((row: any) => {
            for (const key in row) {
                if (typeof row[key] === 'bigint') {
                    row[key] = Number(row[key]);
                }
            }
        });
        return data;
    }

    const formatOne = (data: any) => {
        for (const key in data) {
            if (typeof data[key] === 'bigint') {
                data[key] = Number(data[key]);
            }
        }
        return data;
    }

    if (req === "realtime") {
        if (query.type === "popGrowth") {
            return format(await prisma.population.findMany({
                orderBy: {
                    time: "desc"
                },
                take: 2
            }))
        } else if (query.type === "co2") {
            return format(await prisma.annualCo2Emissions.findMany({
                orderBy: {
                    time: "desc"
                },
                take: 2
            }))
        }
    } else if (req === "predicted") {
        const population2030 = await prisma.populationBy.findFirst({
            where: {
                year: 2030
            },
            orderBy: {
                time: "desc"
            }
        })
        const population2050 = await prisma.populationBy.findFirst({
            where: {
                year: 2050
            },
            orderBy: {
                time: "desc"
            }
        })

        const co22030 = await prisma.co2EmissionsBy.findFirst({
            where: {
                year: 2030
            },
            orderBy: {
                time: "desc"
            }
        })
        const co22050 = await prisma.co2EmissionsBy.findFirst({
            where: {
                year: 2050
            },
            orderBy: {
                time: "desc"
            }
        })
        if (query.type === "temp") {
            return {
                2030: {
                    population: Number(population2030?.populationGrowthCalculated),
                    temp: Number(co22030?.tempAnomalyPredicted)
                },
                2050: {
                    population: Number(population2050?.populationGrowthCalculated),
                    temp: Number(co22050?.tempAnomalyPredicted)
                }
            }
        } else if (query.type === "co2") {
            return {
                2030: {
                    population: Number(population2030?.populationPredicted),
                    co2: Number(co22030?.totalCo2EmissionsPredicted)
                },
                2050: {
                    population: Number(population2050?.populationPredicted),
                    co2: Number(co22050?.totalCo2EmissionsPredicted)
                }
            }
        } else if (query.type === "energy") {
            const energy2030 = await prisma.energyProductionBy.findFirst({
                where: {
                    year: 2030
                },
                orderBy: {
                    time: "desc"
                }
            })
            const energy2050 = await prisma.energyProductionBy.findFirst({
                where: {
                    year: 2050
                },
                orderBy: {
                    time: "desc"
                }
            })

            return {
                2030: formatOne(energy2030),
                2050: formatOne(energy2050)
            }
        }
    } else if (req === "summary") {
        const co22030 = await prisma.co2EmissionsBy.findFirst({
            where: {
                year: 2030
            },
            orderBy: {
                time: "desc"
            }
        })
        const co22050 = await prisma.co2EmissionsBy.findFirst({
            where: {
                year: 2050
            },
            orderBy: {
                time: "desc"
            }
        })
        const emissions2010 = 1342308036222


        return {
            temp2030: Number(co22030?.tempAnomalyPredicted),
            temp2050: Number(co22050?.tempAnomalyPredicted),
            percent2030: (Number(co22030?.totalCo2EmissionsPredicted) / emissions2010 * 100) - 100,
            percent2050: (Number(co22050?.totalCo2EmissionsPredicted) / emissions2010 * 100) - 100,
            emissions2030: Number(co22030?.totalCo2EmissionsPredicted),
            emissions2050: Number(co22050?.totalCo2EmissionsPredicted),
        }
    }

    return null
})