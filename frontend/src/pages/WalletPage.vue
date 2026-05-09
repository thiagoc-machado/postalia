<template>
  <div class="content-grid">
    <v-card class="section-card pa-6">
      <PageShell
        :eyebrow="t('pages.wallet.eyebrow')"
        :title="t('pages.wallet.title')"
        :subtitle="t('pages.wallet.subtitle')"
      />

      <v-card class="hero-panel pa-5 mt-5">
        <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.wallet.currentBalance') }}</div>
        <div class="text-h2 font-weight-black">{{ wallet?.points_balance ?? 0 }} {{ t('common.points') }}</div>
        <div class="soft-text mt-1">{{ t('pages.wallet.balanceCopy') }}</div>
      </v-card>

      <v-card v-if="appConfig.enableRewardedAds && rewardStatus?.enabled" class="section-card pa-5 mt-5">
        <SectionHeading :title="t('pages.wallet.earnedPoints')" :subtitle="t('pages.wallet.earnedPointsSubtitle')" />
        <div class="field-grid">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.wallet.pointsPerAd') }}</div>
            <div class="text-h6 font-weight-bold">{{ rewardStatus.points_per_ad }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.wallet.dailyLimit') }}</div>
            <div class="text-h6 font-weight-bold">{{ rewardStatus.daily_limit }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.wallet.watchedToday') }}</div>
            <div class="text-h6 font-weight-bold">{{ rewardStatus.watched_today }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.wallet.remainingToday') }}</div>
            <div class="text-h6 font-weight-bold">{{ rewardStatus.remaining_today }}</div>
          </div>
        </div>
        <v-alert v-if="rewardMessage" class="mt-4" :type="rewardError ? 'error' : 'success'" variant="tonal">
          {{ rewardMessage }}
        </v-alert>
        <div class="d-flex flex-wrap ga-3 mt-4">
          <v-btn
            color="primary"
            :disabled="rewardLoading || rewardStatus.remaining_today <= 0"
            :loading="rewardLoading"
            @click="watchAd"
          >
            {{ t("actions.watchAd") }}
          </v-btn>
        </div>
      </v-card>
    </v-card>

    <v-card class="section-card pa-6 sticky-panel">
      <SectionHeading :title="t('pages.wallet.transactions')" :subtitle="t('pages.wallet.transactionsSubtitle')" />
      <v-list lines="two" class="bg-transparent">
        <v-list-item v-for="tx in transactions" :key="tx.id" :title="transactionTypeLabel(tx.transaction_type)" :subtitle="tx.reason">
          <template #append>
            <v-chip size="small" variant="tonal">{{ tx.amount }}</v-chip>
          </template>
        </v-list-item>
      </v-list>
      <AdSlot placement="sidebar" class-name="mt-5" :visible="showAds" />
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import AdSlot from "../components/AdSlot.vue";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";
import client from "../api/client";
import { appConfig } from "../config";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const { t } = useI18n();
const wallet = ref<any>(null);
const transactions = ref<any[]>([]);
const rewardStatus = ref<any>(null);
const rewardLoading = ref(false);
const rewardMessage = ref("");
const rewardError = ref(false);
const showAds = computed(() => auth.isFreePlan);

onMounted(async () => {
  const [walletRes, txRes, rewardRes] = await Promise.all([
    client.get("/wallet/me/"),
    client.get("/wallet/transactions/"),
    client.get("/rewards/ads/status/"),
  ]);
  wallet.value = walletRes.data;
  transactions.value = txRes.data;
  rewardStatus.value = rewardRes.data;
});

async function watchAd() {
  rewardLoading.value = true;
  rewardMessage.value = "";
  rewardError.value = false;
  try {
    const eventId = `mock-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    const { data } = await client.post("/rewards/ads/complete/", {
      external_event_id: eventId,
      metadata: { placement: "wallet" },
    });
    wallet.value = { ...wallet.value, points_balance: data.points_balance };
    rewardStatus.value = {
      ...rewardStatus.value,
      watched_today: (rewardStatus.value?.watched_today || 0) + 1,
      remaining_today: Math.max((rewardStatus.value?.remaining_today || 0) - 1, 0),
    };
    rewardMessage.value = t("pages.wallet.rewardSuccess", { points: data.points_awarded || appRewardPoints() });
  } catch (error: any) {
    rewardError.value = true;
    rewardMessage.value = error?.response?.data?.detail || t("pages.wallet.rewardError");
  } finally {
    rewardLoading.value = false;
  }
}

function appRewardPoints() {
  return rewardStatus.value?.points_per_ad ?? 5;
}

function transactionTypeLabel(type: string) {
  const mapping: Record<string, string> = {
    registration_bonus: "pages.wallet.transactionTypes.registrationBonus",
    daily_login: "pages.wallet.transactionTypes.dailyLogin",
    streak_bonus: "pages.wallet.transactionTypes.streakBonus",
    referral_bonus: "pages.wallet.transactionTypes.referralBonus",
    rewarded_ad: "pages.wallet.transactionTypes.rewardedAd",
    generation_spend: "pages.wallet.transactionTypes.generationSpend",
    manual: "pages.wallet.transactionTypes.manual",
  };
  return t(mapping[type] || "common.unknown");
}
</script>
