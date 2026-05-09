<template>
  <div class="stack">
    <AdSlot placement="header" :visible="showAds" />

    <PageShell
      :eyebrow="t('pages.pricing.eyebrow')"
      :title="t('pages.pricing.title')"
      :subtitle="t('pages.pricing.subtitle')"
    />

    <v-alert v-if="!appConfig.creemEnabled" type="info" variant="tonal">
      {{ t("pages.pricing.paymentsDisabled") }}
    </v-alert>

    <v-row>
      <v-col v-for="plan in plans" :key="plan.code" cols="12" md="3">
        <v-card class="section-card pa-5 h-100 d-flex flex-column">
          <div class="d-flex align-center justify-space-between mb-3">
            <div class="text-h6 font-weight-bold">{{ planLabel(plan.code) }}</div>
            <v-chip v-if="plan.highlight" color="primary" size="small" variant="tonal">{{ t("pages.pricing.popular") }}</v-chip>
          </div>
          <div class="text-h3 font-weight-black mb-1">€{{ plan.price }}</div>
          <div class="soft-text mb-4">{{ t("common.perMonth") }}</div>
          <div class="feature-list">
            <div class="feature-item">
              <span class="feature-item__dot" />
              <span class="feature-item__text">{{ t("pages.pricing.textGenerations", { count: plan.text }) }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-item__dot" />
              <span class="feature-item__text">{{ t("pages.pricing.imageGenerations", { count: plan.images }) }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-item__dot" />
              <span class="feature-item__text">{{ t("pages.pricing.brandLimit", { count: plan.brands, plural: plan.brands > 1 ? "s" : "" }) }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-item__dot" />
              <span class="feature-item__text">{{ t(plan.noteKey) }}</span>
            </div>
          </div>
          <v-spacer />
          <v-btn
            class="mt-6"
            :variant="plan.code === currentPlanCode ? 'flat' : 'outlined'"
            :color="plan.highlight ? 'primary' : undefined"
            :disabled="plan.code !== 'free' && !appConfig.creemEnabled"
            :loading="loadingPlan === plan.code"
            @click="handlePlanClick(plan.code)"
          >
            {{ actionLabel(plan.code) }}
          </v-btn>
        </v-card>
      </v-col>
    </v-row>

    <AdSlot placement="footer" :visible="showAds" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import AdSlot from "../components/AdSlot.vue";
import PageShell from "../components/PageShell.vue";
import client from "../api/client";
import { appConfig } from "../config";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();
const { t } = useI18n();
const loadingPlan = ref("");
const currentPlanCode = computed(() => auth.billing?.plan_code || "free");
const showAds = computed(() => !auth.isAuthenticated || auth.isFreePlan);

const plans = [
  { code: "free", price: 0, text: 3, images: 0, brands: 1, noteKey: "pages.pricing.watermarkEnabled", highlight: false },
  { code: "starter", price: 5, text: 50, images: 10, brands: 1, noteKey: "pages.pricing.noWatermark", highlight: false },
  { code: "pro", price: 12, text: 200, images: 40, brands: 3, noteKey: "pages.pricing.savedBrandIdentity", highlight: true },
  { code: "agency", price: 29, text: 800, images: 150, brands: 999, noteKey: "pages.pricing.batchGenerationReady", highlight: false },
];

function planLabel(planCode: string) {
  return t(`plans.${planCode}`);
}

function actionLabel(planCode: string) {
  if (planCode === currentPlanCode.value) return t("pages.pricing.planCurrent");
  if (planCode === "free") return auth.isAuthenticated ? t("pages.pricing.planKeepFree") : t("pages.pricing.planStartFree");
  return appConfig.creemEnabled ? t("pages.pricing.planUpgrade") : t("pages.pricing.planPaymentsDisabled");
}

async function handlePlanClick(planCode: string) {
  if (planCode === "free") {
    if (auth.isAuthenticated) {
      await router.push("/dashboard");
      return;
    }
    await router.push(auth.config?.google_only ? "/login" : "/register");
    return;
  }
  if (!appConfig.creemEnabled) return;
  loadingPlan.value = planCode;
  try {
    const { data } = await client.post("/billing/checkout/", { plan_code: planCode });
    if (data?.checkout_url) {
      window.location.href = data.checkout_url;
    }
  } finally {
    loadingPlan.value = "";
  }
}
</script>
