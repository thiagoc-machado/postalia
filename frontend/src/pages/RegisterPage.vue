<template>
  <div class="content-grid">
    <v-card class="section-card pa-6 pa-md-8 hero-panel">
      <p class="eyebrow">{{ t("nav.register") }}</p>
      <h1 class="hero-title text-h4 text-md-h3 font-weight-black">{{ t("pages.register.title") }}</h1>
      <p class="hero-copy">{{ t("pages.register.copy") }}</p>

      <div class="feature-list mt-6">
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t("pages.register.feature1") }}</span>
        </div>
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t("pages.register.feature2") }}</span>
        </div>
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t("pages.register.feature3") }}</span>
        </div>
      </div>
    </v-card>

    <v-card class="section-card pa-6 pa-md-8">
      <div class="card-title">
        <div>
          <div class="text-h6 font-weight-bold">{{ t("pages.register.cardTitle") }}</div>
          <div class="soft-text">{{ t("pages.register.cardSubtitle") }}</div>
        </div>
      </div>

      <v-alert v-if="auth.config?.google_only" type="warning" variant="tonal" class="mb-4">
        {{ t("pages.register.googleOnly") }}
      </v-alert>

      <v-form v-else @submit.prevent="submit" class="form-group">
        <v-alert v-if="formError" type="error" variant="tonal" class="mb-4">
          {{ formError }}
        </v-alert>
        <v-text-field v-model="form.name" :label="`${t('forms.name')} *`" :error-messages="fieldErrors.name" required />
        <v-text-field v-model="form.email" :label="`${t('forms.email')} *`" type="email" :error-messages="fieldErrors.email" required />
        <v-text-field
          v-model="form.password"
          :label="`${t('forms.password')} *`"
          type="password"
          :error-messages="fieldErrors.password"
          required
        />
        <v-text-field
          v-model="form.referral_code"
          :label="t('forms.referralCode')"
          :error-messages="fieldErrors.referral_code"
        />
        <v-btn color="primary" type="submit" :loading="loading">{{ t("actions.createAccount") }}</v-btn>
      </v-form>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { extractApiErrorMessage, extractApiFieldErrors } from "../utils/apiErrors";

const auth = useAuthStore();
const router = useRouter();
const { t } = useI18n();
const loading = ref(false);
const formError = ref("");
const fieldErrors = ref<Record<string, string[]>>({});
const form = ref({ name: "", email: "", password: "", referral_code: "" });

async function submit() {
  loading.value = true;
  formError.value = "";
  fieldErrors.value = {};
  try {
    await auth.register(form.value);
    await router.push("/dashboard");
  } catch (error) {
    fieldErrors.value = extractApiFieldErrors(error);
    formError.value = extractApiErrorMessage(error, t("errors.register"));
  } finally {
    loading.value = false;
  }
}
</script>
