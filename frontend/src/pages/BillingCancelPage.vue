<template>
  <PageShell :eyebrow="t('pages.billing.canceledEyebrow')" :title="t('pages.billing.canceledTitle')" :subtitle="t('pages.billing.canceledSubtitle')">
    <v-card class="section-card pa-6">
      <div class="soft-text">
        {{ t("pages.billing.canceledCopy") }}
      </div>
      <div class="d-flex flex-wrap ga-3 mt-5">
        <v-btn color="primary" to="/pricing">{{ t('actions.backToPricing') }}</v-btn>
        <v-btn variant="outlined" to="/dashboard">{{ t('actions.goToDashboard') }}</v-btn>
      </div>
    </v-card>
  </PageShell>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import PageShell from "../components/PageShell.vue";

const { t } = useI18n();
</script>
