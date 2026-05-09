<template>
  <div class="content-grid">
    <v-card class="section-card pa-6">
      <PageShell
        :eyebrow="t('pages.history.eyebrow')"
        :title="t('pages.history.title')"
        :subtitle="t('pages.history.subtitle')"
      />

      <AdSlot placement="header" :visible="showAds" class-name="mt-5" />

      <v-alert v-if="errorMessage" class="mt-5" type="error" variant="tonal">
        {{ errorMessage }}
      </v-alert>

      <div class="stack mt-5">
        <v-skeleton-loader v-if="loading" type="article, article, article" />

        <template v-else-if="generations.length">
          <InstagramPostCard
            v-for="item in generations"
            :key="item.id"
            :brand-name="brandNameFor(item)"
            :brand-meta="brandMetaFor(item)"
            :generation-label="generationTypeLabel(item.generation_type)"
            :status-label="statusLabel(item.status)"
            :output-format-label="formatLabel(item.output_format)"
            :points-spent-label="t('pages.history.pointsSpent', { points: item.points_spent || 0 })"
            :caption-label="t('pages.history.caption')"
            :caption-text="captionTextFor(item)"
            :hashtags-text="hashtagsTextFor(item)"
            :slides-text="slidesFor(item)"
            :design-notes="designNotesFor(item)"
            :image-url="imageUrlFor(item)"
            :empty-title="t('pages.history.emptyImageTitle')"
            :empty-copy="t('pages.history.emptyImageCopy')"
            :slides-label="t('pages.history.slides')"
            :design-notes-label="t('pages.history.designNotes')"
            :details-label="t('pages.history.viewDetails')"
            :created-at-label="t('pages.history.postedOn', { date: formatDateTime(item.created_at) })"
            @details="openDetails(item)"
          />
        </template>

        <v-card v-else class="section-card pa-8 text-center">
          <div class="text-h6 font-weight-bold">{{ t("pages.history.noGenerations") }}</div>
          <div class="soft-text mt-2">{{ t("pages.history.noGenerationsCopy") }}</div>
          <v-btn class="mt-5" color="primary" to="/generate">{{ t("actions.generate") }}</v-btn>
        </v-card>
      </div>
    </v-card>

    <v-card class="section-card pa-6 sticky-panel">
      <SectionHeading :title="t('pages.history.planAwareAds')" :subtitle="t('pages.history.planAwareAdsSubtitle')" />
      <AdSlot placement="sidebar" :visible="showAds" />
    </v-card>
  </div>

  <v-dialog v-model="detailsOpen" max-width="960">
    <v-card class="section-card pa-6">
      <div class="d-flex align-center justify-space-between ga-3 mb-4">
        <div>
          <div class="text-h6 font-weight-bold">{{ t("pages.history.detailsTitle") }}</div>
          <div class="soft-text">{{ t("pages.history.detailsSubtitle") }}</div>
        </div>
        <v-btn variant="text" icon="mdi-close" @click="detailsOpen = false" />
      </div>

      <template v-if="selectedGeneration">
        <div class="field-grid">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.brand") }}</div>
            <div class="text-body-1 font-weight-medium">{{ brandNameFor(selectedGeneration) }}</div>
            <div class="soft-text text-caption mt-1">{{ brandMetaFor(selectedGeneration) || t("common.none") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.template") }}</div>
            <div class="text-body-1 font-weight-medium">{{ templateNameFor(selectedGeneration) }}</div>
          </div>
        </div>

        <div class="field-grid mt-4">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.generationType") }}</div>
            <div class="text-body-1 font-weight-medium">{{ generationTypeLabel(selectedGeneration.generation_type) }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("forms.outputFormat") }}</div>
            <div class="text-body-1 font-weight-medium">{{ formatLabel(selectedGeneration.output_format) }}</div>
          </div>
        </div>

        <div class="field-grid mt-4">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.history.provider") }}</div>
            <div class="text-body-1 font-weight-medium">{{ selectedGeneration.ai_provider || t("pages.history.demo") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.history.model") }}</div>
            <div class="text-body-1 font-weight-medium">{{ selectedGeneration.ai_model || t("common.unknown") }}</div>
          </div>
        </div>

        <div class="field-grid mt-4">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.history.pointsSpent") }}</div>
            <div class="text-body-1 font-weight-medium">{{ selectedGeneration.points_spent || 0 }} {{ t("pages.history.pts") }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.history.status") }}</div>
            <div class="text-body-1 font-weight-medium">{{ statusLabel(selectedGeneration.status) }}</div>
          </div>
        </div>

        <div class="stack mt-4">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.history.promptInput") }}</div>
            <pre class="result-pre">{{ selectedGeneration.prompt_input || t("pages.history.noPrompt") }}</pre>
          </div>

          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.history.generatedText") }}</div>
            <pre class="result-pre">{{ selectedGeneration.generated_text || t("common.none") }}</pre>
          </div>

          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t("pages.history.generatedPayload") }}</div>
            <pre class="result-pre">{{ prettyJson(selectedGeneration.generated_payload) }}</pre>
          </div>
        </div>

        <div class="d-flex justify-end mt-5">
          <v-btn color="primary" @click="detailsOpen = false">{{ t("actions.close") }}</v-btn>
        </div>
      </template>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import client from "../api/client";
import AdSlot from "../components/AdSlot.vue";
import InstagramPostCard from "../components/InstagramPostCard.vue";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";
import { extractApiErrorMessage } from "../utils/apiErrors";
import { useAuthStore } from "../stores/auth";

type BrandTemplateRecord = {
  id: number;
  name: string;
};

type BrandRecord = {
  id: number;
  name: string;
  niche?: string | null;
  instagram_handle?: string | null;
  language?: string | null;
  templates?: BrandTemplateRecord[];
};

type GenerationRecord = {
  id: number;
  brand: number;
  template: number | null;
  generation_type: string;
  output_format: string;
  prompt_input: string;
  generated_text: string;
  generated_payload: Record<string, unknown>;
  generated_image_url: string;
  ai_provider: string;
  ai_model: string;
  points_spent: number;
  status: string;
  error_message: string;
  created_at: string;
};

const auth = useAuthStore();
const generations = ref<GenerationRecord[]>([]);
const brands = ref<BrandRecord[]>([]);
const loading = ref(true);
const errorMessage = ref("");
const detailsOpen = ref(false);
const selectedGeneration = ref<GenerationRecord | null>(null);
const showAds = computed(() => auth.isFreePlan);
const { t, locale } = useI18n();

onMounted(async () => {
  loading.value = true;
  errorMessage.value = "";

  const [generationResult, brandResult] = await Promise.allSettled([
    client.get("/generations/"),
    client.get("/brands/"),
  ]);

  if (generationResult.status === "fulfilled") {
    generations.value = generationResult.value.data;
  } else {
    errorMessage.value = extractApiErrorMessage(generationResult.reason, t("pages.history.loadError"));
  }

  if (brandResult.status === "fulfilled") {
    brands.value = brandResult.value.data;
  } else if (!errorMessage.value) {
    errorMessage.value = extractApiErrorMessage(brandResult.reason, t("pages.history.loadError"));
  }

  loading.value = false;
});

const brandLookup = computed(() => new Map(brands.value.map((brand) => [brand.id, brand])));

function getBrand(record: GenerationRecord) {
  return brandLookup.value.get(record.brand);
}

function brandNameFor(record: GenerationRecord) {
  return getBrand(record)?.name || t("pages.history.brandUnknown");
}

function brandMetaFor(record: GenerationRecord) {
  const brand = getBrand(record);
  if (!brand) return "";
  const languageLabel = brand.language ? t(`languages.${brand.language}`) : "";
  return [brand.niche, brand.instagram_handle ? `@${brand.instagram_handle.replace(/^@/, "")}` : "", languageLabel]
    .filter(Boolean)
    .join(" · ");
}

function templateNameFor(record: GenerationRecord) {
  const brand = getBrand(record);
  const template = brand?.templates?.find((item) => item.id === record.template);
  return template?.name || t("pages.history.templateUnknown");
}

function generationTypeLabel(type: string) {
  const mapping: Record<string, string> = {
    text: "pages.generate.types.text",
    image: "pages.generate.types.image",
    carousel: "pages.generate.types.carousel",
    full_post: "pages.generate.types.fullPost",
    image_prompt: "pages.generate.types.imagePrompt",
    video_future: "pages.generate.types.videoFuture",
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

function statusLabel(status: string) {
  return t(`statuses.${status}`) || status;
}

function captionTextFor(record: GenerationRecord) {
  const payload = normalizePayload(record.generated_payload);
  const candidates = [
    payload.caption,
    payload.content,
    payload.short_hook,
    payload.title,
    looksLikeJson(record.generated_text) ? "" : record.generated_text,
    record.prompt_input,
  ];
  return firstText(candidates) || t("pages.history.noPrompt");
}

function hashtagsTextFor(record: GenerationRecord) {
  const payload = normalizePayload(record.generated_payload);
  const hashtags = payload.hashtags;
  if (Array.isArray(hashtags)) {
    return hashtags.map((item) => String(item).trim()).filter(Boolean).join(" ");
  }
  if (typeof hashtags === "string") {
    return hashtags.trim();
  }
  return "";
}

function slidesFor(record: GenerationRecord) {
  const payload = normalizePayload(record.generated_payload);
  const slides = payload.carousel_slides;
  if (Array.isArray(slides)) {
    return slides.map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof slides === "string") {
    return slides
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

function designNotesFor(record: GenerationRecord) {
  const payload = normalizePayload(record.generated_payload);
  const candidates = [payload.recommended_design_notes, payload.image_prompt];
  return firstText(candidates);
}

function imageUrlFor(record: GenerationRecord) {
  const payload = normalizePayload(record.generated_payload);
  const candidates = [record.generated_image_url, payload.image_url, payload.generated_image_url, payload.preview_url];
  return firstText(candidates);
}

function openDetails(record: GenerationRecord) {
  selectedGeneration.value = record;
  detailsOpen.value = true;
}

function normalizePayload(payload: Record<string, unknown> | null | undefined) {
  return payload && typeof payload === "object" ? payload : {};
}

function firstText(values: unknown[]) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function looksLikeJson(value: string) {
  const trimmed = value.trim();
  return (trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"));
}

function prettyJson(value: unknown) {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return "{}";
  }
}

function formatDateTime(value: string) {
  const localeCode = locale.value === "pt" ? "pt-PT" : locale.value === "es" ? "es-ES" : "en-US";
  return new Intl.DateTimeFormat(localeCode, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
</script>
