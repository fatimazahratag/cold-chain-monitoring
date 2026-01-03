from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Dht11

@api_view(['GET'])
def latest_measure(request):
    """
    Renvoie la dernière mesure du DHT11
    """
    last = Dht11.objects.order_by('-id').first()
    if last:
        data = {
            'temp': last.temp,
            'humidity': last.humidity,
            'dt': last.dt.isoformat()
        }
    else:
        data = {'temp': 0, 'humidity': 0, 'dt': None}
    return Response(data)
