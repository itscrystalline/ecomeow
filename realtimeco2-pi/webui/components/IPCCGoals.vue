<script setup lang="ts">
import type {SummaryApiResponse} from "~/types/api";
import {onMounted, onUnmounted} from "vue";

const data = ref<SummaryApiResponse | null>(null)

const fetchData = async (): Promise<SummaryApiResponse | null> => {
  try {
    const response = await fetch(`/api/summary`) // Adjust the endpoint as needed
    if (!response.ok) {
      console.error('Network response was not ok')
      return null
    }
    return await response.json()
  } catch (error) {
    console.error('Fetch error:', error)
    return null
  }
}

const p = (num: number, outOf: number): number => {
  return ((num / outOf) * 100)
}

const convert = (n: number) => {
  if (n < 1e3) return n;
  if (n >= 1e3 && n < 1e6)
    return +(n / 1e3).toFixed(3) + "K";
  if (n >= 1e6 && n < 1e9)
    return +(n / 1e6).toFixed(3) + "M";
  if (n >= 1e9 && n < 1e12)
    return +(n / 1e9).toFixed(3) + "B";
  if (n >= 1e12) return +(n / 1e12).toFixed(3) + " Trillion";
};

let intervalId: number

onMounted(async () => {
  data.value = await fetchData()

  // Set up periodic data fetching every 5 minutes (300,000 ms)
  intervalId = window.setInterval(async () => {
    data.value = await fetchData()
  }, 10000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<template>
  <table class="tg">
    <thead>
    <tr class="goal">
      <th class="tg-0lax"></th>
      <th class="tg-0lax">1.5°C ▼</th>
      <th class="tg-0lax">CO2 Reduction ▼ 45%</th>
      <th class="tg-0lax">Zero Carbon</th>
    </tr>
    </thead>
    <tbody>
    <tr>
      <td class="tg-0lax">2030</td>
      <td class="tg-0lax"
          :style="data?.temp2030 > 1.5 ? (p(data?.temp2030, 1.5) > 500 ? 'color: darkred' : 'color: red') : 'color: darkgreen'">
        <h4 class="nomargin">{{ data?.temp2030.toFixed(2) }}°C {{ data?.temp2030 > 1.5 ? "▲" : "▼" }}
          ({{ p(data?.temp2030, 1.5).toFixed(1) }}%)</h4>
      </td>
      <td class="tg-0lax" :style="data?.percent2030 > -45 ? 'color: red' : 'color: darkgreen'"><h4 class="nomargin">{{ data?.percent2030 > 0 ? "+" : "" }}{{
          data?.percent2030.toFixed(2)
        }}%</h4></td>
      <td class="tg-0lax"><h4 class="nomargin" style="color: red">{{ convert(data?.emissions2030) }}</h4></td>
    </tr>
    <tr>
      <td class="tg-0lax">2050</td>
      <td class="tg-0lax"
          :style="data?.temp2050 > 1.5 ? (p(data?.temp2050, 1.5) > 500 ? 'color: darkred' : 'color: red') : 'color: darkgreen'">
        <h4 class="nomargin">{{ data?.temp2050.toFixed(2) }}°C {{ data?.temp2050 > 1.5 ? "▲" : "▼" }}
          ({{ p(data?.temp2050, 1.5).toFixed(1) }}%)</h4>
      </td>
      <td class="tg-0lax"
          :style="data?.percent2050 > -45 ? 'color: darkred' : 'color: darkgreen'">
        <h4 class="nomargin">{{ data?.percent2050 > 0 ? "+" : "" }}{{ data?.percent2050.toFixed(2) }}%</h4>
      </td>
      <td class="tg-0lax"><h4 class="nomargin" style="color: darkred">{{ convert(data?.emissions2050) }}</h4></td>
    </tr>
    </tbody>
  </table>
</template>

<style scoped>
.tg {
  border-collapse: collapse;
  border-spacing: 0;
}

.tg td {
  border-color: white;
  border-style: solid;
  border-width: 1px;
  font-size: 1.1em;
  overflow: hidden;
  padding: 10px 5px;
  word-break: normal;
}

.tg th {
  border-color: white;
  border-style: solid;
  border-width: 1px;
  overflow: hidden;
  padding: 10px 5px;
  word-break: normal;
}

.tg .tg-0lax {
  text-align: center;
  vertical-align: top
}

.goal {
  font-size: 1.2em;
  font-weight: bold;
  color: #00a900;
}

.noborder {
  border: none;
}

.nomargin {
  margin: 0;
}
</style>