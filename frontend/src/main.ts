import { createApp } from "vue";
import { createPinia } from "pinia";
import { createI18n } from "vue-i18n";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/700.css";
import "vuetify/styles";
import { createVuetify } from "vuetify";
import { md3 } from "vuetify/blueprints";

import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";
import en from "./locales/en.json";
import es from "./locales/es.json";
import pt from "./locales/pt.json";
import "./styles.css";

const app = createApp(App);
const pinia = createPinia();

const i18n = createI18n({
  legacy: false,
  locale:
    localStorage.getItem("postalia_locale") ||
    (navigator.language.startsWith("es") ? "es" : navigator.language.startsWith("pt") ? "pt" : "en"),
  fallbackLocale: "en",
  messages: { en, es, pt },
});

const vuetify = createVuetify({
  blueprint: md3,
  defaults: {
    VBtn: {
      rounded: "lg",
      variant: "flat",
      style: "text-transform: none;",
    },
    VCard: {
      rounded: "xl",
      elevation: 0,
    },
    VTextField: {
      variant: "outlined",
      density: "comfortable",
      hideDetails: "auto",
    },
    VTextarea: {
      variant: "outlined",
      density: "comfortable",
      hideDetails: "auto",
    },
    VSelect: {
      variant: "outlined",
      density: "comfortable",
      hideDetails: "auto",
    },
  },
  theme: {
    defaultTheme: "postalia",
    themes: {
      postalia: {
        dark: false,
        colors: {
          background: "#f5f7fb",
          surface: "#ffffff",
          primary: "#0f766e",
          secondary: "#ef7b45",
          accent: "#2563eb",
          success: "#15803d",
          info: "#0369a1",
          warning: "#c2410c",
          error: "#b42318",
          "on-background": "#0f172a",
          "on-surface": "#0f172a",
        },
      },
    },
  },
});

app.use(pinia);
app.use(i18n);
app.use(vuetify);
app.use(router);

const auth = useAuthStore(pinia);
auth.initialize().finally(() => app.mount("#app"));
