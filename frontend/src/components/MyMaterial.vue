<template>
  <div class="content">
    <div class="content-header">
      <h1>Please choose your game unit to generate your pre-match material</h1>
      <!-- <div class="actions">
        <button>Filter</button>
      </div> -->
    </div>
    <div class="content-body">
      <div class="card" @click="card_click">
        <div class="date">August 7th, 16:30</div>
        <ul>
          <li>🤸‍♀️ Women's Floor Exercise</li>
          <li>🏆 Women's Floor Exercise Final</li>
        </ul>
      </div>
      <div class="card">
        <div class="date">August 10th, 16:30</div>
        <ul>
          <li>🏃‍♂️ Men's 400m Hurdles</li>
          <li>🏆 Men's 400m Hurdles Final</li>
        </ul>
      </div>
      <div class="card">
        <div class="date">August 8th, 15:00</div>
        <ul>
          <li>🏊‍♂️ Men's 10m Platform</li>
          <li>🏆 Men's 10m Platform Final</li>
        </ul>
      </div>
      <div class="card">
        <div class="date">August 6th, 16:30</div>
        <ul>
          <li>🤸‍♂️ Men's Floor Exercise</li>
          <li>🏆 Men's Floor Exercise Final</li>
        </ul>
      </div>
      <div class="card">
        <div class="date">August 2nd, 16:30</div>
        <ul>
          <li>🏊‍♀️ Women's 400m Individual Medley</li>
          <li>🏆 Women's 400m Individual Medley Final</li>
        </ul>
      </div>
      <div class="card">
        <div class="date">August 2nd, 16:30</div>
        <ul>
          <li>🏊‍♂️ Men's 400m Individual Medley</li>
          <li>🏆 Men's 400m Individual Medley Final</li>
        </ul>
      </div>
      <div class="card">
        <div class="date">August 11th, 16:30</div>
        <ul>
          <li>🏃‍♀️ Women's 400m Hurdles</li>
          <li>🏆 Women's 400m Hurdles Final</li>
        </ul>
      </div>
      <div class="card">
        <div class="date">August 9th, 15:00</div>
        <ul>
          <li>🏊‍♀️ Women's 10m Platform</li>
          <li>🏆 Women's 10m Platform Final</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>

export default {
  name: 'MyMaterial',
  data() {
    return {

    }
  },
  mounted() {

    console.log(this.$router)
    // this.$store.dispatch('increment');
  },
  methods: {
    gpt_test() {
      fetch("https://11.163.70.215:8001/llm/chat", {
        method: "POST",
        headers: {
          'Content-Type': 'application/octet-stream'
        },
        body: JSON.stringify({ "input": "Who is the fastest people in the world?", "user": "guest", "stream": true })
      })
        .then(response => {
          if (!response.body) {
            throw new Error("ReadableStream not supported by this browser.");
          }
          return response.body.getReader();
        })
        .then(reader => {
          const decoder = new TextDecoder('utf-8');
          let receivedLength = 0; // 计数器

          return reader.read().then(function processText({ done, value }) {
            if (done) {
              console.log("Stream completed.");
              return;
            }

            receivedLength += value.length;
            const chunk = decoder.decode(value, { stream: true });
            console.log(`Received ${chunk.length} bytes (${receivedLength} bytes in total)`);
            console.log(chunk);

            // 处理接收到的数据
            // 更新 UI，处理 chunk 数据

            return reader.read().then(processText);
          });
        })
        .catch(error => {
          console.error("Fetch error: ", error);
        });

    },
    card_click() {
      console.log('click')
      this.gpt_test();
      this.$router.push({ name: 'MaterialContent', params: { userId: '123' } })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: Arial, sans-serif;
  display: flex;
  height: 100vh;
  background-color: #f5f5f5;
}

.sidebar {
  width: 250px;
  background-color: #fff;
  border-right: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.sidebar-header {
  padding: 20px;
  font-size: 1.2em;
  font-weight: bold;
  color: #0b4f9a;
  display: flex;
  align-items: center;
}

.sidebar-header img {
  width: 24px;
  height: 24px;
  margin-right: 10px;
}

.sidebar-nav {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.sidebar-nav a {
  padding: 15px 20px;
  color: #333;
  text-decoration: none;
  cursor: pointer;
}

.sidebar-nav a:hover,
.sidebar-nav a.active {
  background-color: #0b4f9a;
  color: #fff;
}

.sidebar-footer {
  padding: 15px 20px;
  border-top: 1px solid #ddd;
}

.content {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.content-header h1 {
  font-size: 1.5em;
  color: #333;
}

.content-header .actions {
  display: flex;
  align-items: center;
}

.content-header .actions button {
  background-color: #0b4f9a;
  color: #fff;
  border: none;
  border-radius: 5px;
  padding: 10px 15px;
  cursor: pointer;
}

.content-body {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.card {
  background-color: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 15px;
}

.card .date {
  font-weight: bold;
  margin-bottom: 10px;
}

.card ul {
  list-style-type: none;
}

.card ul li {
  margin-bottom: 5px;
}

.card:hover {
  cursor: pointer;
}
</style>
