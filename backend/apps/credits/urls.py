from django.urls import path

from .views import MyTransactionsView, MyWalletView

urlpatterns = [
    path("wallet/me/", MyWalletView.as_view(), name="my-wallet"),
    path("wallet/transactions/", MyTransactionsView.as_view(), name="my-transactions"),
]
