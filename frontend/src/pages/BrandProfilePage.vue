<template>
  <div class="content-grid">
    <v-card class="section-card pa-6">
      <PageShell
        :eyebrow="t('pages.brands.profile.eyebrow')"
        :title="t('pages.brands.profile.title')"
        :subtitle="t('pages.brands.profile.subtitle')"
      >
        <template #actions>
          <v-btn color="primary" to="/brands/wizard">{{ t("actions.newBrand") }}</v-btn>
        </template>
      </PageShell>

      <v-alert v-if="!brands.length" type="info" variant="tonal" class="mt-5">
        {{ t("pages.brands.profile.emptyState") }}
      </v-alert>

      <div v-else class="mt-5">
        <SectionHeading
          :title="t('pages.brands.profile.brandListTitle')"
          :subtitle="t('pages.brands.profile.brandListSubtitle')"
        />
        <div class="brand-grid mt-4">
          <button
            v-for="brand in brands"
            :key="brand.id"
            type="button"
            class="brand-card"
            :class="{ 'brand-card--active': brand.id === selectedBrandId }"
            @click="selectedBrandId = brand.id"
          >
            <div class="d-flex align-center justify-space-between ga-3">
              <div class="d-flex align-center ga-3">
                <div class="brand-card__logo">
                  <img v-if="resolveMediaUrl(brand.logo)" :src="resolveMediaUrl(brand.logo)" :alt="brand.name" />
                  <span v-else>{{ brand.name.slice(0, 1).toUpperCase() }}</span>
                </div>
                <div>
                  <div class="brand-card__title">{{ brand.name }}</div>
                  <div class="brand-card__subtitle">{{ brand.niche || t('pages.brands.profile.noNiche') }}</div>
                </div>
              </div>
              <div class="brand-card__swatches">
                <span class="brand-card__swatch" :style="{ backgroundColor: brand.primary_color || '#f8be27' }" />
                <span class="brand-card__swatch" :style="{ backgroundColor: brand.secondary_color || '#ff7722' }" />
              </div>
            </div>
            <div class="d-flex flex-wrap ga-2 mt-3">
              <v-chip size="small" variant="tonal" color="primary">{{ languageLabel(brand.language || 'en') }}</v-chip>
              <v-chip size="small" variant="tonal" color="secondary">{{ brand.is_default ? t('pages.brands.profile.default') : t('pages.brands.profile.secondary') }}</v-chip>
            </div>
            <div class="d-flex justify-space-between align-center mt-3">
              <span class="soft-text text-caption">{{ brand.instagram_handle || t('common.unset') }}</span>
              <v-btn size="small" variant="text" @click.stop="openEditor(brand.id)">
                {{ t('actions.edit') }}
              </v-btn>
            </div>
          </button>
        </div>
      </div>

      <v-select
        v-model="selectedBrandId"
        :items="brandOptions"
        item-title="name"
        item-value="id"
        :label="t('pages.brands.profile.selectBrand')"
        class="mt-5"
        :disabled="!brands.length"
      />

      <v-card v-if="selectedBrand" class="soft-panel pa-5 mt-5">
        <div class="d-flex flex-wrap align-center justify-space-between ga-3">
          <div class="d-flex align-center ga-3">
            <div class="brand-detail__logo">
              <img v-if="resolveMediaUrl(selectedBrand.logo)" :src="resolveMediaUrl(selectedBrand.logo)" :alt="selectedBrand.name" />
              <span v-else>{{ selectedBrand.name.slice(0, 1).toUpperCase() }}</span>
            </div>
            <div>
              <div class="text-h5 font-weight-black">{{ selectedBrand.name }}</div>
              <div class="soft-text">{{ selectedBrand.niche || t('pages.brands.profile.noNiche') }}</div>
            </div>
          </div>
          <div class="d-flex flex-wrap ga-2">
            <v-chip variant="tonal" color="primary">{{ languageLabel(selectedBrand.language || 'en') }}</v-chip>
            <v-chip variant="tonal" color="secondary">{{ selectedBrand.is_default ? t('pages.brands.profile.default') : t('pages.brands.profile.secondary') }}</v-chip>
            <v-btn color="primary" variant="outlined" @click="openEditor(selectedBrand.id)">
              {{ t('pages.brands.profile.editBrand') }}
            </v-btn>
          </div>
        </div>

        <div class="field-grid mt-4">
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.brands.profile.targetAudience') }}</div>
            <div class="soft-text">{{ selectedBrand.target_audience || t('pages.brands.profile.notProvided') }}</div>
          </div>
          <div class="muted-box pa-4">
            <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.brands.profile.productsServices') }}</div>
            <div class="soft-text">{{ selectedBrand.products_services || t('pages.brands.profile.notProvided') }}</div>
          </div>
        </div>

        <div class="muted-box pa-4 mt-4">
          <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.brands.profile.description') }}</div>
          <div class="soft-text">{{ selectedBrand.description || t('pages.brands.profile.noDescription') }}</div>
        </div>

        <div class="muted-box pa-4 mt-4" v-if="websiteContext">
          <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-3">
            <div>
              <div class="text-caption text-uppercase font-weight-bold mb-1">{{ t('pages.brands.profile.websiteContextTitle') }}</div>
              <div class="soft-text">{{ t('pages.brands.profile.websiteContextSubtitle') }}</div>
            </div>
            <v-chip size="small" variant="tonal" :color="websiteContext.status === 'captured' ? 'primary' : 'warning'">
              {{ websiteContext.status === 'captured' ? t('pages.brands.profile.websiteContextCaptured') : t('pages.brands.profile.websiteContextUnavailable') }}
            </v-chip>
          </div>
          <div class="stack">
            <div class="soft-text">
              <strong>{{ t('pages.brands.profile.websiteContextSource') }}:</strong>
              {{ websiteContext.source_url || selectedBrand.website || t('common.unset') }}
            </div>
            <div class="soft-text" v-if="websiteContext.title">
              <strong>{{ t('pages.brands.profile.websiteContextSiteTitle') }}:</strong>
              {{ websiteContext.title }}
            </div>
            <div class="soft-text" v-if="websiteContext.description">
              <strong>{{ t('pages.brands.profile.websiteContextDescription') }}:</strong>
              {{ websiteContext.description }}
            </div>
            <div class="soft-text" v-if="websiteContext.text_excerpt">
              <strong>{{ t('pages.brands.profile.websiteContextExcerpt') }}:</strong>
              {{ websiteContext.text_excerpt }}
            </div>
            <div class="d-flex flex-wrap ga-2" v-if="websiteColors.length">
              <v-chip v-for="color in websiteColors" :key="color" size="small" variant="tonal">
                {{ color }}
              </v-chip>
            </div>
          </div>
        </div>
      </v-card>
    </v-card>

    <v-card class="section-card pa-5 sticky-panel">
      <SectionHeading :title="t('pages.brands.profile.quickFacts')" :subtitle="t('pages.brands.profile.quickFactsSubtitle')" />
      <div class="feature-list">
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t('pages.brands.profile.website') }}: {{ selectedBrand?.website || t('common.unset') }}</span>
        </div>
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t('pages.brands.profile.instagram') }}: {{ selectedBrand?.instagram_handle || t('common.unset') }}</span>
        </div>
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t('pages.brands.profile.primaryColor') }}: {{ selectedBrand?.primary_color || t('common.unset') }}</span>
        </div>
        <div class="feature-item">
          <span class="feature-item__dot" />
          <span class="feature-item__text">{{ t('pages.brands.profile.secondaryColor') }}: {{ selectedBrand?.secondary_color || t('common.unset') }}</span>
        </div>
      </div>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import client from "../api/client";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";
