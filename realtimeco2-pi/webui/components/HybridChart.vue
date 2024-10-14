<!-- components/HybridChart.vue -->
<template>
  <div class="chart-container" ref="chartContainer">
    <!-- Tooltip for interactivity -->
    <div
        v-if="tooltip.visible"
        :style="tooltip.style"
        class="tooltip"
    >
      <strong>{{ tooltip.data.year }}</strong><br/>
      Population: {{ formatNumberWithCommas(tooltip.data.population) }}<br/>
      CO₂ Emissions: {{ formatNumberWithIons(tooltip.data.content) }}
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, onUnmounted} from 'vue'
import * as d3 from 'd3'
import type {ApiResponse, GraphConstraints} from "~/types/api";

// References
const chartContainer = ref<HTMLElement | null>(null)

// Tooltip state
interface TooltipData {
  year: string
  population: number
  content: number
}

const props = defineProps<{
  title: string
  color: string
  constraints: GraphConstraints
  content: string
  text?: string
}>()

const tooltip = ref<{
  visible: boolean
  data: TooltipData
  style: { [key: string]: string }
}>({
  visible: false,
  data: {year: '', population: 0, content: 0},
  style: {},
})

// Formatting functions
const formatNumberWithCommas = (num: number): string => {
  return num % 1 == 0 ? num.toLocaleString() : num.toFixed(2).toLocaleString()
}

const formatNumberWithIons = (num: number): string => {
  return d3.format('.2s')(num).replace("G", "B") // e.g., 2.01T for trillion
}

// Fetch data from API
const fetchData = async (): Promise<ApiResponse | null> => {
  try {
    const response = await fetch(`/api/predicted?type=${props.content}`) // Adjust the endpoint as needed
    if (!response.ok) {
      console.error('Network response was not ok')
      return null
    }
    const data: ApiResponse = await response.json()
    return data
  } catch (error) {
    console.error('Fetch error:', error)
    return null
  }
}

