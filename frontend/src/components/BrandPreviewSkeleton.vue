<template>
  <section class="brand-preview-skeleton" :class="{ 'brand-preview-skeleton--compact': isCompact }" :style="styleVars">
    <div class="brand-preview-skeleton__top">
      <div class="brand-preview-skeleton__brand">
        <div class="brand-preview-skeleton__mark">
          <img v-if="logoUrl" :src="logoUrl" :alt="brandName || t('pages.brands.preview.defaultTitle')" />
          <span v-else>{{ brandInitial }}</span>
        </div>
        <div>
          <div class="brand-preview-skeleton__eyebrow">{{ t("pages.brands.preview.eyebrow") }}</div>
          <div class="brand-preview-skeleton__title">{{ brandName || t("pages.brands.preview.defaultTitle") }}</div>
        </div>
      </div>
      <div class="brand-preview-skeleton__chips">
        <span class="brand-preview-skeleton__chip">{{ languageLabel }}</span>
        <span class="brand-preview-skeleton__chip brand-preview-skeleton__chip--accent">{{ niche || t("pages.brands.preview.nicheFallback") }}</span>
      </div>
    </div>

    <div class="brand-preview-skeleton__canvas">
      <div class="brand-preview-skeleton__hero">
        <div class="brand-preview-skeleton__hero-lines">
          <span class="brand-preview-skeleton__line brand-preview-skeleton__line--xl" />
          <span class="brand-preview-skeleton__line brand-preview-skeleton__line--lg" />
          <span v-if="!isCompact" class="brand-preview-skeleton__line brand-preview-skeleton__line--md" />
        </div>
        <div class="brand-preview-skeleton__meta">
          <div class="brand-preview-skeleton__meta-pill">{{ audienceLabel }}</div>
          <div class="brand-preview-skeleton__meta-pill">{{ toneLabel }}</div>
        </div>
        <div class="brand-preview-skeleton__bullets">
          <div class="brand-preview-skeleton__bullet" v-for="bullet in bullets" :key="bullet">
            <span class="brand-preview-skeleton__bullet-icon" />
            <span class="brand-preview-skeleton__bullet-line">
              <span class="brand-preview-skeleton__line brand-preview-skeleton__line--sm" />
            </span>
          </div>
        </div>
        <div class="brand-preview-skeleton__cta">
          <span class="brand-preview-skeleton__cta-text">{{ t("pages.brands.preview.cta") }}</span>
          <span class="brand-preview-skeleton__cta-arrow">→</span>
        </div>
      </div>

      <div class="brand-preview-skeleton__panel">
        <div class="brand-preview-skeleton__panel-header">
          <div>
            <div class="brand-preview-skeleton__panel-label">{{ t("pages.brands.preview.panelLabel") }}</div>
            <div class="brand-preview-skeleton__panel-title">{{ t("pages.brands.preview.panelTitle") }}</div>
          </div>
          <div class="brand-preview-skeleton__status">{{ t("pages.brands.preview.status") }}</div>
        </div>
        <div class="brand-preview-skeleton__panel-grid">
          <div
            v-for="card in cards"
            :key="card.label"
            class="brand-preview-skeleton__panel-card"
            :style="{ backgroundColor: card.color }"
          >
            <div class="brand-preview-skeleton__panel-card-title">{{ card.label }}</div>
            <div class="brand-preview-skeleton__panel-card-copy">{{ card.copy }}</div>
          </div>
        </div>
        <div class="brand-preview-skeleton__panel-foot">
          <div class="brand-preview-skeleton__panel-bar" />
          <div class="brand-preview-skeleton__panel-bar brand-preview-skeleton__panel-bar--wide" />
          <div class="brand-preview-skeleton__panel-bar" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  compact?: boolean;
  brandName?: string;
  niche?: string;
  audience?: string;
  tone?: string;
  language?: string;
  primaryColor?: string;
  secondaryColor?: string;
  logoUrl?: string;
}>();

const { t } = useI18n();
const isCompact = computed(() => props.compact ?? false);

