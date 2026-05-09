<template>
  <div class="content-grid">
    <v-card class="section-card pa-6 pa-md-8 hero-panel">
      <p class="eyebrow">{{ t("nav.login") }}</p>
      <h1 class="hero-title text-h4 text-md-h3 font-weight-black">{{ t("nav.login") }}</h1>
      <p class="hero-copy">{{ t("pages.login.copy") }}</p>

      <div class="feature-list mt-6">
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t("pages.login.feature1") }}</span>
        </div>
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t("pages.login.feature2") }}</span>
        </div>
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t("pages.login.feature3") }}</span>
        </div>
      </div>
    </v-card>

    <v-card class="section-card pa-6 pa-md-8">
      <div class="card-title">
        <div>
          <div class="text-h6 font-weight-bold">{{ t("pages.login.cardTitle") }}</div>
          <div class="soft-text">{{ t("pages.login.cardSubtitle") }}</div>
        </div>
      </div>

      <v-alert v-if="sessionInvalidMessage" type="warning" variant="tonal" class="mb-4">
        {{ sessionInvalidMessage }}
      </v-alert>

      <v-form @submit.prevent="submit" class="form-group">
        <GoogleLoginButton :client-id="googleClientId" :on-credential="auth.googleLogin" />

        <template v-if="!auth.config?.google_only">
          <v-divider class="my-1" />
          <v-alert v-if="formError" type="error" variant="tonal" class="mb-4">
            {{ formError }}
          </v-alert>
          <v-text-field
            v-model="form.email"
            :label="`${t('forms.email')} *`"
            type="email"
            :error-messages="fieldErrors.email"
            required
          />
          <v-text-field
            v-model="form.password"
            :label="`${t('forms.password')} *`"
            type="password"
            :error-messages="fieldErrors.password"
            required
          />
          <v-btn color="primary" type="submit" :loading="loading">{{ t("actions.loginWithEmail") }}</v-btn>
        </template>

        <v-alert v-else type="info" variant="tonal">
          {{ t("pages.login.googleOnly") }}
        </v-alert>
      </v-form>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import GoogleLoginButton from "../components/GoogleLoginButton.vue";
import { useAuthStore } from "../stores/auth";
import { extractApiErrorMessage, extractApiFieldErrors } from "../utils/apiErrors";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const { t } = useI18n();
const loading = ref(false);
const formError = ref("");
const fieldErrors = ref<Record<string, string[]>>({});
const form = ref({ email: "", password: "" });
const googleClientId = computed(() => import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined);
const sessionInvalidMessage = computed(() =>
  route.query.session === "invalid" ? t("pages.login.sessionInvalid") : "",
);

async function submit() {
  loading.value = true;
  formError.value = "";
  fieldErrors.value = {};
  try {
    await auth.login(form.value);
    await router.push("/dashboard");
  } catch (error) {
    fieldErrors.value = extractApiFieldErrors(error);
    formError.value = extractApiErrorMessage(error, t("errors.login"));
  } finally {
    loading.value = false;
  }
}
</script>
