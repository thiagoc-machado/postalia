<template>
  <div class="content-grid">
    <v-card class="section-card pa-6 pa-md-7">
      <PageShell
        :eyebrow="t('pages.brands.wizard.eyebrow')"
        :title="pageTitle"
        :subtitle="pageSubtitle"
      />

      <v-alert v-if="isEditing" type="info" variant="tonal" class="mt-5">
        {{ t("pages.brands.wizard.editNotice") }}
      </v-alert>

      <v-progress-linear :model-value="(step / 4) * 100" class="my-5" color="primary" rounded />
      <div class="soft-text mb-4">{{ t("pages.brands.wizard.stepOf", { current: step, total: 4 }) }}</div>

      <v-alert v-if="formError" type="error" variant="tonal" class="mb-4">
        {{ formError }}
      </v-alert>

      <div v-if="step === 1" class="form-group">
        <div class="field-grid">
          <v-text-field
            v-model="form.name"
            :label="`${t('forms.brandName')} *`"
            :error-messages="fieldErrors.name"
            :disabled="isEditing"
            :readonly="isEditing"
            :hint="isEditing ? t('pages.brands.wizard.nameLockedHint') : ''"
            :persistent-hint="isEditing"
            required
          />
          <v-text-field
            v-model="form.niche"
            :label="`${t('forms.niche')} *`"
            :error-messages="fieldErrors.niche"
            required
          />
        </div>
        <div v-if="isEditing" class="muted-box pa-4 mb-4">
          <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.brands.wizard.slugLabel") }}</div>
          <div class="soft-text">{{ brandSlug || t("common.unset") }}</div>
        </div>
        <div class="field-grid">
          <v-text-field
            v-model="form.website"
            :label="t('forms.website')"
            :error-messages="fieldErrors.website"
            :hint="t('pages.brands.wizard.websiteHint')"
            persistent-hint
          />
          <v-text-field
            v-model="form.instagram_handle"
            :label="t('forms.instagramHandle')"
            :error-messages="fieldErrors.instagram_handle"
          />
        </div>
      </div>

      <div v-else-if="step === 2" class="form-group">
        <v-textarea
          v-model="form.target_audience"
          :label="t('forms.targetAudience')"
          :error-messages="fieldErrors.target_audience"
        />
        <v-textarea
          v-model="form.products_services"
          :label="t('forms.productsServices')"
          :error-messages="fieldErrors.products_services"
        />
        <v-textarea
          v-model="form.description"
          :label="t('forms.description')"
          :error-messages="fieldErrors.description"
        />
      </div>

      <div v-else-if="step === 3" class="form-group">
        <div class="field-grid">
          <v-text-field
            v-model="form.tone_of_voice"
            :label="t('forms.toneOfVoice')"
            :error-messages="fieldErrors.tone_of_voice"
          />
          <v-select
            v-model="form.language"
            :items="languageOptions"
            item-title="title"
            item-value="value"
            :label="t('forms.language')"
            :error-messages="fieldErrors.language"
          />
        </div>
        <div class="field-grid">
          <ColorPickerField
            v-model="form.primary_color"
            :label="t('forms.primaryColor')"
            :hint="t('pages.brands.wizard.primaryColorHint')"
            :error-messages="fieldErrors.primary_color"
          />
          <ColorPickerField
            v-model="form.secondary_color"
            :label="t('forms.secondaryColor')"
            :hint="t('pages.brands.wizard.secondaryColorHint')"
            :error-messages="fieldErrors.secondary_color"
          />
        </div>
        <div class="field-grid mt-4">
          <div class="stack">
            <v-file-input
              :model-value="logoFile"
              :label="t('forms.logo')"
              :hint="t('pages.brands.wizard.logoHint')"
              :error-messages="fieldErrors.logo"
              persistent-hint
              accept="image/*"
              prepend-icon="mdi-image"
              clearable
              @update:model-value="handleLogoChange"
            />
            <v-btn
              v-if="logoFile"
              variant="text"
              class="align-self-start"
              @click="clearLogo"
            >
              {{ t("pages.brands.wizard.clearLogo") }}
            </v-btn>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-3">{{ t("pages.brands.wizard.logoPreviewTitle") }}</div>
            <div class="brand-logo-preview">
              <img v-if="logoPreviewUrl" :src="logoPreviewUrl" :alt="form.name || t('forms.logo')" />
              <div v-else class="brand-logo-preview__empty">{{ brandInitial }}</div>
            </div>
            <div class="soft-text mt-3">{{ logoPreviewUrl ? t("pages.brands.wizard.logoPreviewCopy") : t("pages.brands.wizard.logoPreviewEmpty") }}</div>
          </div>
        </div>
      </div>

      <div v-else class="stack">
        <v-alert type="info" variant="tonal">
          {{ t("pages.brands.wizard.templateAutoCreated") }}
        </v-alert>
        <div class="callout">
          <div class="text-subtitle-2 font-weight-bold">{{ t("pages.brands.wizard.readyTitle") }}</div>
          <div class="soft-text mt-1">{{ t("pages.brands.wizard.readyCopy") }}</div>
        </div>
      </div>

      <div class="d-flex justify-space-between mt-6">
        <v-btn variant="outlined" :disabled="step === 1 || loading" @click="step--">{{ t("actions.back") }}</v-btn>
        <v-btn v-if="step < 4" color="primary" :disabled="loading" @click="step++">{{ t("actions.next") }}</v-btn>
        <v-btn v-else color="primary" :loading="loading" @click="submit">
          {{ isEditing ? t("actions.update") : t("pages.brands.wizard.create") }}
        </v-btn>
      </div>
    </v-card>

    <div class="stack">
      <v-card class="section-card pa-5 sticky-panel">
        <SectionHeading :title="t('pages.brands.wizard.previewTitle')" :subtitle="t('pages.brands.wizard.previewSubtitle')" />
        <BrandPreviewSkeleton
          class="mt-4"
          compact
          :brand-name="form.name"
          :niche="form.niche"
          :audience="form.target_audience"
          :tone="form.tone_of_voice"
          :language="form.language"
          :primary-color="form.primary_color"
          :secondary-color="form.secondary_color"
          :logo-url="logoPreviewUrl"
        />
      </v-card>

      <v-card class="section-card pa-5 sticky-panel">
        <SectionHeading :title="t('pages.brands.wizard.whyTitle')" :subtitle="t('pages.brands.wizard.whySubtitle')" />
        <div class="feature-list">
          <div class="feature-item">
            <span class="feature-item__dot" />
            <span class="feature-item__text">{{ t("pages.brands.wizard.why1") }}</span>
          </div>
          <div class="feature-item">
            <span class="feature-item__dot" />
            <span class="feature-item__text">{{ t("pages.brands.wizard.why2") }}</span>
          </div>
          <div class="feature-item">
            <span class="feature-item__dot" />
            <span class="feature-item__text">{{ t("pages.brands.wizard.why3") }}</span>
          </div>
        </div>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import client from "../api/client";
