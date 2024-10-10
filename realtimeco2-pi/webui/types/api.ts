export interface QueryParams {
    type: string
    refreshTime?: number
}

export interface GraphConstraints {
    top: number
    bottom: number
    left: number
    right: number
    width: number
    height: number
    animate?: boolean
    legendShift?: number
}

export interface YearlyData {
    population: number
    co2?: number
    temp?: number
}

export interface ApiResponse {
    [year: string]: YearlyData
}

export interface EnergyData {
    time: string
    year: number
    totalFossilFuelProduction: number
    totalRenewableProduction: number
    hydropowerProduction: number
    windPowerProduction: number
    solarPowerProduction: number
    otherRenewablePowerProduction: number
}

export interface EnergyApiResponse {
    [year: string]: EnergyData
}

export interface SummaryApiResponse {
    temp2030: number
    temp2050: number
    percent2030: number
    percent2050: number
    emissions2030: number
    emissions2050: number
}