const env = import.meta.env;

export const appConfig = {
  enablePageAds: env.VITE_ENABLE_PAGE_ADS === "true",
  enableRewardedAds: env.VITE_ENABLE_REWARDED_ADS === "true",
  adsProvider: env.VITE_ADS_PROVIDER || "mock",
  googleAdSenseClientId: env.VITE_GOOGLE_ADSENSE_CLIENT_ID || "",
  googleAdSenseSlots: {
    header: env.VITE_GOOGLE_ADSENSE_SLOT_HEADER || "",
    sidebar: env.VITE_GOOGLE_ADSENSE_SLOT_SIDEBAR || "",
    dashboard: env.VITE_GOOGLE_ADSENSE_SLOT_DASHBOARD || "",
    footer: env.VITE_GOOGLE_ADSENSE_SLOT_FOOTER || "",
  },
  creemEnabled: env.VITE_CREEM_ENABLED === "true",
  rewardedAdsEnabled: env.VITE_ENABLE_REWARDED_ADS === "true",
  rewardedAdProvider: env.VITE_REWARDED_AD_PROVIDER || "mock",
  rewardedAdPoints: Number(env.VITE_REWARDED_AD_POINTS || 5),
  rewardedAdDailyLimit: Number(env.VITE_REWARDED_AD_DAILY_LIMIT || 2),
};
