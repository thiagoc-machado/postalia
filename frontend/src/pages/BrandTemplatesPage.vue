<template>
  <div class="content-grid">
    <v-card class="section-card pa-6">
      <PageShell
        :eyebrow="t('pages.brands.templates.eyebrow')"
        :title="t('pages.brands.templates.title')"
        :subtitle="t('pages.brands.templates.subtitle')"
      />

      <v-select
        v-model="selectedBrandId"
        :items="brands"
        item-title="name"
        item-value="id"
        :label="t('pages.brands.templates.selectBrand')"
        class="mt-5"
      />

      <v-card class="soft-panel pa-5 mt-5" v-if="selectedBrand">
        <SectionHeading :title="t('pages.brands.templates.savedTemplates')" :subtitle="t('pages.brands.templates.savedTemplatesSubtitle')" />
        <v-list lines="two" class="bg-transparent">
          <v-list-item
            v-for="template in selectedBrand.templates"
            :key="template.id"
            :title="template.name"
            :subtitle="template.base_prompt"
          >
            <template #append>
              <v-chip size="small" variant="tonal">{{ template.visual_style || t("common.unset") }}</v-chip>
            </template>
          </v-list-item>
        </v-list>
      </v-card>
    </v-card>

    <v-card class="section-card pa-6 sticky-panel">
      <SectionHeading :title="t('pages.brands.templates.addTemplate')" :subtitle="t('pages.brands.templates.addTemplateSubtitle')" />
      <v-form class="form-group">
        <v-alert v-if="formError" type="error" variant="tonal" class="mb-4">
          {{ formError }}
        </v-alert>
        <v-text-field v-model="form.name" :label="`${t('forms.name')} *`" :error-messages="fieldErrors.name" required />
        <v-textarea
          v-model="form.base_prompt"
          :label="`${t('forms.basePrompt')} *`"
          :error-messages="fieldErrors.base_prompt"
          required
        />
        <v-textarea v-model="form.visual_style" :label="t('forms.visualStyle')" :error-messages="fieldErrors.visual_style" />
        <v-textarea
          v-model="form.copywriting_style"
          :label="t('forms.copywritingStyle')"
          :error-messages="fieldErrors.copywriting_style"
        />
        <v-textarea
          v-model="form.forbidden_topics"
          :label="t('forms.forbiddenTopics')"
          :error-messages="fieldErrors.forbidden_topics"
        />
        <v-text-field v-model="form.preferred_cta" :label="t('forms.preferredCta')" :error-messages="fieldErrors.preferred_cta" />
        <v-btn color="primary" class="mt-2" @click="submit">{{ t("actions.save") }}</v-btn>
      </v-form>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute } from "vue-router";
import client from "../api/client";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";
import { extractApiErrorMessage, extractApiFieldErrors } from "../utils/apiErrors";

const route = useRoute();
const { t } = useI18n();
const brands = ref<any[]>([]);
const selectedBrandId = ref<number | null>(Number(route.params.id));
const form = ref({ name: "", base_prompt: "", visual_style: "", copywriting_style: "", forbidden_topics: "", preferred_cta: "" });
const formError = ref("");
const fieldErrors = ref<Record<string, string[]>>({});

onMounted(async () => {
  const { data } = await client.get("/brands/");
  brands.value = data;
  if (!selectedBrandId.value && data[0]) selectedBrandId.value = data[0].id;
});

const selectedBrand = computed(() => brands.value.find((item) => item.id === selectedBrandId.value));

async function submit() {
  if (!selectedBrandId.value) return;
  formError.value = "";
  fieldErrors.value = {};
  try {
    await client.post(`/brands/${selectedBrandId.value}/templates/`, form.value);
    const { data } = await client.get("/brands/");
    brands.value = data;
  } catch (error) {
    fieldErrors.value = extractApiFieldErrors(error);
    formError.value = extractApiErrorMessage(error, t("errors.template"));
  }
}
</script>