const safePrimary = computed(() => normalizeColor(props.primaryColor, "#f8be27"));
const safeSecondary = computed(() => normalizeColor(props.secondaryColor, "#ff7722"));
const brandInitial = computed(() => (props.brandName?.trim()?.slice(0, 1) || "P").toUpperCase());
const languageLabel = computed(() => {
  const language = (props.language || "en") as "en" | "es" | "pt";
  return t(`languages.${language}`) || language.toUpperCase();
});
const audienceLabel = computed(() => props.audience?.trim() || t("pages.brands.preview.audienceFallback"));
const toneLabel = computed(() => props.tone?.trim() || t("pages.brands.preview.toneFallback"));
const cards = computed(() => [
  {
    label: t("pages.brands.preview.card1Label"),
    copy: props.brandName?.trim() || t("pages.brands.preview.card1Copy"),
    color: safePrimary.value,
  },
  {
    label: t("pages.brands.preview.card2Label"),
    copy: props.niche?.trim() || t("pages.brands.preview.card2Copy"),
    color: safeSecondary.value,
  },
  ...(isCompact.value
    ? []
    : [
        {
          label: t("pages.brands.preview.card3Label"),
          copy: audienceLabel.value,
          color: mixColor(safePrimary.value, safeSecondary.value, 0.35),
        },
      ]),
]);
const bullets = computed(() => [
  t("pages.brands.preview.bullet1"),
  t("pages.brands.preview.bullet2"),
  ...(isCompact.value ? [] : [t("pages.brands.preview.bullet3")]),
]);
const styleVars = computed(() => ({
  "--preview-primary": safePrimary.value,
  "--preview-secondary": safeSecondary.value,
  "--preview-primary-soft": mixColor(safePrimary.value, "#ffffff", 0.78),
  "--preview-secondary-soft": mixColor(safeSecondary.value, "#ffffff", 0.8),
}));

function normalizeColor(value: string | undefined, fallback: string) {
  const candidate = (value || "").trim();
  return /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(candidate) ? candidate : fallback;
}

function hexToRgb(value: string) {
  const normalized = normalizeColor(value, "#f8be27").slice(1);
  const raw = normalized.length === 3 ? normalized.split("").map((part) => part + part).join("") : normalized;
  return [0, 2, 4].map((index) => Number.parseInt(raw.slice(index, index + 2), 16));
}

function mixColor(a: string, b: string, ratio: number) {
  const mix = Math.max(0, Math.min(1, ratio));
  const [ar, ag, ab] = hexToRgb(a);
  const [br, bg, bb] = hexToRgb(b);
  const channel = (x: number, y: number) => Math.round(x * (1 - mix) + y * mix);
  return `rgb(${channel(ar, br)}, ${channel(ag, bg)}, ${channel(ab, bb)})`;
}
</script>

<style scoped>
.brand-preview-skeleton {
  border-radius: 28px;
  padding: 1.25rem;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--preview-primary) 28%, transparent), transparent 38%),
    radial-gradient(circle at bottom right, color-mix(in srgb, var(--preview-secondary) 28%, transparent), transparent 34%),
    linear-gradient(160deg, #0b0c10 0%, #121721 100%);
  color: #fff;
  box-shadow: 0 22px 60px rgba(0, 0, 0, 0.22);
  overflow: hidden;
}

.brand-preview-skeleton--compact {
  max-width: 360px;
  margin: 0 auto;
  padding: 0.9rem;
}

.brand-preview-skeleton__top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__top {
  margin-bottom: 0.8rem;
  gap: 0.75rem;
}

.brand-preview-skeleton__brand {
  display: flex;
  align-items: center;
  gap: 0.9rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__brand {
  gap: 0.65rem;
}

.brand-preview-skeleton__mark {
  width: 3rem;
  height: 3rem;
  border-radius: 0.95rem;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, var(--preview-primary), var(--preview-secondary));
  color: #111;
  font-size: 1.3rem;
  font-weight: 900;
  overflow: hidden;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__mark {
  width: 2.6rem;
  height: 2.6rem;
  font-size: 1.05rem;
  border-radius: 0.8rem;
}

.brand-preview-skeleton__mark img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.brand-preview-skeleton__eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.64);
}

