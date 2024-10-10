<template>
  <div>
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    <div class="container">
      <p class="title">{{ displayName ? displayName : contentKey }}</p>
      <h2 class="number">{{ formatNumberWithCommas(data[0]) }}</h2>
      <h5 class="change">{{(((data[0] - data[1]) / (data[1])) * 100) > 0 ? "+": ""}}{{ (((data[0] - data[1]) / (data[1])) * 100).toPrecision(3)}}%</h5>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, onUnmounted} from 'vue'
import {useFetch} from '#app'
import * as d3 from 'd3'
import type {GraphConstraints, QueryParams} from "~/types/api";

const data = ref<number[]>([0, 0])
const error = ref<string | null>(null)

const props = defineProps<{
  params: QueryParams
  constraints: GraphConstraints
  contentKey: string,
  displayName?: string
}>()

// Function to format population numbers with commas
const formatNumberWithCommas = (number: number): string => {
  return d3.format(',')(number)
}

// Function to format population numbers in billions with two decimal places
const formatNumberInBillions = (number: number): string => {
  return `${(number / 1e9).toFixed(2)}B`
}

// Function to fetch data
const fetchData = async (): Promise<void> => {
  try {

    const {data: fetchData, error: fetchError} = await useFetch("/api/realtime", {
      query: {type: "co2"}
    })

    if (fetchData.value) {
      // Process and sort data
      data.value[0] = fetchData.value[0][props.contentKey]
      data.value[1] = fetchData.value[1][props.contentKey]

      error.value = null // Clear previous errors
    } else {
      error.value = fetchError || 'Failed to fetch data.'
      console.error(error.value)
    }
  } catch (err) {
    error.value = 'An unexpected error occurred.'
    console.error('Fetch error:', err)
  }
}

onMounted(() => {
  fetchData()

  // Set interval to fetch data every 5 minutes (300,000 ms)
  const interval = setInterval(() => {
    fetchData()
  }, props.params.refreshTime || 300000)

  // Clear interval on component unmount
  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<style scoped>
.container {
  width: 100%;
  margin-right: 50px;
}

.title {
  margin: 0;
  text-align: center;
}

.number {
  margin: 0;
  text-align: center;
}

.change {
  margin: 0;
  text-align: center;
  color: darkgreen;
}

.error-message {
  color: red;
  margin-bottom: 1em;
  text-align: center;
}

.tooltip {
  position: absolute;
  text-align: left;
  width: auto;
  height: auto;
  padding: 8px;
  font: 12px sans-serif;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #ccc;
  border-radius: 4px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
  box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.3);
}
</style>

