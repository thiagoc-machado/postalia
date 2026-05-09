<template>
  <div class="stack">
      <AdSlot placement="header" :visible="showAds" />
    <section class="hero-panel surface-card pa-6 pa-md-10 rounded-xl">
      <div class="hero-grid">
        <div class="hero-card">
          <p class="eyebrow">{{ t("pages.landing.eyebrow") }}</p>
          <h1 class="hero-title text-h3 text-md-h2 font-weight-black">
            {{ t("pages.landing.title") }}
          </h1>
          <p class="hero-copy">{{ t("pages.landing.copy") }}</p>

          <div class="hero-badges">
            <v-chip color="primary" variant="tonal">{{ t("pages.landing.secure") }}</v-chip>
            <v-chip color="secondary" variant="tonal">{{ t("pages.landing.mobile") }}</v-chip>
            <v-chip color="info" variant="tonal">{{ t("pages.landing.googleReady") }}</v-chip>
          </div>

          <div class="pill-row mt-6">
            <v-btn color="primary" size="large" :to="startFreeRoute">{{ t("pages.landing.startFree") }}</v-btn>
            <v-btn variant="outlined" size="large" to="/pricing">{{ t("actions.viewPricing") }}</v-btn>
            <v-btn variant="text" size="large" to="/login">{{ t("nav.login") }}</v-btn>
          </div>
        </div>

        <v-card class="section-card hero-visual pa-5">
          <div class="hero-visual__tile">
            <div class="hero-visual__metric">
              <strong>{{ t("pages.landing.metric1.value") }}</strong>
              <span class="soft-text">{{ t("pages.landing.metric1.label") }}</span>
            </div>
            <div class="hero-visual__caption">{{ t("pages.landing.metric1.copy") }}</div>
          </div>
          <div class="hero-visual__tile">
            <div class="hero-visual__metric">
              <strong>{{ t("pages.landing.metric2.value") }}</strong>
              <span class="soft-text">{{ t("pages.landing.metric2.label") }}</span>
            </div>
            <div class="hero-visual__caption">{{ t("pages.landing.metric2.copy") }}</div>
          </div>
          <div class="hero-visual__tile">
            <div class="hero-visual__metric">
              <strong>{{ t("pages.landing.metric3.value") }}</strong>
              <span class="soft-text">{{ t("pages.landing.metric3.label") }}</span>
            </div>
            <div class="hero-visual__caption">{{ t("pages.landing.metric3.copy") }}</div>
          </div>
          <div class="callout">
            <div class="text-subtitle-2 font-weight-bold">{{ t("pages.landing.trust.title") }}</div>
            <div class="soft-text mt-1">{{ t("pages.landing.trust.copy") }}</div>
          </div>
        </v-card>
      </div>
    </section>

    <v-row>
      <v-col cols="12" md="4" v-for="feature in features" :key="feature.title">
        <v-card class="section-card pa-5 h-100">
          <div class="text-overline text-primary">{{ feature.badge }}</div>
          <div class="text-h6 font-weight-bold mb-2">{{ feature.title }}</div>
          <div class="soft-text">{{ feature.copy }}</div>
        </v-card>
      </v-col>
    </v-row>

    <AdSlot placement="footer" :visible="showAds" />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import AdSlot from "../components/AdSlot.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const showAds = computed(() => !auth.isAuthenticated || auth.isFreePlan);
const startFreeRoute = computed(() => (auth.config?.google_only ? "/login" : "/register"));
const { t } = useI18n();

const features = computed(() => [
  {
    badge: t("pages.landing.feature1.badge"),
    title: t("pages.landing.feature1.title"),
    copy: t("pages.landing.feature1.copy"),
  },
  {
    badge: t("pages.landing.feature2.badge"),
    title: t("pages.landing.feature2.title"),
    copy: t("pages.landing.feature2.copy"),
  },
  {
    badge: t("pages.landing.feature3.badge"),
    title: t("pages.landing.feature3.title"),
    copy: t("pages.landing.feature3.copy"),
  },
]);
</script>