import { resolveMediaUrl } from "../utils/media";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const brands = ref<any[]>([]);
const selectedBrandId = ref<number | null>(Number(route.params.id));

onMounted(async () => {
  const { data } = await client.get("/brands/");
  brands.value = data;
  if (!selectedBrandId.value && brands.value[0]) selectedBrandId.value = brands.value[0].id;
});

watch(
  () => route.params.id,
  (next) => {
    const parsed = Number(next);
    if (Number.isFinite(parsed)) {
      selectedBrandId.value = parsed;
    }
  },
);

const brandOptions = computed(() => brands.value);
const selectedBrand = computed(() => brands.value.find((item) => item.id === selectedBrandId.value));
const websiteContext = computed(() => selectedBrand.value?.website_context || null);
const websiteColors = computed(() => {
  const colors = websiteContext.value?.colors;
  return Array.isArray(colors) ? colors.filter((value) => typeof value === "string" && value.trim()).slice(0, 6) : [];
});

function languageLabel(language: string) {
  return t(`languages.${language}`) || language;
}

function openEditor(id: number) {
  router.push(`/brands/${id}/edit`);
}
</script>

<style scoped>
.brand-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.9rem;
}

.brand-card {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 1.1rem;
  padding: 1rem;
  text-align: left;
  background: rgba(255, 255, 255, 0.72);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.brand-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
}

.brand-card--active {
  border-color: rgba(37, 99, 235, 0.3);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.14);
}

.brand-card__title {
  font-weight: 800;
  font-size: 1rem;
}

.brand-card__subtitle {
  margin-top: 0.18rem;
  color: rgba(71, 85, 105, 0.92);
  font-size: 0.84rem;
}

.brand-card__swatches {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.brand-card__swatch {
  width: 1rem;
  height: 1rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.12);
}

.brand-card__logo,
.brand-detail__logo {
  width: 2.65rem;
  height: 2.65rem;
  border-radius: 0.9rem;
  overflow: hidden;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(15, 23, 42, 0.08);
  color: rgba(15, 23, 42, 0.78);
  font-weight: 800;
}

.brand-card__logo img,
.brand-detail__logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.brand-detail__logo {
  width: 3rem;
  height: 3rem;
}
</style>
