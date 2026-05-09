<template>
  <div class="stack">
    <PageShell
      :eyebrow="t('staff.eyebrow')"
      :title="t('staff.title')"
      :subtitle="t('staff.subtitle')"
    />

    <v-row>
      <v-col cols="12" sm="6" lg="3" v-for="card in summaryCards" :key="card.label">
        <MetricCard :label="card.label" :value="card.value" />
      </v-col>
    </v-row>

    <v-card class="section-card pa-6">
      <SectionHeading :title="t('staff.notesTitle')" :subtitle="t('staff.notesSubtitle')" />
      <div class="callout">
        <div class="text-subtitle-2 font-weight-bold">{{ t('staff.protectedSurface') }}</div>
        <div class="soft-text mt-1">{{ t('staff.protectedSurfaceCopy') }}</div>
      </div>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import client from "../api/client";
import MetricCard from "../components/MetricCard.vue";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";

const summary = ref<any>(null);
const { t } = useI18n();
onMounted(async () => {
  const { data } = await client.get("/staff/summary/");
  summary.value = data;
});

const summaryCards = computed(() => [
  { label: t("staff.users"), value: summary.value?.users ?? 0 },
  { label: t("staff.brands"), value: summary.value?.brands ?? 0 },
  { label: t("staff.generations"), value: summary.value?.generations ?? 0 },
  { label: t("staff.riskEvents"), value: summary.value?.risk_events ?? 0 },
]);
</script>
