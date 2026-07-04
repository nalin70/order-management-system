from apps.payments.models import PaymentTransaction


class PaymentRepository:
    @staticmethod
    def create_transaction(order, amount, status, transaction_reference):
        return PaymentTransaction.objects.create(
            order=order,
            amount=amount,
            status=status,
            transaction_reference=transaction_reference,
        )

    @staticmethod
    def get_transaction(transaction_id):
        return PaymentTransaction.objects.filter(id=transaction_id).first()

    @staticmethod
    def save_transaction(transaction):
        transaction.save()
        return transaction