import BrandPreviewSkeleton from "../components/BrandPreviewSkeleton.vue";
import ColorPickerField from "../components/ColorPickerField.vue";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";
import { extractApiErrorMessage, extractApiFieldErrors } from "../utils/apiErrors";
import { resolveMediaUrl } from "../utils/media";

type BrandForm = {
  name: string;
  niche: string;
  website: string;
  instagram_handle: string;
  target_audience: string;
  products_services: string;
  description: string;
  tone_of_voice: string;
  primary_color: string;
  secondary_color: string;
  language: string;
  is_default: boolean;
};

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const step = ref(1);
const loading = ref(false);
const loadingBrand = ref(false);
const formError = ref("");
const fieldErrors = ref<Record<string, string[]>>({});
const brandSlug = ref("");
const existingLogoUrl = ref("");
const logoFile = ref<File | null>(null);
const logoObjectUrl = ref("");
const form = ref<BrandForm>({
  name: "",
  niche: "",
  website: "",
  instagram_handle: "",
  target_audience: "",
  products_services: "",
  description: "",
  tone_of_voice: "",
  primary_color: "",
  secondary_color: "",
  language: "en",
  is_default: true,
});

const brandId = computed(() => {
  const raw = route.params.id;
  if (!raw) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
});

const isEditing = computed(() => brandId.value !== null);
const pageTitle = computed(() =>
  isEditing.value ? t("pages.brands.wizard.editTitle") : t("pages.brands.wizard.title"),
);
const pageSubtitle = computed(() =>
  isEditing.value ? t("pages.brands.wizard.editSubtitle") : t("pages.brands.wizard.subtitle"),
);
const languageOptions = computed(() => [
  { title: t("languages.en"), value: "en" },
  { title: t("languages.es"), value: "es" },
  { title: t("languages.pt"), value: "pt" },
]);
const logoPreviewUrl = computed(() => logoObjectUrl.value || existingLogoUrl.value);
const brandInitial = computed(() => (form.value.name?.trim()?.slice(0, 1) || "P").toUpperCase());

