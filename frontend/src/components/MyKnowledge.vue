<template>
    <div class="wrapper flex-column">
        empty
    </div>
</template>

<script>
export default {
    name: 'MyKnowledge',
    data() {
        return {

        }
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
* {
    margin: 0;
    padding: 0;
}

.wrapper {
    width: 100%;
}

img {
    width: 300px;
}

.row-scroll {
    width: 100%;
    overflow: auto;
    white-space: nowrap;
}

.wrap {
    flex-wrap: wrap;
    justify-content: space-around;
}

.flex-row {
    display: flex;
    flex-direction: row;
    padding: 5px;
}

.flex-column {
    display: flex;
    flex-direction: column;
}
</style>
