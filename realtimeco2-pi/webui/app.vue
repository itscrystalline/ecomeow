<template>
  <div class="light">
    <NuxtRouteAnnouncer/>
    <div class="horizontal">
      <img src="/logo.webp" alt="Logo" width="75"/>
      <h2>Machine Learning Prediction Dashboard</h2>
      <img src="/logo_kosen_1_a2c03efafa.png" style="padding-left: 10px"/>
    </div>
    <div class="horizontal">
      <div class="realtime">
        <h2 class="title realtimeh1">Realtime Data <small>by Worldometer</small></h2>
        <div class="horizontal">
          <InfoBox :params="populationParams" :constraints="populationConstraints"
                   content-key="populationGrowthThisYear"
                   display-name="Population Growth"/>
          <InfoBox :params="co2Params" :constraints="populationConstraints" content-key="currentCo2Emissions"
                   display-name="CO₂ Emissions (Tons)"/>
        </div>
      </div>
      <div class="warning">
        <h2 class="title warningh1">IPCC Goals</h2>
        <IPCCGoals/>
      </div>
    </div>
    <h2 class="title predictionh1">Predictions For 2030 & 2050</h2>
    <div class="horizontal fitscreen prediction">
      <div>
        <HybridChart title="Global CO₂ Emissions In Relation to Global Population" :constraints="populationConstraints"
                     content="co2" text="CO₂ Emissions (Tons)" color="rgba(54, 162, 235, 0.5)"/>
        <HybridChart title="Global Warming In Relation to Global Population" :constraints="populationConstraints"
                     content="temp" text="Global Warming (°C)" color="rgba(146, 211, 120, 0.5)"/>
      </div>

      <div>
        <p class="nomargin text-center">Global Energy Consumption</p>
        <div class="horizontal">
          <PieChart year="2030"/>
          <PieChart year="2050"/>
        </div>
        <StackedBarChart :constraints="powerGraphConstraints"/>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type {GraphConstraints, QueryParams} from "~/types/api";

const populationParams: QueryParams = {
  rows: 2,
  refreshTime: 5000
}
const co2Params: QueryParams = {
  table: 'annualCo2Emissions',
  rows: 2,
  refreshTime: 5000
}

const populationConstraints: GraphConstraints = {
  top: 60,
  right: 70,
  bottom: 60,
  left: 60,
  width: 680,
  height: 300,
}

const powerGraphConstraints: GraphConstraints = {
  top: 60,
  right: 30,
  bottom: 60,
  left: 60,
  width: 680,
  height: 300,
  legendShift: 35,
}
</script>

<style lang="css">
.light {
  color: black;
  background-color: white;
}

body {
  border: none;
  margin: 0;
  width: 100%;
  height: 100%;
  padding: 20px;
}

.dark {
  color: white;
  background-color: #1E1E2E;
}

#dashboard {
  display: flex;
  justify-content: start;
  align-items: start;
}

.horizontal {
  display: flex;
  justify-content: center;
  align-items: center;
}

.fitscreen {
  width: 97%;
  height: 100%;
}

.title {
  margin: 0;
  margin-bottom: 10px;
}

.nomargin {
  margin: 0;
}

.text-center {
  text-align: center;
}

.warning {
  border: crimson 5px solid;
  background: rgba(220, 20, 60, 0.1);
  padding: 10px;
  min-height: 160px;
  margin-left: 30px;
}

.warningh1 {
  color: crimson;
}

.prediction {
  border: steelblue 5px solid;
  background: rgba(70, 130, 180, 0.1);

}

.predictionh1 {
  color: steelblue;
}

.realtime {
  border: darkorange 5px solid;
  background: rgba(255, 140, 0, 0.1);
  padding: 10px;
  min-height: 150px;
  width: 30%;
}

.realtimeh1 {
  color: darkorange;
}

img {
  margin-right: 10px;
}
</style>