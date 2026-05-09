from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .models import CreditTransaction
from .serializers import CreditTransactionSerializer, CreditWalletSerializer


class MyWalletView(RetrieveAPIView):
    serializer_class = CreditWalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.wallet


class MyTransactionsView(ListAPIView):
    serializer_class = CreditTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CreditTransaction.objects.filter(wallet=self.request.user.wallet)
