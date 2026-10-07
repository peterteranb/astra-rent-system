import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from .services import create_rental


@login_required
@require_POST
def create_rental_view(request):
    try:
        data = json.loads(request.body)
        equipment_id = data.get('equipment_id')
        start_datetime = parse_datetime(data.get('start_datetime', ''))
        end_datetime = parse_datetime(data.get('end_datetime', ''))

        if not all([equipment_id, start_datetime, end_datetime]):
            return JsonResponse({'error': 'Todos los campos son obligatorios.'}, status=400)

        rental = create_rental(
            client=request.user,
            equipment_id=equipment_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )

        return JsonResponse({
            'message': 'Renta confirmada exitosamente.',
            'rental': {
                'id': rental.id,
                'equipment': rental.equipment.name,
                'start_datetime': rental.start_datetime.isoformat(),
                'end_datetime': rental.end_datetime.isoformat(),
                'status': rental.status
            }
        }, status=201)

    except ValidationError as e:
        # Alternativa E1: Devuelve el mensaje de indisponibilidad
        return JsonResponse({'error': e.messages[0] if hasattr(e, 'messages') else str(e)}, status=400)
    except Exception:
        return JsonResponse({'error': 'Error inesperado al procesar la solicitud.'}, status=500)