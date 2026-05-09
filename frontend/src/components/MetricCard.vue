<template>
  <v-card class="metric-card pa-5">
    <div class="metric-card__label">{{ label }}</div>
    <div class="metric-card__value">{{ value }}</div>
    <div v-if="hint" class="metric-card__hint">{{ hint }}</div>
    <div v-if="$slots.default" class="metric-card__chip">
      <slot />
    </div>
  </v-card>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  hint?: string;
}>();
</script>
