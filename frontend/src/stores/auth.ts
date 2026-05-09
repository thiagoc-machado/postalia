import { defineStore } from "pinia";
import client from "../api/client";
import { clearSession, setAccessToken, getAccessToken } from "./session";

type User = {
  id: number;
  email: string;
  name: string;
  is_staff: boolean;
  referral_code: string;
  auth_provider: string;
};

type AuthConfig = {
  google_only: boolean;
  local_auth_enabled: boolean;
  registration_enabled: boolean;
  supported_languages: string[];
  default_language: string;
};

type BillingSnapshot = {
  plan_code: string;
  status: string;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  payment_provider: string;
};

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as User | null,
    config: null as AuthConfig | null,
    billing: null as BillingSnapshot | null,
    initialized: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    isFreePlan: (state) => {
      if (!state.user) return true;
      if (!state.billing) return false;
      return state.billing.plan_code === "free";
    },
    isPaidPlan: (state) => Boolean(state.billing && state.billing.plan_code !== "free"),
  },
  actions: {
    async initialize() {
      if (this.initialized) return;
      await this.loadConfig();
      const token = getAccessToken();
      if (token) {
        try {
          const { data } = await client.get("/auth/me/");
          this.user = data;
          await this.loadBilling();
        } catch {
          clearSession();
        }
      }
      this.initialized = true;
    },
    async loadConfig() {
      const { data } = await client.get("/auth/config/");
      this.config = data;
    },
    async loadBilling() {
      if (!this.user) {
        this.billing = null;
        return;
      }
      try {
        const { data } = await client.get("/billing/subscription/");
        this.billing = data;
      } catch {
        this.billing = null;
      }
    },
    async login(payload: { email: string; password: string }) {
      const { data } = await client.post("/auth/login/", payload);
      setAccessToken(data.access);
      this.user = data.user;
      await this.loadBilling();
    },
    async register(payload: { email: string; password: string; name: string; referral_code?: string }) {
      const { data } = await client.post("/auth/register/", payload);
      setAccessToken(data.access);
      this.user = data.user;
      await this.loadBilling();
    },
    async googleLogin(credential: string) {
      const { data } = await client.post("/auth/google/", { credential });
      setAccessToken(data.access);
      this.user = data.user;
      await this.loadBilling();
    },
    async logout() {
      try {
        await client.post("/auth/logout/");
      } finally {
        clearSession();
        this.user = null;
        this.billing = null;
      }
    },
  },
});