onMounted(async () => {
  if (!isEditing.value) return;
  await loadBrand();
});

watch(brandId, async (next) => {
  if (!next) return;
  await loadBrand();
});

async function loadBrand() {
  if (!brandId.value) return;
  loadingBrand.value = true;
  formError.value = "";
  try {
    const { data } = await client.get(`/brands/${brandId.value}/`);
    brandSlug.value = data.slug || "";
    existingLogoUrl.value = resolveMediaUrl(data.logo);
    logoFile.value = null;
    form.value = {
      name: data.name || "",
      niche: data.niche || "",
      website: data.website || "",
      instagram_handle: data.instagram_handle || "",
      target_audience: data.target_audience || "",
      products_services: data.products_services || "",
      description: data.description || "",
      tone_of_voice: data.tone_of_voice || "",
      primary_color: data.primary_color || "",
      secondary_color: data.secondary_color || "",
      language: data.language || "en",
      is_default: Boolean(data.is_default),
    };
  } catch (error) {
    formError.value = extractApiErrorMessage(error, t("errors.brand"));
  } finally {
    loadingBrand.value = false;
  }
}

watch(logoFile, (next) => {
  if (logoObjectUrl.value) {
    URL.revokeObjectURL(logoObjectUrl.value);
    logoObjectUrl.value = "";
  }
  if (next instanceof File) {
    logoObjectUrl.value = URL.createObjectURL(next);
  }
});

function handleLogoChange(value: File | File[] | null) {
  const next = Array.isArray(value) ? value[0] || null : value;
  logoFile.value = next || null;
}

function clearLogo() {
  logoFile.value = null;
  if (logoObjectUrl.value) {
    URL.revokeObjectURL(logoObjectUrl.value);
    logoObjectUrl.value = "";
  }
}

async function submit() {
  loading.value = true;
  formError.value = "";
  fieldErrors.value = {};
  try {
    const payload = new FormData();
    Object.entries({
      ...form.value,
      is_default: isEditing.value ? form.value.is_default : true,
    }).forEach(([key, value]) => {
      payload.append(key, typeof value === "boolean" ? String(value) : String(value || ""));
    });
    if (!isEditing.value) {
      payload.append("create_default_template", "true");
    }
    if (logoFile.value) {
      payload.append("logo", logoFile.value);
    }
    const response =
      isEditing.value && brandId.value ? await client.patch(`/brands/${brandId.value}/`, payload) : await client.post("/brands/", payload);
    const nextBrandId = response.data.id;
    await router.push(`/brands/${nextBrandId}`);
  } catch (error) {
    fieldErrors.value = extractApiFieldErrors(error);
    formError.value = extractApiErrorMessage(error, t("errors.brand"));
    step.value = errorStepForFields(Object.keys(fieldErrors.value));
  } finally {
    loading.value = false;
  }
}

onBeforeUnmount(() => {
  if (logoObjectUrl.value) {
    URL.revokeObjectURL(logoObjectUrl.value);
    logoObjectUrl.value = "";
  }
});

function errorStepForFields(fields: string[]) {
  const step1 = new Set(["name", "niche", "website", "instagram_handle"]);
  const step2 = new Set(["target_audience", "products_services", "description"]);
  const step3 = new Set(["tone_of_voice", "language", "primary_color", "secondary_color"]);

  if (fields.some((field) => step1.has(field))) return 1;
  if (fields.some((field) => step2.has(field))) return 2;
  if (fields.some((field) => step3.has(field))) return 3;
  return step.value;
}
</script>

<style scoped>
.brand-logo-preview {
  width: 100%;
  max-width: 240px;
  aspect-ratio: 1 / 1;
  border-radius: 1.1rem;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: linear-gradient(160deg, rgba(15, 23, 42, 0.04), rgba(15, 23, 42, 0.08));
  border: 1px dashed rgba(15, 23, 42, 0.16);
}

.brand-logo-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.brand-logo-preview__empty {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  font-size: 2.1rem;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.5);
}

@media (max-width: 960px) {
  .brand-logo-preview {
    max-width: 100%;
  }
}
</style>
