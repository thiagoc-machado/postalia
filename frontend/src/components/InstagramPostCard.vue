<template>
  <v-card class="instagram-post-card overflow-hidden">
    <div class="instagram-post-card__header">
      <div class="d-flex align-center ga-3">
        <v-avatar size="40" color="primary" variant="tonal">
          <span class="font-weight-black">{{ brandInitial }}</span>
        </v-avatar>
        <div>
          <div class="text-subtitle-2 font-weight-bold">{{ brandName }}</div>
          <div class="soft-text text-caption">{{ brandMeta }}</div>
        </div>
      </div>
      <div class="d-flex align-center ga-2">
        <v-chip size="small" variant="tonal" color="primary">{{ statusLabel }}</v-chip>
      </div>
    </div>

    <div v-if="imageUrl" class="instagram-post-card__media">
      <v-img
        :src="imageUrl"
        cover
        height="100%"
        class="instagram-post-card__image"
      />
      <div class="instagram-post-card__badge-row">
        <v-chip size="small" variant="tonal" color="primary">{{ generationLabel }}</v-chip>
        <v-chip size="small" variant="tonal">{{ outputFormatLabel }}</v-chip>
      </div>
    </div>

    <div v-else class="instagram-post-card__badge-row instagram-post-card__badge-row--inline">
      <v-chip size="small" variant="tonal" color="primary">{{ generationLabel }}</v-chip>
      <v-chip size="small" variant="tonal">{{ outputFormatLabel }}</v-chip>
    </div>

    <div class="instagram-post-card__actions">
      <div class="d-flex align-center ga-4 instagram-post-card__icons">
        <v-icon size="20" icon="mdi-heart-outline" />
        <v-icon size="20" icon="mdi-comment-outline" />
        <v-icon size="20" icon="mdi-send-outline" />
      </div>
      <v-chip size="small" variant="outlined">{{ pointsSpentLabel }}</v-chip>
    </div>

    <div class="instagram-post-card__body" :class="{ 'instagram-post-card__body--no-media': !imageUrl }">
      <div class="text-caption text-uppercase font-weight-bold mb-1">{{ captionLabel }}</div>
      <div class="instagram-post-card__caption">{{ captionText }}</div>

      <div v-if="hashtagsText" class="instagram-post-card__hashtags">{{ hashtagsText }}</div>

      <div v-if="slidesText" class="instagram-post-card__slides">
        <div class="text-caption text-uppercase font-weight-bold mb-1">{{ slidesLabel }}</div>
        <ul class="instagram-post-card__slide-list">
          <li v-for="(slide, index) in slidesText" :key="`${index}-${slide}`">{{ slide }}</li>
        </ul>
      </div>

      <div v-if="designNotes" class="instagram-post-card__notes">
        <div class="text-caption text-uppercase font-weight-bold mb-1">{{ designNotesLabel }}</div>
        <div class="soft-text">{{ designNotes }}</div>
      </div>
    </div>

    <div class="instagram-post-card__footer">
      <div class="soft-text text-caption">{{ createdAtLabel }}</div>
      <v-btn variant="text" size="small" @click="$emit('details')">{{ detailsLabel }}</v-btn>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  brandName: string;
  brandMeta?: string;
  generationLabel: string;
  statusLabel: string;
  outputFormatLabel: string;
  pointsSpentLabel: string;
  captionLabel: string;
  captionText: string;
  hashtagsText?: string;
  slidesText?: string[];
  designNotes?: string;
  imageUrl?: string;
  emptyTitle: string;
  emptyCopy: string;
  slidesLabel: string;
  designNotesLabel: string;
  detailsLabel: string;
  createdAtLabel: string;
}>();

defineEmits<{
  (event: "details"): void;
}>();

const brandInitial = computed(() => (props.brandName?.trim()?.[0] || "P").toUpperCase());
</script>

<style scoped>
.instagram-post-card {
  width: min(100%, 640px);
  margin-inline: auto;
  border-radius: 28px;
  border: 1px solid rgba(var(--v-border-color), 0.12);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(251, 249, 245, 0.98)),
    radial-gradient(circle at top right, rgba(249, 115, 22, 0.08), transparent 30%);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
}

.instagram-post-card__header,
.instagram-post-card__actions,
.instagram-post-card__footer {
  padding-inline: 1.25rem;
}

.instagram-post-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 1.1rem;
  padding-bottom: 1rem;
}

.instagram-post-card__media {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.72));
  aspect-ratio: 1 / 1;
  max-height: 420px;
}

.instagram-post-card__image {
  min-height: 100%;
}

.instagram-post-card__badge-row {
  position: absolute;
  left: 1rem;
  right: 1rem;
  top: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: space-between;
  pointer-events: none;
}

.instagram-post-card__badge-row--inline {
  position: static;
  left: auto;
  right: auto;
  top: auto;
  padding: 1rem 1.25rem 0;
}

.instagram-post-card__badge-row :deep(.v-chip) {
  pointer-events: auto;
  backdrop-filter: blur(18px);
}

.instagram-post-card__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 0.95rem;
  padding-bottom: 0.7rem;
}

.instagram-post-card__icons {
  color: rgb(var(--v-theme-on-surface));
  font-size: 1.05rem;
}

.instagram-post-card__body {
  display: grid;
  gap: 0.85rem;
  padding: 0 1.25rem 1rem;
}

.instagram-post-card__body--no-media {
  padding-top: 0.15rem;
}

.instagram-post-card__caption {
  white-space: pre-line;
  font-size: 0.96rem;
  line-height: 1.6;
  color: rgb(var(--v-theme-on-surface));
}

.instagram-post-card__hashtags {
  color: rgb(var(--v-theme-primary));
  font-weight: 700;
  line-height: 1.6;
  word-break: break-word;
}

.instagram-post-card__slides,
.instagram-post-card__notes {
  padding-top: 0.2rem;
}

.instagram-post-card__slide-list {
  margin: 0;
  padding-inline-start: 1.1rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.55;
}

.instagram-post-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 0.2rem;
  padding-bottom: 1.05rem;
}

@media (max-width: 600px) {
  .instagram-post-card__header,
  .instagram-post-card__actions,
  .instagram-post-card__footer {
    padding-inline: 1rem;
  }

  .instagram-post-card__body {
    padding-inline: 1rem;
  }

  .instagram-post-card__badge-row--inline {
    padding-inline: 1rem;
  }
}
</style>
