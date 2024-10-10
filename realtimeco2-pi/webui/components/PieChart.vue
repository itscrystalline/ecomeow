<template>
  <div class="pie-chart-container" ref="pieChartContainer">
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
import type {EnergyApiResponse, EnergyData} from "~/types/api";
import {he} from "cronstrue/dist/i18n/locales/he";

// References
const pieChartContainer = ref<HTMLElement | null>(null)

// Tooltip state
interface TooltipData {
  category: string
  value: number
  percentage: number
}

const props = defineProps<{
  year: string
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

// Render the pie chart
const renderPieChart = (data: EnergyApiResponse) => {
  if (!pieChartContainer.value) return

  // Clear any existing SVG elements
  d3.select(pieChartContainer.value).selectAll('*').remove()

  // Convert data into an array
  let dataset = data[props.year]

  // Set dimensions and radius
  const width = 250
  const height = 250
  const margin = 20
  const radius = Math.min(width, height) / 2 - margin

  // Create SVG
  const svg = d3
      .select(pieChartContainer.value)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`)

  // Color scale
  const color = d3.scaleOrdinal<string>()
      .domain(['Fossil Fuels', 'Renewables'])
      .range(['#ffdb00', '#21e500'])

  // Compute the position of each group on the pie
  const pie = d3.pie<{ category: string; value: number }>()
      .sort(null)
      .value(d => d.value)

  const arc = d3.arc<d3.PieArcDatum<any>>()
      .innerRadius(0)
      .outerRadius(radius);

  // Prepare data for each year
  const data_ready = pie([
    {category: 'Fossil Fuels', value: dataset.totalFossilFuelProduction},
    {category: 'Renewables', value: dataset.totalRenewableProduction},
  ])

  // Append the slices for each category
  svg
      .selectAll('whatever')
      .data(data_ready)
      .enter()
      .append('path')
      .attr('d', d3.arc<d3.PieArcDatum<{ category: string; value: number }>>()
          .innerRadius(0)
          .outerRadius(radius)
      )
      .attr('fill', d => color(d.data.category) as string)
      .attr('stroke', 'white')
      .style('stroke-width', '2px')
      .on('mouseover', (event, d) => {
        const total = d3.sum(data_ready, d => d.data.value)
        const percentage = ((d.data.value / total) * 100).toFixed(2)
        tooltip.value = {
          visible: true,
          data: {
            category: d.data.category,
            value: d.data.value,
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


  // Optional: Add a title for each year's pie chart
  svg.selectAll('text')
      .data(data_ready)
      .enter()
      .append('text')
      .text((d: any) => `${d.data.category}: ${(100 * (d.data.value / (data_ready[0].value + data_ready[1].value))).toFixed(2)}%`)
      .attr("transform", (d: any) => `translate(${(arc.centroid(d) as [number, number]).join(",")})`)
      .style("text-anchor", "middle")
      .style("font-size", 15);

  svg
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('x', 0)
      .attr('y', (height / 2) - 15)
      .text(`${props.year}`)
}

let intervalId: number

onMounted(async () => {
  const apiData = await fetchData()
  if (apiData) {
    renderPieChart(apiData)
  }

  // Set up periodic data fetching every 5 minutes (300,000 ms)
  intervalId = window.setInterval(async () => {
    const newData = await fetchData()
    if (newData) {
      renderPieChart(newData)
    }
  }, 300000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
.pie-chart-container {
  position: relative;
  width: 100%;
  max-width: 500px;
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
