<template>
  <div class="content-grid">
    <v-card class="section-card pa-6">
      <PageShell
        :eyebrow="t('pages.settings.eyebrow')"
        :title="t('pages.settings.title')"
        :subtitle="t('pages.settings.subtitle')"
      />

      <div class="stack mt-5">
        <v-alert type="info" variant="tonal">{{ t('pages.settings.googleOnly') }}: {{ auth.config?.google_only ? t('pages.settings.googleOnlyYes') : t('pages.settings.googleOnlyNo') }}</v-alert>
        <v-alert type="info" variant="tonal">{{ t('pages.settings.localLogin') }}: {{ auth.config?.local_auth_enabled ? t('pages.settings.localLoginEnabled') : t('pages.settings.localLoginDisabled') }}</v-alert>
        <v-alert type="info" variant="tonal">{{ t('pages.settings.authProvider') }}: {{ auth.user?.auth_provider || t('common.unknown') }}</v-alert>
      </div>
    </v-card>

    <v-card class="section-card pa-6 sticky-panel">
      <SectionHeading :title="t('pages.settings.account')" :subtitle="t('pages.settings.accountSubtitle')" />
      <div class="muted-box pa-4">
        <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.settings.name') }}</div>
        <div class="text-h6 font-weight-bold">{{ auth.user?.name || t('common.unknown') }}</div>
      </div>
      <div class="muted-box pa-4 mt-4">
        <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.settings.email') }}</div>
        <div class="text-h6 font-weight-bold">{{ auth.user?.email || t('common.unknown') }}</div>
      </div>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const { t } = useI18n();
</script>
