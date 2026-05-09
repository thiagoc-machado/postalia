<template>
  <div class="stack">
    <PageShell
      :eyebrow="t('pages.subscription.eyebrow')"
      :title="t('pages.subscription.title')"
      :subtitle="t('pages.subscription.subtitle')"
    >
      <template #actions>
        <v-btn variant="outlined" :loading="portalLoading" @click="openPortal">{{ t('actions.manageBilling') }}</v-btn>
      </template>
    </PageShell>

    <v-card class="section-card pa-6 hero-panel">
      <div class="d-flex flex-wrap align-center justify-space-between ga-3">
        <div>
          <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.subscription.currentPlan') }}</div>
          <div class="text-h4 font-weight-black">{{ currentPlanLabel }}</div>
          <div class="soft-text mt-1">
            {{ t('pages.subscription.status') }}: {{ statusLabel(billing?.status || subscription?.status || "active") }}
          </div>
          <div class="soft-text">
            {{ periodLabel }}
          </div>
        </div>
        <div class="d-flex flex-wrap ga-2">
          <v-chip color="primary" variant="tonal">{{ currentPlanLabel }}</v-chip>
          <v-chip color="secondary" variant="tonal">{{ t('pages.subscription.rewardsAvailable') }}</v-chip>
        </div>
      </div>
    </v-card>

    <v-row>
      <v-col cols="12" md="4">
        <MetricCard :label="t('pages.subscription.textLimit')" :value="selectedPlan?.text_limit ?? 0" :hint="t('pages.subscription.textLimitHint')" />
      </v-col>
      <v-col cols="12" md="4">
        <MetricCard :label="t('pages.subscription.imageLimit')" :value="selectedPlan?.image_limit ?? 0" :hint="t('pages.subscription.imageLimitHint')" />
      </v-col>
      <v-col cols="12" md="4">
        <MetricCard :label="t('pages.subscription.brandLimit')" :value="selectedPlan?.brand_limit ?? 0" :hint="t('pages.subscription.brandLimitHint')" />
      </v-col>
    </v-row>

    <v-card class="section-card pa-6">
      <SectionHeading :title="t('pages.subscription.availablePlans')" :subtitle="t('pages.subscription.availablePlansSubtitle')" />
      <v-row>
        <v-col v-for="plan in plans" :key="plan.code" cols="12" md="3">
          <v-card class="section-card pa-5 h-100 d-flex flex-column" :variant="plan.code === currentPlanCode ? 'flat' : 'outlined'">
            <div class="d-flex align-center justify-space-between mb-3">
              <div class="text-h6 font-weight-bold">{{ planLabel(plan.code) }}</div>
              <v-chip v-if="plan.code === currentPlanCode" size="small" variant="tonal">{{ t("pages.subscription.current") }}</v-chip>
            </div>
            <div class="text-h4 font-weight-black mb-1">€{{ plan.monthly_price }}</div>
            <div class="feature-list">
              <div class="feature-item">
                <span class="feature-item__dot" />
                <span class="feature-item__text">{{ t("pages.pricing.textGenerations", { count: plan.text_limit }) }}</span>
              </div>
              <div class="feature-item">
                <span class="feature-item__dot" />
                <span class="feature-item__text">{{ t("pages.pricing.imageGenerations", { count: plan.image_limit }) }}</span>
              </div>
              <div class="feature-item">
                <span class="feature-item__dot" />
                <span class="feature-item__text">{{ t("pages.pricing.brandLimit", { count: plan.brand_limit, plural: plan.brand_limit > 1 ? "s" : "" }) }}</span>
              </div>
            </div>
            <v-spacer />
            <v-btn
              class="mt-6"
              :variant="plan.code === currentPlanCode ? 'flat' : 'outlined'"
              color="primary"
              :disabled="plan.code === 'free' || !appConfig.creemEnabled"
              :loading="loadingPlan === plan.code"
              @click="changePlan(plan.code)"
            >
              {{ actionLabel(plan.code) }}
            </v-btn>
          </v-card>
        </v-col>
      </v-row>
    </v-card>

    <v-card class="section-card pa-6">
      <div class="callout">
        <div class="text-subtitle-2 font-weight-bold">{{ t('pages.subscription.pointsAndRewards') }}</div>
        <div class="soft-text mt-1">{{ t('pages.subscription.pointsAndRewardsCopy') }}</div>
      </div>
      <v-alert v-if="portalMessage" class="mt-4" :type="portalError ? 'warning' : 'info'" variant="tonal">
        {{ portalMessage }}
      </v-alert>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";
import MetricCard from "../components/MetricCard.vue";
import client from "../api/client";
import { appConfig } from "../config";

const subscription = ref<any>(null);
const plans = ref<any[]>([]);
const billing = ref<any>(null);
const { t } = useI18n();
const loadingPlan = ref("");
const portalLoading = ref(false);
const portalMessage = ref("");
const portalError = ref(false);

const currentPlanCode = computed(() => billing.value?.plan_code || subscription.value?.plan?.code || "free");
const currentPlanLabel = computed(() => planLabel(currentPlanCode.value));
const periodLabel = computed(() => {
  const start = billing.value?.current_period_start || subscription.value?.current_period_start;
  const end = billing.value?.current_period_end || subscription.value?.current_period_end;
  return `${start || t("common.startDateUnavailable")} - ${end || t("common.endDateUnavailable")}`;
});
const selectedPlan = computed(() => plans.value.find((plan) => plan.code === currentPlanCode.value));

onMounted(async () => {
  const [subRes, plansRes, billingRes] = await Promise.all([
    client.get("/subscription/me/"),
    client.get("/plans/"),
    client.get("/billing/subscription/"),
  ]);
  subscription.value = subRes.data;
  plans.value = plansRes.data;
  billing.value = billingRes.data;
});

async function changePlan(planCode: string) {
  if (planCode === "free") return;
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

async function openPortal() {
  if (!appConfig.creemEnabled) return;
  portalLoading.value = true;
  portalMessage.value = "";
  portalError.value = false;
  try {
    const { data } = await client.post("/billing/portal/");
    if (data?.portal_url) {
      window.location.href = data.portal_url;
      return;
    }
    portalError.value = true;
    portalMessage.value = data?.detail || t("pages.billing.portalUnavailable");
  } finally {
    portalLoading.value = false;
  }
}

function planLabel(planCode: string) {
  return t(`plans.${planCode}`);
}

function statusLabel(status: string) {
  return t(`statuses.${status}`) || status;
}

function actionLabel(planCode: string) {
  if (planCode === currentPlanCode.value) return t("common.currentPlan");
  if (planCode === "free") return t("pages.pricing.planKeepFree");
  return appConfig.creemEnabled ? t("pages.pricing.planUpgrade") : t("pages.pricing.planPaymentsDisabled");
}
</script>
