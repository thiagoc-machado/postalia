<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" temporary class="mobile-drawer d-md-none" width="320">
      <div class="pa-5 pb-4">
        <div class="brand-lockup mb-4">
          <span class="brand-mark brand-mark--small">P</span>
          <div>
            <div>{{ t("app.name") }}</div>
            <span class="brand-subtitle">{{ t("app.tagline") }}</span>
          </div>
        </div>
        <v-list class="nav-list" density="comfortable">
          <v-list-item v-for="item in navItems" :key="item.to" :to="item.to" :title="item.label" rounded="lg" />
        </v-list>
        <v-divider class="my-4" />
        <div class="stack">
          <LanguageSwitcher />
          <v-btn v-if="auth.isAuthenticated" color="primary" to="/generate">{{ t("nav.generate") }}</v-btn>
          <v-btn v-if="auth.isAuthenticated" variant="outlined" @click="logout">{{ t("nav.logout") }}</v-btn>
        </div>
      </div>
    </v-navigation-drawer>

    <v-layout class="app-shell">
      <v-app-bar flat color="transparent" density="comfortable" class="app-header px-3 px-md-6">
        <v-app-bar-nav-icon class="d-md-none" @click="drawer = !drawer" />
        <RouterLink class="brand-lockup me-4" to="/">
          <span class="brand-mark">P</span>
          <div>
            <div>{{ t("app.name") }}</div>
            <span class="brand-subtitle">{{ t("app.tagline") }}</span>
          </div>
        </RouterLink>
        <div class="d-none d-md-flex align-center ga-1">
          <v-btn v-for="item in navItems" :key="item.to" variant="text" :to="item.to">{{ item.label }}</v-btn>
        </div>
        <v-spacer />
        <v-chip v-if="auth.config" class="d-none d-md-inline-flex me-3" size="small" variant="tonal" color="primary">
          {{ auth.config.google_only ? t("pages.settings.googleOnly") : t("pages.settings.localLogin") }}
        </v-chip>
        <LanguageSwitcher class="d-none d-sm-inline-flex me-3" />
        <v-btn v-if="!auth.isAuthenticated" class="d-none d-sm-inline-flex me-2" variant="text" to="/login">{{ t("nav.login") }}</v-btn>
        <v-btn
          v-if="!auth.isAuthenticated"
          color="primary"
          class="d-none d-sm-inline-flex"
          to="/register"
          :disabled="auth.config?.google_only"
        >
          {{ t("nav.register") }}
        </v-btn>
        <v-btn v-if="auth.user?.is_staff" variant="outlined" class="ms-2 d-none d-md-inline-flex" to="/staff">{{ t("nav.staff") }}</v-btn>
        <v-btn v-if="auth.isAuthenticated" variant="text" class="ms-2 d-none d-md-inline-flex" @click="logout">
          {{ t("nav.logout") }}
        </v-btn>
      </v-app-bar>

      <v-main>
        <v-container class="app-container app-content">
          <router-view />
        </v-container>
        <v-container class="app-container page-footer">
          <div class="d-flex flex-wrap align-center justify-space-between ga-3">
            <div class="soft-text">{{ t("app.name") }} · {{ t("app.tagline") }}</div>
            <div class="d-flex flex-wrap ga-2">
              <v-btn variant="text" size="small" to="/terms">{{ t("pages.legal.termsTitle") }}</v-btn>
              <v-btn variant="text" size="small" to="/privacy">{{ t("pages.legal.privacyTitle") }}</v-btn>
            </div>
          </div>
        </v-container>
      </v-main>
    </v-layout>
  </v-app>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "./stores/auth";
import LanguageSwitcher from "./components/LanguageSwitcher.vue";

const { t } = useI18n();
const auth = useAuthStore();
const drawer = ref(false);
const logout = () => auth.logout();

const navItems = computed(() => {
  if (auth.isAuthenticated) {
    const items = [
      { label: t("nav.dashboard"), to: "/dashboard" },
      { label: t("nav.generate"), to: "/generate" },
      { label: t("nav.history"), to: "/history" },
      { label: t("nav.brands"), to: "/brands" },
      { label: t("nav.wallet"), to: "/wallet" },
      { label: t("nav.referrals"), to: "/referrals" },
      { label: t("nav.subscription"), to: "/subscription" },
      { label: t("nav.settings"), to: "/settings" },
    ];
    if (auth.user?.is_staff) items.push({ label: t("nav.staff"), to: "/staff" });
    return items;
  }

  return [
    { label: t("nav.home"), to: "/" },
    { label: t("nav.pricing"), to: "/pricing" },
    { label: t("nav.login"), to: "/login" },
    { label: t("nav.register"), to: "/register" },
  ];
});
</script>
