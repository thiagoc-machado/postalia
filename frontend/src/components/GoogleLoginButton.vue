<template>
  <div ref="container" />
  <v-alert v-if="error" type="warning" variant="tonal" class="mt-3">{{ error }}</v-alert>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  clientId?: string;
  onCredential: (credential: string) => Promise<void> | void;
}>();

const container = ref<HTMLElement | null>(null);
const error = ref("");
const { t } = useI18n();

function loadScript() {
  return new Promise<void>((resolve, reject) => {
    if ((window as any).google?.accounts?.id) return resolve();
    const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("google_script_failed")), {
        once: true,
      });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("google_script_failed"));
    document.head.appendChild(script);
  });
}

onMounted(async () => {
  if (!props.clientId) {
    error.value = t("pages.login.googleNotConfigured");
    return;
  }
  try {
    await loadScript();
    const google = (window as any).google;
    google.accounts.id.initialize({
      client_id: props.clientId,
      callback: async (response: { credential: string }) => props.onCredential(response.credential),
    });
    if (container.value) {
      google.accounts.id.renderButton(container.value, {
        theme: "outline",
        size: "large",
        shape: "pill",
        text: "continue_with",
        width: 320,
      });
    }
  } catch (err) {
    error.value = err instanceof Error && err.message === "google_script_failed"
      ? t("pages.login.googleScriptFailed")
      : t("pages.login.googleUnavailable");
  }
});
</script>
