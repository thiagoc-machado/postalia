<template>
  <PageShell
    :eyebrow="t('pages.billing.receivedEyebrow')"
    :title="t('pages.billing.receivedTitle')"
    :subtitle="t('pages.billing.receivedSubtitle')"
  >
    <v-card class="section-card pa-6">
      <div class="soft-text">
        {{ t("pages.billing.receivedCopy") }}
      </div>
      <div class="d-flex flex-wrap ga-3 mt-5">
        <v-btn color="primary" :loading="loading" @click="refreshSubscription">{{ t('pages.billing.refreshSubscription') }}</v-btn>
        <v-btn variant="outlined" to="/dashboard">{{ t('actions.goToDashboard') }}</v-btn>
      </div>
      <v-alert v-if="message" type="info" variant="tonal" class="mt-4">{{ message }}</v-alert>
    </v-card>
  </PageShell>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import PageShell from "../components/PageShell.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const { t } = useI18n();
const loading = ref(false);
const message = ref("");

async function refreshSubscription() {
  loading.value = true;
  try {
    await auth.loadBilling();
    message.value = auth.billing?.plan_code
      ? `${t("pages.billing.currentPlanPrefix")}: ${t(`plans.${auth.billing.plan_code}`)}`
      : t("pages.billing.subscriptionRefreshed");
  } finally {
    loading.value = false;
  }
}
</script>
