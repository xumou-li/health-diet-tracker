<template>
  <view class="body-trend-chart" :id="containerId">
    <canvas
      class="body-trend-chart__canvas"
      :canvas-id="canvasId"
      :id="canvasId"
      :width="canvasWidth * pixelRatio"
      :height="canvasHeight * pixelRatio"
      :style="canvasStyle"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    />
  </view>
</template>

<script setup>
import { computed, getCurrentInstance, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import uCharts from '@qiun/ucharts'

const props = defineProps({
  canvasId: {
    type: String,
    required: true
  },
  categories: {
    type: Array,
    default: () => []
  },
  series: {
    type: Array,
    default: () => []
  },
  color: {
    type: String,
    default: '#4CAF50'
  },
  backgroundColor: {
    type: String,
    default: '#F8FAF8'
  },
  yAxisTitle: {
    type: String,
    default: ''
  },
  unitSuffix: {
    type: String,
    default: ''
  },
  heightRpx: {
    type: Number,
    // #ifdef MP-WEIXIN
    default: 400
    // #endif
    // #ifndef MP-WEIXIN
    default: 320
    // #endif
  },
  visibleCount: {
    type: Number,
    default: 7
  },
  labelStep: {
    type: Number,
    default: 1
  }
})

const instance = getCurrentInstance()
const instanceProxy = instance?.proxy

let chart = null
let renderToken = 0
let hasRendered = false
const pixelRatio = ref(1)
const canvasWidth = ref(0)
const canvasHeight = ref(0)

const containerId = computed(() => `${props.canvasId}-container`)

const canvasStyle = computed(() => {
  const width = canvasWidth.value ? `${canvasWidth.value}px` : '100%'
  const height = canvasHeight.value ? `${canvasHeight.value}px` : `${props.heightRpx}rpx`
  return `width: ${width}; height: ${height};`
})

const hasData = computed(() => {
  return props.categories.length > 0 && props.series.some(item => Array.isArray(item.data) && item.data.length)
})

const getPixelRatio = () => {
  const systemInfo = uni.getSystemInfoSync()
  const raw = systemInfo.pixelRatio || 1
  // #ifdef MP-WEIXIN
  return Math.min(raw, 2)
  // #endif
  // #ifndef MP-WEIXIN
  return raw
  // #endif
}

const getCanvasSize = async () => {
  return new Promise((resolve) => {
    const query = uni.createSelectorQuery()
    query
      .in(instanceProxy)
      .select(`#${containerId.value}`)
      .boundingClientRect((rect) => {
        if (rect?.width) {
          const width = rect.width
          const height = Math.round((props.heightRpx / 750) * uni.getSystemInfoSync().windowWidth)
          resolve({ width, height })
          return
        }

        const systemInfo = uni.getSystemInfoSync()
        resolve({
          width: systemInfo.windowWidth - 60,
          height: Math.round((props.heightRpx / 750) * systemInfo.windowWidth)
        })
      })
      .exec()
    })
}

const displayCategories = computed(() => {
  const step = Math.max(1, Number(props.labelStep) || 1)
  return props.categories.map((label, index) => {
    return index % step === 0 ? label : ''
  })
})

const resolvedSeries = computed(() => {
  return props.series.map((item) => ({
    connectNulls: true,
    ...item,
  }))
})

const resolvedVisibleCount = computed(() => {
  const fallbackCount = props.categories.length || 1
  return Math.max(1, Number(props.visibleCount) || fallbackCount)
})

const isNarrowChart = computed(() => {
  const fallbackWidth = uni.getSystemInfoSync().windowWidth || 0
  const width = canvasWidth.value || fallbackWidth
  return width > 0 && width <= 360
})

const axisFontSize = computed(() => {
  // #ifdef MP-WEIXIN
  return isNarrowChart.value ? 6 : 7
  // #endif
  // #ifndef MP-WEIXIN
  return isNarrowChart.value ? 7 : 10
  // #endif
})

const chartPadding = computed(() => {
  // #ifdef MP-WEIXIN
  return isNarrowChart.value ? [14, 6, 8, 4] : [14, 10, 8, 6]
  // #endif
  // #ifndef MP-WEIXIN
  return isNarrowChart.value ? [18, 6, 8, 4] : [18, 12, 8, 8]
  // #endif
})

const resolvedItemCount = computed(() => {
  const categoryCount = props.categories.length || 1
  const desiredCount = Math.min(categoryCount, resolvedVisibleCount.value)

  if (!isNarrowChart.value) return desiredCount

  const mobileCount = props.labelStep > 1 ? Math.max(3, desiredCount - 1) : desiredCount
  return Math.max(3, Math.min(categoryCount, mobileCount))
})

const xAxisLabelCount = computed(() => {
  if (!isNarrowChart.value) return undefined

  const categoryCount = props.categories.length || 1
  const width = canvasWidth.value || uni.getSystemInfoSync().windowWidth || 0
  const baseLabelCount = Math.max(3, Math.min(categoryCount, resolvedItemCount.value))

  if (categoryCount < 21) return baseLabelCount

  const widthDrivenLabelCount = width <= 340 ? 4 : 5
  return Math.max(3, Math.min(baseLabelCount, widthDrivenLabelCount))
})

const buildOptions = () => {
  return {
    type: 'line',
    context: uni.createCanvasContext(props.canvasId, instanceProxy),
    width: canvasWidth.value,
    height: canvasHeight.value,
    categories: displayCategories.value,
    series: resolvedSeries.value,
    animation: !hasRendered,
    background: props.backgroundColor,
    color: [props.color],
    padding: chartPadding.value,
    pixelRatio: pixelRatio.value,
    enableScroll: false,
    enableMarkLine: false,
    legend: {
      show: false
    },
    dataLabel: false,
    dataPointShape: true,
    xAxis: {
      disableGrid: true,
      fontColor: '#8A94A6',
      fontSize: axisFontSize.value,
      boundaryGap: 'justify',
      itemCount: resolvedItemCount.value,
      labelCount: xAxisLabelCount.value
    },
    yAxis: {
      gridType: 'dash',
      dashLength: 3,
      splitNumber: 5,
      fontColor: '#8A94A6',
      fontSize: axisFontSize.value,
      title: props.yAxisTitle,
      titleFontColor: '#5B6575',
      titleFontSize: axisFontSize.value,
      data: [
        {
          tofix: 1,
          unit: props.unitSuffix,
          fontSize: axisFontSize.value
        }
      ]
    },
    extra: {
      line: {
        type: 'curve',
        // #ifdef MP-WEIXIN
        width: 0.9,
        // #endif
        // #ifndef MP-WEIXIN
        width: 2,
        // #endif
        activeType: 'hollow',
        linearType: 'custom'
      },
      tooltip: {
        borderColor: '#D9E3F0',
        borderWidth: 1,
        bgColor: '#FFFFFF',
        fontColor: '#2F3640',
        legendShape: 'circle'
      }
    }
  }
}

const renderChart = async () => {
  const currentToken = ++renderToken

  if (!hasData.value) {
    chart = null
    hasRendered = false
    return
  }

  await nextTick()
  const size = await getCanvasSize()
  if (currentToken !== renderToken) return

  pixelRatio.value = getPixelRatio()
  canvasWidth.value = Math.round(size.width)
  canvasHeight.value = Math.round(size.height)

  await nextTick()
  if (currentToken !== renderToken) return

  chart = new uCharts(buildOptions())
  hasRendered = true
}

const handleTouchStart = (event) => {
  if (!chart) return
  chart.scrollStart(event)
}

const handleTouchMove = (event) => {
  if (!chart) return
  chart.scroll(event)
}

const handleTouchEnd = (event) => {
  if (!chart) return
  chart.scrollEnd(event)
  chart.showToolTip(event, {
    formatter: (item, category) => `${category} ${item.name}: ${item.data}${props.unitSuffix}`
  })
}

watch(
  () => [props.categories, props.series, props.labelStep, props.visibleCount],
  () => {
    renderChart()
  },
  { deep: true, immediate: true }
)

onBeforeUnmount(() => {
  chart = null
  hasRendered = false
})
</script>

<style lang="scss" scoped>
.body-trend-chart {
  width: 100%;
}

.body-trend-chart__canvas {
  width: 100%;
  display: block;
}
</style>
