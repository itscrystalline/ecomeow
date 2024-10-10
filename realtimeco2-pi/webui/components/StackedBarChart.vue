<!-- components/StackedBarChart.vue -->
<template>
  <div class="stacked-bar-chart-container" ref="stackedBarChartContainer">
    <!-- Tooltip for interactivity -->
    <div
        v-if="tooltip.visible"
        :style="tooltip.style"
        class="tooltip"
    >
      <strong>{{ tooltip.data.category }}</strong><br/>
      Value: {{ formatNumberWithCommas(tooltip.data.value) }}<br/>
      Percentage: {{ tooltip.data.percentage }}%
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, onUnmounted} from 'vue'
import * as d3 from 'd3'
import {EnergyApiResponse, EnergyData} from '~/types/energy'
import type {GraphConstraints} from "~/types/api";

// References
const stackedBarChartContainer = ref<HTMLElement | null>(null)

// Tooltip state
interface TooltipData {
  category: string
  value: number
  percentage: number
}

const props = defineProps<{
  constraints: GraphConstraints
}>()

const tooltip = ref<{
  visible: boolean
  data: TooltipData
  style: { [key: string]: string }
}>({
  visible: false,
  data: {category: '', value: 0, percentage: 0},
  style: {},
})

// Formatting function
const formatNumberWithCommas = (num: number): string => {
  return d3.format(',')(num)
}

// Fetch data from API
const fetchData = async (): Promise<EnergyApiResponse | null> => {
  try {
    const response = await fetch('/api/predicted?type=energy')
    if (!response.ok) {
      console.error('Network response was not ok')
      return null
    }
    const data: EnergyApiResponse = await response.json()
    return data
  } catch (error) {
    console.error('Fetch error:', error)
    return null
  }
}

// Render the stacked bar chart
const renderStackedBarChart = (data: EnergyApiResponse) => {
  if (!stackedBarChartContainer.value) return

  // Clear any existing SVG elements
  d3.select(stackedBarChartContainer.value).selectAll('*').remove()

  // Convert data into an array
  const dataset = Object.values(data).map((d: EnergyData) => ({
    year: d.year.toString(),
    hydropower: d.hydropowerProduction,
    windPower: d.windPowerProduction,
    solarPower: d.solarPowerProduction,
    otherRenewable: d.otherRenewablePowerProduction,
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
      .select(stackedBarChartContainer.value)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .attr(
          'viewBox',
          `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`
      )
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

  // List of subgroups (renewable categories)
  const subgroups = ['hydropower', 'windPower', 'solarPower', 'otherRenewable']

  // List of groups (years)
  const groups = dataset.map(d => d.year)

  // X scale
  const xScale = d3.scaleBand<string>()
      .domain(groups)
      .range([0, width])
      .padding(0.6)

  // Add X axis
  svg.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(d3.axisBottom(xScale))

  // Y scale
  const yScale = d3.scaleLinear()
      .domain([0, d3.max(dataset, d =>
          d.hydropower + d.windPower + d.solarPower + d.otherRenewable
      )! * 1.1])
      .range([height, 0])

  // Add Y axis
  svg.append('g')
      .call(d3.axisLeft(yScale).ticks(5).tickFormat(d => formatNumberWithCommas(d)))

  // Color palette
  const color = d3.scaleOrdinal<string>()
      .domain(subgroups)
      .range(['#37a6f1', '#fdbf3c', '#2ca02c', '#d62728']) // Customize colors as needed

  // Stack the data
  const stackedData = d3.stack<d3.SeriesPoint<EnergyData>>()
      .keys(subgroups)
      (dataset as any)

  // Show the bars
  const base = svg
      .selectAll('g.layer')
      .data(stackedData)
      .enter()
      .append('g')
      .attr('class', 'layer')
      .attr('fill', d => color(d.key) as string)
      .selectAll('rect')
      .data(d => d)
      .enter()

  base.append('rect')
      .attr('x', d => xScale(d.data.year)!)
      .attr('y', d => yScale(d[1]))
      .attr('height', d => yScale(d[0]) - yScale(d[1]))
      .attr('width', xScale.bandwidth())
      .on('mouseover', (event, d) => {
        // Determine which subgroup this rect belongs to
        const subgroupName = (event.currentTarget as SVGRectElement).parentNode
            ?.nodeName === 'g' ?
            (event.currentTarget as SVGRectElement).parentElement?.__data__.key : 'Unknown'

        if (!subgroupName) return

        const category = subgroupName.charAt(0).toUpperCase() + subgroupName.slice(1)
        const value = d[1] - d[0]
        const total = d3.sum(subgroups, key => d3.sum(dataset, d => d[key as keyof typeof d] as number))
        const percentage = ((value / total) * 100).toFixed(2)

        tooltip.value = {
          visible: true,
          data: {
            category,
            value,
            percentage: Number(percentage),
          },
          style: {
            left: `${event.pageX + 10}px`,
            top: `${event.pageY - 28}px`,
          },
        }
      })
      .on('mouseout', () => {
        tooltip.value.visible = false
      })

  base.append("text")
      .attr('x', d => xScale(d.data.year)! - 60)
      .attr('y', d => ((yScale(d[1]) - yScale(d[0])) / 2) + yScale(d[0]))
      .text(d => {
        const value = d[1] - d[0]
        const total = d3.sum(subgroups, key => d3.sum(dataset, d => d[key as keyof typeof d] as number))
        const percentage = ((value / total) * 100).toFixed(2)
        return `${percentage * 2}%`
      })


  svg
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('x', width / 2)
      .attr('y', -20)
      .text("Renewable Energy Consumption by Year, By Source")

  // Add Y axis label
  svg.append('text')
      .attr('text-anchor', 'middle')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -margin.left + 20)
      .text('Energy Production (in Gigawatt-hours)')

  // Add X axis label
  svg.append('text')
      .attr('text-anchor', 'middle')
      .attr('x', width / 2)
      .attr('y', height + margin.bottom - 10)
      .text('Year')

  // Optional: Add a legend
  const legend = svg.append('g')
      .attr('transform', `translate(${width - 150}, 0)`)

  subgroups.forEach((key, index) => {
    legend.append('rect')
        .attr('x', props.constraints.legendShift || 0)
        .attr('y', index * 20)
        .attr('width', 15)
        .attr('height', 15)
        .attr('fill', color(key) as string)

    legend.append('text')
        .attr('x', (props.constraints.legendShift || 0) + 20)
        .attr('y', index * 20 + 12)
        .text(() => {
          switch (key) {
            case 'hydropower':
              return 'Hydropower'
            case 'windPower':
              return 'Wind Power'
            case 'solarPower':
              return 'Solar Power'
            case 'otherRenewable':
              return 'Other Renewables'
            default:
              return key
          }
        })
        .attr('font-size', '12px')
        .attr('alignment-baseline', 'middle')
  })
}

let intervalId: number

onMounted(async () => {
  const apiData = await fetchData()
  if (apiData) {
    renderStackedBarChart(apiData)
  }

  // Set up periodic data fetching every 5 minutes (300,000 ms)
  intervalId = window.setInterval(async () => {
    const newData = await fetchData()
    if (newData) {
      renderStackedBarChart(newData)
    }
  }, 300000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
.stacked-bar-chart-container {
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
</style>
