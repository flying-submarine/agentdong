<template>
    <div id="charts" :style="{ width: config.width, height: config.height }"></div>
</template>
<script>
import * as echarts from 'echarts';
export default {
    props: {
        config: {
            type: Object,
            default: () => { return { width: '900px', height: '300px' } },
        },
    },
    methods: {
        reset() {
            const el = echarts.init(document.getElementById('charts'))
            el.clear()
        },
        set_option(options) {
            this.$nextTick(_ => {
                const el = echarts.init(document.getElementById('charts'))
                el.clear()
                el.setOption(options);
            })
        },
        show_data_with_bar(data, config = {}) {
            const { title = '', data_key = 'name', data_max_set = {} } = config
            const legend_data = data.map(x => (x[data_key]))
            if (!legend_data[0]) {
                console.error(`show_data_with_radar: can not find key: ${data_key} in data`)
                return
            }
            const serie_keys = Object.keys(data[0]).filter(x => (x !== data_key))
            // const radar_indicator = serie_keys.map(x => ({ name: x, max: data_max_set[x] ?? 10 }))
            const series_data = data.map(x => ({ data: serie_keys.map(k => (x[k])), type:'bar', name: x[data_key] }))
        
            var option = {
                title: {
                    text: title
                },
                tooltip: {},
                legend: {
                    data: legend_data
                },
                xAxis: {
                    data: serie_keys
                },
                yAxis: {},
                series: series_data
            };
            this.set_option(option)
        },
        show_data_with_radar(data, config = {}) {
            const { title = '', data_key = 'name', data_max_set = {} } = config
            if (!data || data.length === 0) {
                console.error(`show_data_with_radar: data invalid`)
                return
            }
            const legend_data = data.map(x => (x[data_key]))
            if (!legend_data[0]) {
                console.error(`show_data_with_radar: can not find key: ${data_key} in data`)
                return
            }
            const serie_keys = Object.keys(data[0]).filter(x => (x !== data_key))
            const radar_indicator = serie_keys.map(x => ({ name: x, max: data_max_set[x] ?? 10 }))
            const series_data = data.map(x => ({ value: serie_keys.map(k => (x[k])), name: x[data_key] }))

            // console.log(data, title, data_key)
            // console.log(legend_data, serie_keys, radar_indicator, series_data)
            const option = {
                title: {
                    text: title,
                },
                tooltip: {},
                legend: {
                    data: legend_data,
                },
                radar: {
                    indicator: radar_indicator,
                },
                series: [{
                    type: 'radar',
                    data: series_data,
                }]
            };
            this.set_option(option)
        }
    },
};
</script>
<style scoped></style>