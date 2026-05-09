<template>
  <div class="stack">
    <PageShell
      :eyebrow="t('pages.dashboard.eyebrow')"
      :title="t('pages.dashboard.title')"
      :subtitle="t('pages.dashboard.subtitle')"
    >
      <template #actions>
        <v-btn color="primary" to="/generate">{{ t("pages.dashboard.generatePost") }}</v-btn>
        <v-btn variant="outlined" to="/history">{{ t("nav.history") }}</v-btn>
        <v-btn variant="outlined" to="/brands">{{ t("pages.dashboard.createBrand") }}</v-btn>
      </template>
    </PageShell>

    <v-card class="section-card pa-6 hero-panel">
      <div class="hero-grid">
        <div>
          <div class="d-flex flex-wrap ga-2 mb-4">
            <v-chip color="primary" variant="tonal">{{ planLabel(subscription?.plan?.code || "free") }}</v-chip>
            <v-chip color="secondary" variant="tonal">{{ brands.length }} {{ t("pages.dashboard.brands") }}</v-chip>
            <v-chip color="info" variant="tonal">{{ generations.length }} {{ t("pages.dashboard.generations") }}</v-chip>
          </div>
          <h2 class="text-h4 font-weight-black mb-3">
            {{ currentBrand?.name || t("pages.dashboard.noBrandYet") }}
          </h2>
          <p class="hero-copy">
            {{ currentBrand ? t("pages.dashboard.brandReady") : t("pages.dashboard.brandPrompt") }}
          </p>
          <div class="pill-row mt-6">
            <v-btn color="primary" to="/generate">{{ t("pages.dashboard.openGenerator") }}</v-btn>
            <v-btn variant="outlined" to="/history">{{ t("nav.history") }}</v-btn>
            <v-btn variant="outlined" to="/wallet">{{ t("pages.dashboard.viewWallet") }}</v-btn>
            <v-btn variant="text" to="/subscription">{{ t("pages.dashboard.planDetails") }}</v-btn>
          </div>
        </div>

        <div class="hero-visual">
          <div class="hero-visual__tile">
            <div class="hero-visual__metric">
              <strong>{{ wallet?.points_balance ?? 0 }}</strong>
              <span class="soft-text">{{ t("pages.dashboard.pointsBalance") }}</span>
            </div>
            <div class="hero-visual__caption">{{ t("pages.dashboard.auditSafe") }}</div>
          </div>
          <div class="hero-visual__tile">
            <div class="hero-visual__metric">
              <strong>{{ generations.length }}</strong>
              <span class="soft-text">{{ t("pages.dashboard.savedGenerations") }}</span>
            </div>
            <div class="hero-visual__caption">{{ t("pages.dashboard.organizedHistory") }}</div>
          </div>
          <AdSlot placement="dashboard" :visible="showAds" />
        </div>
      </div>
    </v-card>

    <v-row>
      <v-col cols="12" sm="6" lg="3">
      <MetricCard :label="t('pages.dashboard.plan')" :value="planLabel(subscription?.plan?.code || 'free')" :hint="t('pages.dashboard.planStatus')" />
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <MetricCard :label="t('pages.dashboard.points')" :value="wallet?.points_balance ?? 0" :hint="t('pages.dashboard.pointsBalance')" />
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <MetricCard :label="t('pages.dashboard.brands')" :value="brands.length" :hint="t('pages.dashboard.workspaceSubtitle')" />
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <MetricCard :label="t('pages.dashboard.generations')" :value="generations.length" :hint="t('pages.dashboard.recentGenerationsSubtitle')" />
      </v-col>
    </v-row>

    <div class="content-grid">
      <v-card class="section-card pa-5">
        <SectionHeading :title="t('pages.dashboard.recentGenerations')" :subtitle="t('pages.dashboard.recentGenerationsSubtitle')" />
        <v-list lines="two" class="bg-transparent">
          <v-list-item
            v-for="item in generations.slice(0, 5)"
            :key="item.id"
            :title="generationTypeLabel(item.generation_type)"
            :subtitle="statusLabel(item.status)"
          >
            <template #append>
              <v-chip size="small" variant="tonal">{{ item.points_spent || 0 }} {{ t("common.points") }}</v-chip>
            </template>
          </v-list-item>
        </v-list>
      </v-card>

      <v-card class="section-card pa-5">
        <SectionHeading :title="t('pages.dashboard.workspaceSnapshot')" :subtitle="t('pages.dashboard.workspaceSubtitle')" />
        <div class="stack">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.dashboard.currentBrand") }}</div>
            <div class="text-h6 font-weight-bold">{{ currentBrand?.name || t("pages.dashboard.noBrandYet") }}</div>
            <div class="soft-text mt-1">{{ currentBrand?.niche || t("pages.dashboard.currentBrandPrompt") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.dashboard.planStatus") }}</div>
            <div class="text-h6 font-weight-bold">{{ statusLabel(subscription?.status || "active") }}</div>
            <div class="soft-text mt-1">
              {{ subscription?.current_period_start || t("common.startDateUnavailable") }} - {{ subscription?.current_period_end || t("common.endDateUnavailable") }}
            </div>
          </div>
        </div>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import AdSlot from "../components/AdSlot.vue";
import client from "../api/client";
import MetricCard from "../components/MetricCard.vue";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";

const wallet = ref<any>(null);
const subscription = ref<any>(null);
const brands = ref<any[]>([]);
const generations = ref<any[]>([]);
const currentBrand = computed(() => brands.value.find((item) => item.is_default) || brands.value[0]);
const showAds = computed(() => subscription.value?.plan?.code === "free");
const { t } = useI18n();

onMounted(async () => {
  const [walletRes, subRes, brandsRes, genRes] = await Promise.all([
    client.get("/wallet/me/"),
    client.get("/subscription/me/"),
    client.get("/brands/"),
    client.get("/generations/"),
  ]);
  wallet.value = walletRes.data;
  subscription.value = subRes.data;
  brands.value = brandsRes.data;
  generations.value = genRes.data;
});

function planLabel(planCode: string) {
  return t(`plans.${planCode}`);
}

function generationTypeLabel(type: string) {
  const mapping: Record<string, string> = {
    text: "pages.generate.types.text",
    image: "pages.generate.types.image",
    carousel: "pages.generate.types.carousel",
    full_post: "pages.generate.types.fullPost",
    image_prompt: "pages.generate.types.imagePrompt",
  };
  return t(mapping[type] || "common.unknown");
}

function statusLabel(status: string) {
  return t(`statuses.${status}`) || status;
}
</script>
