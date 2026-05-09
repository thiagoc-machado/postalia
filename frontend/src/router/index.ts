import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

import LandingPage from "../pages/LandingPage.vue";
import PricingPage from "../pages/PricingPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import RegisterPage from "../pages/RegisterPage.vue";
import TermsPage from "../pages/TermsPage.vue";
import PrivacyPage from "../pages/PrivacyPage.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import BrandWizardPage from "../pages/BrandWizardPage.vue";
import BrandProfilePage from "../pages/BrandProfilePage.vue";
import BrandTemplatesPage from "../pages/BrandTemplatesPage.vue";
import GeneratePage from "../pages/GeneratePage.vue";
import HistoryPage from "../pages/HistoryPage.vue";
import WalletPage from "../pages/WalletPage.vue";
import ReferralsPage from "../pages/ReferralsPage.vue";
import SubscriptionPage from "../pages/SubscriptionPage.vue";
import SettingsPage from "../pages/SettingsPage.vue";
import StaffPage from "../pages/StaffPage.vue";
import BillingSuccessPage from "../pages/BillingSuccessPage.vue";
import BillingCancelPage from "../pages/BillingCancelPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: LandingPage },
    { path: "/pricing", component: PricingPage },
    { path: "/login", component: LoginPage },
    { path: "/register", component: RegisterPage },
    { path: "/terms", component: TermsPage },
    { path: "/privacy", component: PrivacyPage },
    { path: "/dashboard", component: DashboardPage, meta: { auth: true } },
    { path: "/brands", component: BrandProfilePage, meta: { auth: true } },
    { path: "/brands/wizard", component: BrandWizardPage, meta: { auth: true } },
    { path: "/brands/:id/edit", component: BrandWizardPage, meta: { auth: true } },
    { path: "/brands/:id", component: BrandProfilePage, meta: { auth: true } },
    { path: "/brands/:id/templates", component: BrandTemplatesPage, meta: { auth: true } },
    { path: "/generate", component: GeneratePage, meta: { auth: true } },
    { path: "/history", component: HistoryPage, meta: { auth: true } },
    { path: "/wallet", component: WalletPage, meta: { auth: true } },
    { path: "/referrals", component: ReferralsPage, meta: { auth: true } },
    { path: "/subscription", component: SubscriptionPage, meta: { auth: true } },
    { path: "/settings", component: SettingsPage, meta: { auth: true } },
    { path: "/staff", component: StaffPage, meta: { auth: true, staff: true } },
    { path: "/billing/success", component: BillingSuccessPage },
    { path: "/billing/cancel", component: BillingCancelPage },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.initialized) await auth.initialize();
  if (to.meta.auth && !auth.isAuthenticated) return "/login";
  if (to.meta.staff && !auth.user?.is_staff) return "/dashboard";
  if ((to.path === "/login" || to.path === "/register") && auth.isAuthenticated) return "/dashboard";
});

export default router;
