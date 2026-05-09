<template>
  <div class="content-grid">
    <v-card class="section-card pa-6 pa-md-7">
      <PageShell
        :eyebrow="t('pages.generate.eyebrow')"
        :title="t('pages.generate.title')"
        :subtitle="t('pages.generate.subtitle')"
      />

      <v-form class="form-group mt-5">
        <div class="field-grid">
          <v-select
            v-model="form.brand_id"
            :items="brands"
            item-title="name"
            item-value="id"
            :label="`${t('forms.brand')} *`"
            :error-messages="fieldErrors.brand_id"
            required
          />
          <v-select
            v-model="form.template_id"
            :items="templateOptions"
            item-title="name"
            item-value="id"
            :label="t('forms.template')"
            :error-messages="fieldErrors.template_id"
          />
        </div>

        <div class="field-grid">
          <v-select
            v-model="form.generation_type"
            :items="generationTypeItems"
            item-title="title"
            item-value="value"
            :label="`${t('forms.generationType')} *`"
            :error-messages="fieldErrors.generation_type"
            required
          />
          <v-select
            v-model="form.output_format"
            :items="formatItems"
            item-title="title"
            item-value="value"
            :label="t('forms.outputFormat')"
            :error-messages="fieldErrors.output_format"
          />
        </div>

        <div class="field-grid">
          <v-select
            v-model="form.style"
            :items="styleItems"
            item-title="title"
            item-value="value"
            :label="`${t('forms.visualStyle')} *`"
            :error-messages="fieldErrors.style"
            required
          />
          <v-text-field
            v-model="form.special_offer"
            :label="t('forms.specialOffer')"
            :error-messages="fieldErrors.special_offer"
          />
        </div>

        <v-alert v-if="formError" type="error" variant="tonal" class="mt-2">
          {{ formError }}
        </v-alert>

        <v-text-field
          v-model="form.topic"
          :label="`${t('forms.topic')} *`"
          :error-messages="fieldErrors.topic"
          required
        />
        <div class="field-grid">
          <v-text-field
            v-model="form.product_service"
            :label="t('forms.productService')"
            :error-messages="fieldErrors.product_service"
          />
          <v-text-field
            v-model="form.campaign_theme"
            :label="t('forms.campaignTheme')"
            :error-messages="fieldErrors.campaign_theme"
          />
        </div>
        <div class="field-grid">
          <v-select
            v-model="form.objective"
            :items="objectiveItems"
            item-title="title"
            item-value="value"
            :label="`${t('forms.objective')} *`"
            :error-messages="fieldErrors.objective"
            required
          />
          <v-select
            v-model="form.tone"
            :items="toneItems"
            item-title="title"
            item-value="value"
            :label="`${t('forms.tone')} *`"
            :error-messages="fieldErrors.tone"
            required
          />
        </div>
        <div class="field-grid">
          <v-select
            v-model="form.language"
            :items="languageItems"
            item-title="title"
            item-value="value"
            :label="`${t('forms.language')} *`"
            :error-messages="fieldErrors.language"
            required
          />
        </div>

        <v-alert v-if="previewData" type="info" variant="tonal" class="mt-2">
          {{ t("pages.generate.previewCost") }}: {{ previewData.cost }} {{ t("common.points") }} ·
          {{ previewData.reason }} · {{ t("pages.wallet.currentBalance") }}: {{ previewData.points_balance }}.
        </v-alert>

        <v-alert v-if="previewData && previewData.cost > previewData.points_balance" type="warning" variant="tonal" class="mt-2">
          {{ t("pages.generate.insufficientPreviewPoints", { points: previewData.cost - previewData.points_balance }) }}
        </v-alert>

        <v-alert v-if="loading || previewLoading" type="info" variant="tonal" class="mt-2">
          <div class="d-flex align-center ga-3">
            <v-progress-circular indeterminate size="18" width="2" />
            <span>{{ loading ? t("pages.generate.generating") : t("pages.generate.previewing") }}</span>
          </div>
        </v-alert>

        <div class="d-flex flex-wrap ga-3 pt-2">
          <v-btn variant="outlined" @click="preview" :loading="previewLoading" :disabled="loading || previewLoading">
            {{ t("actions.previewCost") }}
          </v-btn>
          <v-btn color="primary" @click="submit" :loading="loading" :disabled="loading || previewLoading">
            {{ t("actions.generate") }}
          </v-btn>
        </div>
      </v-form>
    </v-card>

    <div class="stack sticky-panel">
      <v-card class="section-card pa-5">
        <SectionHeading :title="t('pages.generate.previewSummary')" :subtitle="t('pages.generate.previewSubtitle')" />
        <div class="stack">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.generate.selectedBrand") }}</div>
            <div class="text-h6 font-weight-bold">{{ selectedBrand?.name || t("common.noBrandYet") }}</div>
            <div class="soft-text mt-1">{{ selectedBrand?.niche || t("pages.generate.brandContext") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.generate.format") }}</div>
            <div class="text-h6 font-weight-bold">{{ formatLabel(form.output_format) }}</div>
            <div class="soft-text mt-1">{{ t("pages.generate.formatCopy") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.visualStyle") }}</div>
            <div class="text-h6 font-weight-bold">{{ styleLabel(form.style) }}</div>
            <div class="soft-text mt-1">{{ t("pages.generate.styleCopy") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.generate.generationType") }}</div>
            <div class="text-h6 font-weight-bold">{{ generationTypeLabel(form.generation_type) }}</div>
            <div class="soft-text mt-1">{{ t("pages.generate.generationCopy") }}</div>
          </div>
        </div>
      </v-card>

      <v-card class="section-card pa-5" v-if="result">
        <v-alert v-if="generationStatusMessage" :type="generationStatusType" variant="tonal" class="mb-4">
          <div class="text-subtitle-2 font-weight-bold mb-1">{{ generationStatusTitle }}</div>
          <div>{{ generationStatusMessage }}</div>
          <div v-if="generationStatusHint" class="soft-text mt-2">{{ generationStatusHint }}</div>
        </v-alert>

        <SectionHeading :title="t('pages.generate.result')" :subtitle="t('pages.generate.resultSubtitle')" />
        <div class="stack mt-4">
          <template v-if="result.status === 'completed'">
            <v-card v-if="result.generated_text" class="muted-box pa-4">
              <div class="text-caption text-uppercase font-weight-bold mb-2">{{ t("pages.generate.textResult") }}</div>
              <pre class="result-pre">{{ result.generated_text }}</pre>
            </v-card>

            <v-card v-if="structuredPayload" class="muted-box pa-4">
              <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-2">
                <div class="text-caption text-uppercase font-weight-bold">{{ t("pages.generate.payloadResult") }}</div>
                <v-chip size="small" variant="tonal">{{ t("pages.generate.structuredJson") }}</v-chip>
              </div>
              <pre class="result-pre">{{ structuredPayload }}</pre>
            </v-card>

            <v-card v-if="generatedImageUrl" class="muted-box pa-4">
              <div class="text-caption text-uppercase font-weight-bold mb-2">{{ t("pages.generate.imageResult") }}</div>
              <v-img :src="generatedImageUrl" class="rounded-lg border-elevation-1" cover height="340" />
              <div class="d-flex flex-wrap ga-2 mt-3">
                <v-btn variant="outlined" :href="generatedImageUrl" target="_blank">{{ t("actions.openImage") }}</v-btn>
              </div>
            </v-card>

            <v-card v-if="generatedVideoUrl || result.generation_type === 'video_future'" class="muted-box pa-4">
              <div class="text-caption text-uppercase font-weight-bold mb-2">{{ t("pages.generate.videoResult") }}</div>
              <video v-if="generatedVideoUrl" :src="generatedVideoUrl" controls class="generated-video" />
              <v-alert v-else type="info" variant="tonal">
                {{ t("pages.generate.videoPending") }}
              </v-alert>
            </v-card>
          </template>

          <v-card v-else class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-2">{{ t("pages.generate.incompleteResult") }}</div>
            <div class="soft-text">
              {{ result.status === "blocked" ? t("pages.generate.blockedNoContentCopy") : t("pages.generate.incompleteResultCopy") }}
            </div>
          </v-card>
        </div>

        <div class="d-flex flex-wrap ga-3 mt-4">
          <v-btn
            v-if="result.status === 'completed'"
            variant="outlined"
            @click="copy(result.generated_text || structuredPayload || generatedImageUrl || '')"
          >
            {{ t("actions.copy") }}
          </v-btn>
          <v-btn v-if="result.status === 'completed' && result.id" color="primary" @click="exportPost">{{ t("actions.export") }}</v-btn>
          <v-btn variant="outlined" @click="generationDetailsOpen = true">{{ t("pages.generate.viewGenerationData") }}</v-btn>
          <v-btn variant="outlined" to="/history">{{ t("nav.history") }}</v-btn>
        </div>
      </v-card>

    <v-card class="section-card pa-5" v-else>
      <div class="callout">
        <div class="text-subtitle-2 font-weight-bold">{{ t("pages.generate.exportReady") }}</div>
        <div class="soft-text mt-1">{{ t("pages.generate.exportReadyCopy") }}</div>
      </div>
    </v-card>
  </div>

    <v-dialog v-model="generationDetailsOpen" max-width="860">
      <v-card class="section-card pa-6">
        <div class="d-flex align-center justify-space-between ga-3 mb-4">
          <div>
            <div class="text-h6 font-weight-bold">{{ t("pages.generate.detailsTitle") }}</div>
            <div class="soft-text">{{ t("pages.generate.detailsSubtitle") }}</div>
          </div>
          <v-btn variant="text" icon="mdi-close" @click="generationDetailsOpen = false" />
        </div>

        <div class="field-grid">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.brand") }}</div>
            <div class="text-body-1 font-weight-medium">{{ generationDetails?.brand_name || t("common.noBrandYet") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.template") }}</div>
            <div class="text-body-1 font-weight-medium">{{ generationDetails?.template_name || t("common.none") }}</div>
          </div>
        </div>

        <div class="field-grid mt-4">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.generationType") }}</div>
            <div class="text-body-1 font-weight-medium">{{ generationTypeLabel(generationDetails?.generation_type || "") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.outputFormat") }}</div>
            <div class="text-body-1 font-weight-medium">{{ formatLabel(generationDetails?.output_format || "") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.visualStyle") }}</div>
            <div class="text-body-1 font-weight-medium">{{ styleLabel(generationDetails?.style || "") }}</div>
          </div>
        </div>

        <div class="stack mt-4">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.topic") }}</div>
            <div class="soft-text">{{ generationDetails?.topic || t("common.none") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.productService") }}</div>
            <div class="soft-text">{{ generationDetails?.product_service || t("common.none") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.campaignTheme") }}</div>
            <div class="soft-text">{{ generationDetails?.campaign_theme || t("common.none") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.objective") }}</div>
            <div class="soft-text">{{ objectiveLabel(generationDetails?.objective || "") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.tone") }}</div>
            <div class="soft-text">{{ toneLabel(generationDetails?.tone || "") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.language") }}</div>
            <div class="soft-text">{{ languageLabel(generationDetails?.language || "") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.specialOffer") }}</div>
            <div class="soft-text">{{ generationDetails?.special_offer || t("common.none") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.generate.promptInput") }}</div>
            <pre class="result-pre">{{ generationDetails?.prompt_input || t("common.none") }}</pre>
          </div>
        </div>

        <div class="d-flex justify-end mt-5">
          <v-btn color="primary" @click="generationDetailsOpen = false">{{ t("actions.close") }}</v-btn>
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import client from "../api/client";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";
import { extractApiErrorMessage, extractApiFieldErrors } from "../utils/apiErrors";

const { t } = useI18n();
const brands = ref<any[]>([]);
const templateOptions = computed(() => selectedBrand.value?.templates || []);
const selectedBrand = computed(() => brands.value.find((item) => item.id === form.value.brand_id));
const loading = ref(false);
const previewLoading = ref(false);
const previewData = ref<any>(null);
const result = ref<any>(null);
const generationDetailsOpen = ref(false);
const generationDetails = ref<any>(null);
const formError = ref("");
const fieldErrors = ref<Record<string, string[]>>({});

const form = ref({
  brand_id: null as number | null,
  template_id: null as number | null,
  generation_type: "full_post",
  output_format: "feed_square",
  style: "realistic",
  topic: "",
  product_service: "",
  objective: "sell",
  tone: "friendly",
  language: "en",
  campaign_theme: "",
  special_offer: "",
});

const generationTypeItems = computed(() => [
  { title: t("pages.generate.types.text"), value: "text" },
  { title: t("pages.generate.types.image"), value: "image" },
  { title: t("pages.generate.types.carousel"), value: "carousel" },
  { title: t("pages.generate.types.fullPost"), value: "full_post" },
  { title: t("pages.generate.types.imagePrompt"), value: "image_prompt" },
]);
const formatItems = computed(() => [
  { title: t("pages.generate.formats.feedSquare"), value: "feed_square" },
  { title: t("pages.generate.formats.feedPortrait"), value: "feed_portrait" },
  { title: t("pages.generate.formats.story"), value: "story" },
  { title: t("pages.generate.formats.reelCover"), value: "reel_cover" },
  { title: t("pages.generate.formats.carousel"), value: "carousel" },
]);
const styleItems = computed(() => [
  { title: t("pages.generate.styles.realistic"), value: "realistic" },
  { title: t("pages.generate.styles.animated"), value: "animated" },
  { title: t("pages.generate.styles.cartoon"), value: "cartoon" },
  { title: t("pages.generate.styles.ghibli"), value: "ghibli" },
  { title: t("pages.generate.styles.stickFigure"), value: "stick_figure" },
  { title: t("pages.generate.styles.isometric"), value: "isometric" },
  { title: t("pages.generate.styles.flat"), value: "flat" },
  { title: t("pages.generate.styles.minimal"), value: "minimal" },
  { title: t("pages.generate.styles.threeD"), value: "three_d" },
  { title: t("pages.generate.styles.cyberpunk"), value: "cyberpunk" },
  { title: t("pages.generate.styles.editorial"), value: "editorial" },
  { title: t("pages.generate.styles.premiumClean"), value: "premium_clean" },
  { title: t("pages.generate.styles.watercolor"), value: "watercolor" },
]);
const objectiveItems = computed(() => [
  { title: t("pages.generate.objectives.sell"), value: "sell" },
  { title: t("pages.generate.objectives.educate"), value: "educate" },
  { title: t("pages.generate.objectives.announcePromotion"), value: "announce_promotion" },
  { title: t("pages.generate.objectives.engagement"), value: "engagement" },
  { title: t("pages.generate.objectives.brandAwareness"), value: "brand_awareness" },
]);
const toneItems = computed(() => [
  { title: t("pages.generate.tones.professional"), value: "professional" },
  { title: t("pages.generate.tones.friendly"), value: "friendly" },
  { title: t("pages.generate.tones.fun"), value: "fun" },
  { title: t("pages.generate.tones.luxury"), value: "luxury" },
  { title: t("pages.generate.tones.urgent"), value: "urgent" },
  { title: t("pages.generate.tones.inspirational"), value: "inspirational" },
]);
const languageItems = computed(() => [
  { title: t("languages.en"), value: "en" },
  { title: t("languages.es"), value: "es" },
  { title: t("languages.pt"), value: "pt" },
]);

onMounted(async () => {
  const { data } = await client.get("/brands/");
  brands.value = data;
  if (brands.value[0]) {
    form.value.brand_id = brands.value[0].id;
    applyBrandDefaults(selectedBrand.value);
  }
});

watch(
  () => form.value.brand_id,
  () => {
    form.value.template_id = selectedBrand.value?.templates?.[0]?.id || null;
    applyBrandDefaults(selectedBrand.value);
  },
);

function applyBrandDefaults(brand: any) {
  if (!brand) return;
  if (!form.value.product_service.trim()) {
    form.value.product_service = firstMeaningfulText([
      brand.products_services,
      brand.description,
      brand.niche,
    ]);
  }
  if (!form.value.topic.trim() || isGenericTopic(form.value.topic)) {
    form.value.topic = firstMeaningfulText([
      brand.products_services,
      brand.description,
      brand.name,
      brand.niche,
    ]);
  }
  if ((!form.value.tone || form.value.tone === "friendly") && brand.tone_of_voice) {
    form.value.tone = brand.tone_of_voice;
  }
  if ((!form.value.language || form.value.language === "en") && brand.language) {
    form.value.language = brand.language;
  }
}

function isGenericTopic(value: string) {
  const normalized = value.trim().toLowerCase();
  return [
    "",
    "moderno",
    "modern",
    "teste",
    "test",
    "your offer",
    "your audience",
    "your topic",
    "your brand",
    "offer",
    "topic",
    "content",
  ].includes(normalized);
}

function firstMeaningfulText(values: unknown[]) {
  for (const value of values) {
    if (typeof value !== "string") continue;
    const cleaned = value.trim();
    if (cleaned && !isGenericTopic(cleaned)) {
      return cleaned;
    }
  }
  return "";
}

async function preview() {
  previewLoading.value = true;
  formError.value = "";
  fieldErrors.value = {};
  try {
    const { data } = await client.post("/generations/preview/", form.value);
    previewData.value = data;
  } catch (error) {
    fieldErrors.value = extractApiFieldErrors(error);
    formError.value = extractApiErrorMessage(error, t("errors.generationPreview"));
  } finally {
    previewLoading.value = false;
  }
}

async function submit() {
  loading.value = true;
  formError.value = "";
  fieldErrors.value = {};
  try {
    const { data } = await client.post("/generations/", form.value);
    result.value = data;
    generationDetails.value = buildGenerationDetails(data);
  } catch (error) {
    fieldErrors.value = extractApiFieldErrors(error);
    formError.value = extractApiErrorMessage(error, t("errors.generation"));
  } finally {
    loading.value = false;
  }
}

async function exportPost() {
  const { data } = await client.post(`/generations/${result.value.id}/export/`);
  result.value = { ...result.value, export: data };
}

async function copy(text: string) {
  if (text) await navigator.clipboard.writeText(text);
}

function buildGenerationDetails(apiResult: any) {
  const selectedTemplate = selectedBrand.value?.templates?.find((template: any) => template.id === form.value.template_id);
  return {
    brand_name: selectedBrand.value?.name || "",
    brand_niche: selectedBrand.value?.niche || "",
    template_name: selectedTemplate?.name || "",
    generation_type: form.value.generation_type,
    output_format: form.value.output_format,
    style: form.value.style,
    topic: form.value.topic,
    product_service: form.value.product_service,
    objective: form.value.objective,
    tone: form.value.tone,
    language: form.value.language,
    campaign_theme: form.value.campaign_theme,
    special_offer: form.value.special_offer,
    prompt_input: apiResult?.prompt_input || "",
  };
}

const structuredPayload = computed(() => {
  if (!result.value?.generated_payload || Object.keys(result.value.generated_payload).length === 0) return "";
  return JSON.stringify(result.value.generated_payload, null, 2);
});

const generatedImageUrl = computed(() => result.value?.generated_image_url || result.value?.generated_payload?.image_url || "");

const generatedVideoUrl = computed(
  () =>
    result.value?.generated_video_url ||
    result.value?.generated_payload?.video_url ||
    result.value?.generated_payload?.video?.url ||
    "",
);

const generationStatusType = computed(() => {
  if (result.value?.status === "failed") return "error";
  if (result.value?.status === "blocked") return "warning";
  if (result.value?.status === "pending") return "info";
  return "info";
});

const generationStatusMessage = computed(() => {
  if (!result.value) return "";
  if (result.value.status === "blocked") {
    return result.value.error_message
      ? t("pages.generate.blockedWithReason", { reason: result.value.error_message })
      : t("pages.generate.blockedGeneric");
  }
  if (result.value.status === "failed") {
    return result.value.error_message
      ? t("pages.generate.failedWithReason", { reason: result.value.error_message })
      : t("pages.generate.failedGeneric");
  }
  if (result.value.status === "pending") {
    return t("pages.generate.pending");
  }
  return "";
});

const generationStatusTitle = computed(() => {
  if (!result.value) return "";
  if (result.value.status === "blocked") return t("pages.generate.blockedTitle");
  if (result.value.status === "failed") return t("pages.generate.failedTitle");
  if (result.value.status === "pending") return t("pages.generate.pendingTitle");
  return t("pages.generate.result");
});

const generationStatusHint = computed(() => {
  if (!result.value || result.value.status !== "blocked") return "";
  const message = String(result.value.error_message || "").toLowerCase();
  const planLimitPatterns = [
    "per day",
    "1 image generation per day",
    "one image generation per day",
    "por dia",
    "por día",
    "límite diario",
    "limite diário",
  ];
  if (planLimitPatterns.some((pattern) => message.includes(pattern))) {
    return t("pages.generate.blockedPlanLimitHint");
  }
  if (message.includes("point") || message.includes("ponto") || message.includes("punto")) {
    return t("pages.generate.blockedPointsHint");
  }
  return "";
});

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

function formatLabel(format: string) {
  const mapping: Record<string, string> = {
    feed_square: "pages.generate.formats.feedSquare",
    feed_portrait: "pages.generate.formats.feedPortrait",
    story: "pages.generate.formats.story",
    reel_cover: "pages.generate.formats.reelCover",
    carousel: "pages.generate.formats.carousel",
  };
  return t(mapping[format] || "common.unknown");
}

function styleLabel(style: string) {
  const mapping: Record<string, string> = {
    realistic: "pages.generate.styles.realistic",
    animated: "pages.generate.styles.animated",
    cartoon: "pages.generate.styles.cartoon",
    ghibli: "pages.generate.styles.ghibli",
    stick_figure: "pages.generate.styles.stickFigure",
    isometric: "pages.generate.styles.isometric",
    flat: "pages.generate.styles.flat",
    minimal: "pages.generate.styles.minimal",
    three_d: "pages.generate.styles.threeD",
    cyberpunk: "pages.generate.styles.cyberpunk",
    editorial: "pages.generate.styles.editorial",
    premium_clean: "pages.generate.styles.premiumClean",
    watercolor: "pages.generate.styles.watercolor",
  };
  return t(mapping[style] || "common.unknown");
}

function objectiveLabel(value: string) {
  const mapping: Record<string, string> = {
    sell: "pages.generate.objectives.sell",
    educate: "pages.generate.objectives.educate",
    announce_promotion: "pages.generate.objectives.announcePromotion",
    engagement: "pages.generate.objectives.engagement",
    brand_awareness: "pages.generate.objectives.brandAwareness",
  };
  return t(mapping[value] || "common.unknown");
}

function toneLabel(value: string) {
  const mapping: Record<string, string> = {
    professional: "pages.generate.tones.professional",
    friendly: "pages.generate.tones.friendly",
    fun: "pages.generate.tones.fun",
    luxury: "pages.generate.tones.luxury",
    urgent: "pages.generate.tones.urgent",
    inspirational: "pages.generate.tones.inspirational",
  };
  return t(mapping[value] || "common.unknown");
}

function languageLabel(value: string) {
  const mapping: Record<string, string> = {
    en: "languages.en",
    es: "languages.es",
    pt: "languages.pt",
  };
  return t(mapping[value] || "common.unknown");
}
</script>
