<template>
  <v-btn-toggle v-model="model" variant="outlined" density="compact" divided>
    <v-btn value="en">EN</v-btn>
    <v-btn value="es">ES</v-btn>
    <v-btn value="pt">PT</v-btn>
  </v-btn-toggle>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";

const { locale } = useI18n();
const model = computed({
  get: () => locale.value,
  set: (next) => {
    locale.value = next;
    localStorage.setItem("postalia_locale", next);
  },
});
</script>
