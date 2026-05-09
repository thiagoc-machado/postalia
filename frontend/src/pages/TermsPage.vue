<template>
  <PageShell :eyebrow="t('pages.legal.title')" :title="t('pages.legal.termsTitle')" :subtitle="t('pages.legal.placeholderSubtitle')">
    <v-card class="section-card pa-6">
      <p class="soft-text mb-0">
        {{ t("pages.legal.termsCopy") }}
      </p>
    </v-card>
  </PageShell>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import PageShell from "../components/PageShell.vue";

const { t } = useI18n();
</script>
