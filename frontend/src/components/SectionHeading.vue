<template>
  <div class="section-heading">
    <div>
      <p v-if="eyebrow" class="section-heading__eyebrow">{{ eyebrow }}</p>
      <h2 class="section-heading__title">{{ title }}</h2>
      <p v-if="subtitle" class="section-heading__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="d-flex flex-wrap justify-end ga-3">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
  eyebrow?: string;
}>();
</script>
