<template>
  <div class="video-container">
    <video
      ref="video"
      @ended="handleVideoEnded"
      autoplay
      preload="auto"
      muted
      class="video-player"
    >
      <source src="@/assets/Welcome_Page.mp4" type="video/mp4" />
    </video>
  </div>
</template>

<script>
export default {
  name: "FullScreenVideo",
  props: {
    src: {
      type: String,
      required: true,
    },
  },
  methods: {
    handleVideoEnded() {},
  },
};
</script>

<style scoped>
.video-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 9999;
}

.video-player {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  transform: translate(-50%, -50%);
  object-fit: cover; 
}
</style>
