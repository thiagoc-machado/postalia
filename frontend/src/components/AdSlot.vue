<template>
  <div v-if="visible" :class="['ad-slot', `ad-slot--${placement}`, className]">
    <template v-if="isGoogleAdsense">
      <ins
        class="adsbygoogle"
        style="display:block"
        :data-ad-client="appConfig.googleAdSenseClientId"
        :data-ad-slot="slotId"
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </template>
    <template v-else>
      <div class="ad-slot__placeholder">
        <div class="ad-slot__label">{{ t("pages.ads.adSpace") }}</div>
        <div class="ad-slot__hint">{{ t("pages.ads.reservedFor", { placement }) }}</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { appConfig } from "../config";

const { t } = useI18n();
const props = defineProps<{
  placement: "header" | "sidebar" | "dashboard" | "footer" | "inline";
  className?: string;
  visible?: boolean;
}>();

const slotId = computed(() => {
  return (
    {
      header: appConfig.googleAdSenseSlots.header,
      sidebar: appConfig.googleAdSenseSlots.sidebar,
      dashboard: appConfig.googleAdSenseSlots.dashboard,
      footer: appConfig.googleAdSenseSlots.footer,
      inline: appConfig.googleAdSenseSlots.dashboard,
    }[props.placement] || ""
  );
});

const isGoogleAdsense = computed(() => appConfig.enablePageAds && appConfig.adsProvider === "google_adsense" && Boolean(appConfig.googleAdSenseClientId) && Boolean(slotId.value));
const visible = computed(() => props.visible !== false && appConfig.enablePageAds);

function loadAdScript() {
  if (!document.querySelector('script[src^="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"]')) {
    const script = document.createElement("script");
    script.async = true;
    script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${appConfig.googleAdSenseClientId}`;
    script.crossOrigin = "anonymous";
    document.head.appendChild(script);
  }
}

onMounted(() => {
  if (!isGoogleAdsense.value) return;
  loadAdScript();
  try {
    (window as any).adsbygoogle = (window as any).adsbygoogle || [];
    (window as any).adsbygoogle.push({});
  } catch {
    // Ignore ad blockers and script failures.
  }
});
</script>
