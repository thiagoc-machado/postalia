from rest_framework.throttling import ScopedRateThrottle


class AuthThrottle(ScopedRateThrottle):
    scope = "auth"


class GenerationThrottle(ScopedRateThrottle):
    scope = "generation"


class ReferralThrottle(ScopedRateThrottle):
    scope = "referral"


class AdsThrottle(ScopedRateThrottle):
    scope = "ads"


class BillingThrottle(ScopedRateThrottle):
    scope = "billing"
