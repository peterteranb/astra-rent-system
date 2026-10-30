"""API del operador para CU-11: las deudas pendientes y el registro de su pago en la tienda."""
from django.shortcuts import get_object_or_404

from accounts.roles import OPERATOR

from ..models import Debt
from ..services.formatting import debt_paid_message
from ..use_cases.debts import debts_overview, pay_debt
from .responses import api_view, success
from .serializers import client_total_data, debt_data


@api_view("GET", roles=[OPERATOR])
def staff_debts(request):
    """Devuelve cada deuda sin pagar y el total que debe cada cliente."""
    overview = debts_overview()
    return success(
        {
            "debts": [debt_data(debt) for debt in overview.debts],
            "totals": [client_total_data(row) for row in overview.totals],
        }
    )


@api_view("POST", roles=[OPERATOR])
def pay_debt_view(request, debt_id):
    """Registra que el cliente pagó una deuda en la tienda (CU-11)."""
    debt = get_object_or_404(Debt.objects.select_related("rental__client"), pk=debt_id)
    paid = pay_debt(debt, request.user)
    return success(debt_data(paid), debt_paid_message(paid))