.brand-preview-skeleton__title {
  margin-top: 0.15rem;
  font-size: 1.2rem;
  font-weight: 800;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__title {
  font-size: 1rem;
}

.brand-preview-skeleton__chips {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.brand-preview-skeleton__chip {
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.78rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__chip {
  padding: 0.35rem 0.65rem;
  font-size: 0.72rem;
}

.brand-preview-skeleton__chip--accent {
  background: color-mix(in srgb, var(--preview-primary) 24%, rgba(255, 255, 255, 0.1));
  color: #fff;
}

.brand-preview-skeleton__canvas {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(260px, 0.92fr);
  gap: 0.85rem;
}

.brand-preview-skeleton__hero,
.brand-preview-skeleton__panel {
  border-radius: 24px;
  padding: 1.1rem;
  min-height: 17rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__hero,
.brand-preview-skeleton--compact .brand-preview-skeleton__panel {
  min-height: 13.5rem;
  padding: 0.9rem;
  border-radius: 20px;
}

.brand-preview-skeleton__hero {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02)),
    linear-gradient(160deg, color-mix(in srgb, var(--preview-primary) 14%, #0e1016), #08090d);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 1rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__hero {
  gap: 0.8rem;
}

.brand-preview-skeleton__hero-lines {
  display: grid;
  gap: 0.75rem;
  margin-top: 0.3rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__hero-lines {
  gap: 0.45rem;
}

.brand-preview-skeleton__line {
  display: block;
  height: 0.95rem;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.08));
}

.brand-preview-skeleton--compact .brand-preview-skeleton__line {
  height: 0.72rem;
}

.brand-preview-skeleton__line--xl {
  width: 88%;
  height: 1.45rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__line--xl {
  width: 82%;
  height: 1.05rem;
}

.brand-preview-skeleton__line--lg {
  width: 76%;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__line--lg {
  width: 66%;
}

.brand-preview-skeleton__line--md {
  width: 63%;
}

.brand-preview-skeleton__line--sm {
  width: 100%;
  height: 0.65rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__line--sm {
  height: 0.5rem;
}

.brand-preview-skeleton__meta {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.brand-preview-skeleton__meta-pill {
  padding: 0.55rem 0.8rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.84);
  font-size: 0.82rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__meta-pill {
  padding: 0.4rem 0.65rem;
  font-size: 0.72rem;
}

.brand-preview-skeleton__bullets {
  display: grid;
  gap: 0.7rem;
}

.brand-preview-skeleton__bullet {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__bullet {
  gap: 0.55rem;
}

.brand-preview-skeleton__bullet-icon {
  width: 1.8rem;
  height: 1.8rem;
  flex: 0 0 1.8rem;
  border-radius: 999px;
  background: linear-gradient(145deg, var(--preview-primary), var(--preview-secondary));
}

.brand-preview-skeleton--compact .brand-preview-skeleton__bullet-icon {
  width: 1.45rem;
  height: 1.45rem;
  flex-basis: 1.45rem;
}

.brand-preview-skeleton__bullet-line {
  flex: 1;
}

.brand-preview-skeleton__cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border-radius: 1.2rem;
  padding: 0.95rem 1.1rem;
  background: linear-gradient(135deg, var(--preview-primary), var(--preview-secondary));
  color: #111;
  font-weight: 800;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__cta {
  padding: 0.75rem 0.9rem;
  border-radius: 1rem;
}

.brand-preview-skeleton__panel {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(250, 250, 252, 0.94)),
    #fff;
  color: #1a1f29;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.brand-preview-skeleton__panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__panel-header {
  gap: 0.75rem;
}

.brand-preview-skeleton__panel-label {
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(25, 30, 40, 0.58);
}

.brand-preview-skeleton__panel-title {
  margin-top: 0.2rem;
  font-size: 1.15rem;
  font-weight: 800;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__panel-title {
  font-size: 1rem;
}

.brand-preview-skeleton__status {
  padding: 0.42rem 0.72rem;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.08);
  color: rgba(17, 24, 39, 0.78);
  font-size: 0.74rem;
  white-space: nowrap;
}

.brand-preview-skeleton__panel-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.7rem;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__panel-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.brand-preview-skeleton__panel-card {
  min-height: 7rem;
  border-radius: 1rem;
  padding: 0.9rem;
  color: #111827;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__panel-card {
  min-height: 5.5rem;
  padding: 0.75rem;
  border-radius: 0.9rem;
}

.brand-preview-skeleton__panel-card-title {
  font-size: 0.85rem;
  font-weight: 800;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__panel-card-title {
  font-size: 0.75rem;
}

.brand-preview-skeleton__panel-card-copy {
  margin-top: 0.35rem;
  font-size: 0.78rem;
  opacity: 0.9;
}

.brand-preview-skeleton--compact .brand-preview-skeleton__panel-card-copy {
  font-size: 0.68rem;
}

.brand-preview-skeleton__panel-foot {
  margin-top: auto;
  display: grid;
  gap: 0.55rem;
}

.brand-preview-skeleton__panel-bar {
  height: 0.72rem;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.1);
}

.brand-preview-skeleton--compact .brand-preview-skeleton__panel-bar {
  height: 0.55rem;
}

.brand-preview-skeleton__panel-bar--wide {
  width: 88%;
}

@media (max-width: 1024px) {
  .brand-preview-skeleton__canvas {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .brand-preview-skeleton {
    padding: 1rem;
  }

  .brand-preview-skeleton--compact .brand-preview-skeleton__canvas {
    grid-template-columns: 1fr;
  }

  .brand-preview-skeleton__panel-grid {
    grid-template-columns: 1fr;
  }

  .brand-preview-skeleton__cta {
    align-items: flex-start;
  }
}
</style>