// Render the hybrid chart
const renderChart = (data: ApiResponse) => {
  if (!chartContainer.value) return

  // Clear any existing SVG
  d3.select(chartContainer.value).selectAll('*').remove()

  // Convert data into an array
  const dataset = Object.keys(data).map(year => ({
    year,
    population: data[year].population,
    content: props.content === "co2" ? data[year].co2 : data[year].temp,
  }))

  // Set dimensions and margins
  const margin = {
    top: props.constraints.top,
    right: props.constraints.right,
    bottom: props.constraints.bottom,
    left: props.constraints.left
  }
  const width = props.constraints.width - margin.left - margin.right
  const height = props.constraints.height - margin.top - margin.bottom

  // Create SVG
  const svg = d3
      .select(chartContainer.value)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .attr(
          'viewBox',
          `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`
      )
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

  // X Scale
  const xScale = d3
      .scaleBand<string>()
      .domain(dataset.map(d => d.year))
      .range([0, width])
      .padding(0.6)
      .align(0.3)

  // Y Scale for CO2 (Left)
  const yScaleLeft = d3
      .scaleLinear()
      .domain([0, d3.max(dataset, d => d.content)! * 1.1])
      .range([height, 0])

  // Y Scale for Population (Right)
  const yScaleRight = d3
      .scaleLinear()
      .domain([0, d3.max(dataset, d => d.population)! * 2])
      .range([height, 0])

  // Area generator for CO2
  const area = d3
      .area<{ year: string; population: number; content: number }>()
      .x(d => (xScale(d.year)! + xScale.bandwidth() / 2))
      .y0(height)
      .y1(d => yScaleLeft(d.content))
      .curve(d3.curveMonotoneX)

  // Bars for Population
  svg
      .selectAll('.bar')
      .data(dataset)
      .enter()
      .append('rect')
      .attr('x', d => xScale(d.year)!)
      .attr('y', d => yScaleRight(d.population))
      .attr('width', xScale.bandwidth())
      .attr('height', d => height - yScaleRight(d.population))
      .attr('fill', 'rgba(255, 99, 132, 0.7)') // Semi-transparent red
      .on('mouseover', (event, d) => {
        tooltip.value = {
          visible: true,
          data: {year: d.year, population: d.population, content: d.content},
          style: {
            left: `${event.pageX + 10}px`,
            top: `${event.pageY - 28}px`,
          },
        }
      })
      .on('mouseout', () => {
        tooltip.value.visible = false
      })

  // Append area path
  svg
      .append('path')
      .datum(dataset)
      .attr('fill', props.color) // Light blue with transparency
      .attr('d', area)

  // append points
  svg
      .selectAll('circle')
      .data(dataset)
      .enter()
      .append('circle')
      .attr('cx', d => (xScale(d.year)! + xScale.bandwidth() / 2))
      .attr('cy', d => yScaleLeft(d.content))
      .attr('r', 10)
      .attr('fill', 'rgba(255,211,99,0.3)')
      .attr('stroke', '#125AB8')
      .attr('stroke-width', '2px')

  svg
      .selectAll('.text')
      .data(dataset)
      .enter()
      .append('text')
      .attr('x', d => (xScale(d.year)! + xScale.bandwidth() / 2))
      .attr('y', d => yScaleLeft(d.content) - 15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .text(d => d.content > 1000000 ? formatNumberWithIons(d.content) : formatNumberWithCommas(d.content))
      .on('mouseover', (event, d) => {
        event.target.textContent = formatNumberWithCommas(d.content)
      })
      .on('mouseout', (event, d) => {
        event.target.textContent = formatNumberWithIons(d.content)
      })


  svg
      .selectAll('.text')
      .data(dataset)
      .enter()
      .append('text')
      .attr('x', d => (xScale(d.year)! + xScale.bandwidth() / 2))
      .attr('y', height - 10)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .text(d => formatNumberWithIons(d.population))
      .on('mouseover', (event, d) => {
        event.target.textContent = formatNumberWithCommas(d.population)
      })
      .on('mouseout', (event, d) => {
        event.target.textContent = formatNumberWithIons(d.population)
      })

  // X Axis
  svg
      .append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(d3.axisBottom(xScale))

  // Y Axis Left for CO2
  svg
      .append('g')
      .call(d3.axisLeft(yScaleLeft).ticks(5).tickFormat(d => formatNumberWithIons(d)))

  // Y Axis Right for Population
  svg
      .append('g')
      .attr('transform', `translate(${width},0)`)
      .call(d3.axisRight(yScaleRight).ticks(5).tickFormat(d => formatNumberWithIons(d)))

  // Labels
  // X Axis Label
  svg
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('x', width / 2)
      .attr('y', -20)
      .text(props.title)

  svg
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('x', width / 2)
      .attr('y', height + margin.bottom - 10)
      .text('Year')

  // Y Axis Left Label (CO2)
  svg
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -margin.left + 20)
      .text(props.text ? props.text : props.content)

  // Y Axis Right Label (Population)
  svg
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', width + margin.right - 20)
      .text(props.content == "temp" ? 'Population Growth' : 'Population')

  // Optional: Add a legend
  const legend = svg.append('g').attr('transform', `translate(${width - 150}, 0)`)

  // CO2 Emissions Legend
  legend
      .append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', 15)
      .attr('height', 15)
      .attr('fill', props.color)

  legend
      .append('text')
      .attr('x', 20)
      .attr('y', 12)
      .text(props.text ? props.text : props.content)
      .attr('font-size', '12px')
      .attr('alignment-baseline', 'middle')

  // Population Legend
  legend
      .append('rect')
      .attr('x', 0)
      .attr('y', 25)
      .attr('width', 15)
      .attr('height', 15)
      .attr('fill', 'rgba(255, 99, 132, 0.7)')

  legend
      .append('text')
      .attr('x', 20)
      .attr('y', 37)
      .text(props.content == "temp" ? 'Population Growth' : 'Population')
      .attr('font-size', '12px')
      .attr('alignment-baseline', 'middle')
}

// Lifecycle hooks
let intervalId: number

onMounted(async () => {
  const apiData = await fetchData()
  if (apiData) {
    renderChart(apiData)
  }

  // Set up periodic data fetching every 5 minutes (300,000 ms)
  intervalId = window.setInterval(async () => {
    const newData = await fetchData()
    if (newData) {
      renderChart(newData)
    }
  }, 300000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  max-width: 900px;
}

.tooltip {
  position: absolute;
  background-color: white;
  border: 1px solid #ccc;
  padding: 8px;
  border-radius: 4px;
  pointer-events: none;
  box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.3);
  font-size: 12px;
}

.error-message {
  color: red;
  margin-bottom: 1em;
  text-align: center;
}
</style>
