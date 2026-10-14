<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
const paused = ref(false)
const update = () => { paused.value = document.hidden }
onMounted(() => { update(); document.addEventListener('visibilitychange', update) })
onUnmounted(() => document.removeEventListener('visibilitychange', update))
</script>

<template>
  <div class="proposal-ambient" :class="{ paused }" aria-hidden="true">
    <svg v-for="side in ['left', 'right']" :key="side" :class="side" viewBox="0 0 120 560" preserveAspectRatio="none">
      <path v-for="x in [0, 18, 36, 54]" :key="x" :d="`M ${x} -40 C ${110+x} 160 ${-90+x} 330 ${x} 600`" />
    </svg>
    <i v-for="i in 6" :key="i" :style="{left: `${i % 2 ? i : 100-i}%`, animationDelay: `${-i*3}s`}" />
  </div>
</template>

<style>
.proposal-ambient { position:absolute;inset:0;pointer-events:none;overflow:hidden; }
.proposal-ambient svg { position:absolute;top:-5%;height:110%;width:36px;fill:none;stroke:var(--cf-red);stroke-width:.8;opacity:.22;animation:proposal-flow 24s ease-in-out infinite alternate; }
.proposal-ambient .left {left:-10px;scale:-1 1;}
.proposal-ambient .right {right:-10px;animation-delay:-12s;}
.proposal-ambient i {position:absolute;bottom:0;width:3px;height:3px;border-radius:50%;background:var(--cf-red);opacity:0;animation:proposal-rise 22s linear infinite;}
.proposal-ambient.paused * {animation-play-state:paused;}
@keyframes proposal-flow {to{translate:0 20px;}}
@keyframes proposal-rise {15%{opacity:.35;}to{transform:translateY(-400px);opacity:0;}}
@media(prefers-reduced-motion:reduce){.proposal-ambient *{animation:none!important;}}
@media print{.proposal-ambient{display:none;}}
</style>
