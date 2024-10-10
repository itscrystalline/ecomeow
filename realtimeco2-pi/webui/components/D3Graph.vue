<template>
  <div>
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    <div ref="graphContainer" class="graph-container"></div>
    <div ref="tooltip" class="tooltip"></div>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, onUnmounted} from 'vue'
import * as d3 from 'd3'
import {useFetch} from '#app'
import type {GraphConstraints, QueryParams} from "~/types/api";

// References and reactive states
const graphContainer = ref<HTMLElement | null>(null)
const tooltip = ref<HTMLElement | null>(null)
const data = ref<DataPoint[]>([])
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

    const {data: fetchData, error: fetchError} = await useFetch("/api/data", {
      query: props.params
    })

    if (fetchData.value && fetchData.value.success) {
      // Process and sort data
      data.value = fetchData.value.data
          .map((d) => ({
            date: new Date(d.time), // Parse ISO string to Date object
            content: +d[props.contentKey], // Ensure population is a number
          }))
          .sort((a: DataPoint, b: DataPoint) => a.date.getTime() - b.date.getTime()) // Sort data chronologically

      renderGraph()
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

// Define a simplified data point interface for the component
interface DataPoint {
  date: Date
  content: number
}

// Function to render the graph
const renderGraph = (): void => {
  if (!graphContainer.value) return
  d3.select(graphContainer.value).selectAll('*').remove()

  // Define data points
  const chartData: DataPoint[] = data.value.map(d => ({
    date: d.date,
    content: d.content,
  }))

  // Set dimensions
  const margin = {
    top: props.constraints.top,
    right: props.constraints.right,
    bottom: props.constraints.bottom,
    left: props.constraints.left
  }
  const width = props.constraints.width - margin.left - margin.right
  const height = props.constraints.height - margin.top - margin.bottom

  // Append SVG
  const svg = d3.select(graphContainer.value)
      .append('svg')
      .attr('width', props.constraints.width)
      .attr('height', props.constraints.height)
      .attr('viewBox', `0 0 ${props.constraints.width} ${props.constraints.height}`)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

  // Define scales
  const xScale = d3.scaleTime()
      .domain(d3.extent(chartData, d => d.date) as [Date, Date]) // Type assertion since d3.extent can return (Date | undefined)[]
      .range([0, width])

  const yScale = d3.scaleLinear()
      .domain([d3.min(chartData, d => d.content) as number, d3.max(chartData, d => d.content) as number]).nice()
      .range([height, 0])

  // Define the area generator
  const area = d3.area<DataPoint>()
      .x(d => xScale(d.date))
      .y0(height)
      .y1(d => yScale(d.content))
      .curve(d3.curveMonotoneX) // Smooths the area

  // Append the area path
  svg.append('path')
      .datum(chartData)
      .attr('fill', 'steelblue')
      .attr('d', area)

  const timeDiff: number = data.value[0].date.getTime() - data.value[data.value.length - 1].date.getTime()
  const moreThan1Day: boolean = timeDiff > 24 * 60 * 60 * 1000
  const moreThan3Days: boolean = timeDiff > 3 * 24 * 60 * 60 * 1000

  // Append X Axis
  svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).ticks(6).tickFormat(d3.timeFormat(moreThan3Days? '%B %d, %Y' : (moreThan1Day ? '%H:%M %B %d, %Y' : "%H:%M:%S"))))
      .selectAll('text')

  // Append Y Axis
  svg.append('g')
      .call(d3.axisLeft(yScale).ticks(6).tickFormat(d => formatNumberWithCommas(d)))

  // Add X Axis Label
  svg.append('text')
      .attr('x', width / 2)
      .attr('y', height + margin.bottom - 10)
      .attr('text-anchor', 'middle')
      .text('Date')

  // Add Y Axis Label
  svg.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -margin.left + 20)
      .attr('text-anchor', 'middle')
      .text(props.displayName ? props.displayName : props.contentKey)

  // Add data points (circles)
  svg.selectAll('circle')
      .data(chartData)
      .enter()
      .append('circle')
      .attr('cx', d => xScale(d.date))
      .attr('cy', d => yScale(d.content))
      .attr('r', 4)
      .attr('fill', 'steelblue')
      .on('mouseover', (event: MouseEvent, d: DataPoint) => {
        if (!tooltip.value) return
        const tooltipEl = d3.select(tooltip.value)
        tooltipEl
            .style('opacity', 1)
            .html(`
          <strong>Date:</strong> ${d3.timeFormat('%H:%M:%S %B %d, %Y')(d.date)}<br/>
          <strong>Population:</strong> ${formatNumberWithCommas(d.content)}
        `)
            .style('left', `${event.pageX + 10}px`)
            .style('top', `${event.pageY - 28}px`)
      })
      .on('mouseout', () => {
        if (!tooltip.value) return
        d3.select(tooltip.value)
            .style('opacity', 0)
      })
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
.graph-container {
  width: 100%;
  max-width: 1000px;
  position: relative; /* For tooltip positioning */
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

