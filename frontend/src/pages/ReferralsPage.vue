<template>
  <div class="content-grid">
    <v-card class="section-card pa-6">
      <PageShell
        :eyebrow="t('pages.referrals.eyebrow')"
        :title="t('pages.referrals.title')"
        :subtitle="t('pages.referrals.subtitle')"
      />

      <div class="field-grid mt-5">
        <v-text-field :model-value="code" :label="t('pages.referrals.yourCode')" readonly />
        <v-btn color="primary" variant="outlined" class="align-self-center" @click="copyCode">{{ t('actions.copyCode') }}</v-btn>
      </div>

      <v-text-field v-model="applyCode" :label="t('pages.referrals.applyCode')" class="mt-4" />
      <v-btn color="primary" class="mt-2" @click="apply">{{ t('actions.apply') }}</v-btn>
    </v-card>

    <v-card class="section-card pa-6 sticky-panel">
      <SectionHeading :title="t('pages.referrals.sentReferrals')" :subtitle="t('pages.referrals.sentReferralsSubtitle')" />
      <v-list lines="two" class="bg-transparent">
        <v-list-item v-for="item in sent" :key="item.id" :title="item.referred_user_email" :subtitle="statusLabel(item.status)" />
      </v-list>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import client from "../api/client";
import PageShell from "../components/PageShell.vue";
import SectionHeading from "../components/SectionHeading.vue";

const code = ref("");
const sent = ref<any[]>([]);
const applyCode = ref("");
const { t } = useI18n();

onMounted(async () => {
  const { data } = await client.get("/referrals/me/");
  code.value = data.referral_code;
  sent.value = data.sent;
});

async function apply() {
  await client.post("/referrals/apply/", { referral_code: applyCode.value });
  applyCode.value = "";
}

async function copyCode() {
  if (code.value) await navigator.clipboard.writeText(code.value);
}

function statusLabel(status: string) {
  return t(`statuses.${status}`) || status;
}
</script>
