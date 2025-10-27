from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import TripInputSerializer
from .utils import geocode, call_osrm_route, get_stops, ELDCalculator


class TripRouteView(APIView):
    def post(self, request):
        serializer = TripInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            cur_lat, cur_lon = geocode(data["current_location"])
            pickup_lat, pickup_lon = geocode(data["pickup_location"])
            dropoff_lat, dropoff_lon = geocode(data["dropoff_location"])
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            route_resp = call_osrm_route(
                coords=f"{cur_lon},{cur_lat};{pickup_lon},{pickup_lat};{dropoff_lon},{dropoff_lat}"
            )
            route_from_curr_to_pickup_location_resp = call_osrm_route(
                coords=f"{cur_lon},{cur_lat};{pickup_lon},{pickup_lat}"
            )

            route = route_resp.get("routes", [])[0]
            route_from_curr_to_pickup_location = (
                route_from_curr_to_pickup_location_resp.get("routes", [])[0]
            )

            eld_logs_calculator = ELDCalculator(
                route=route,
                route_from_curr_to_pickup_location=route_from_curr_to_pickup_location,
                curr_cycle_used_hours=data.get("current_cycle_hours", 0),
            )

            stops = get_stops(
                route=route,
                cur_coords=[cur_lat, cur_lon],
                pickup_coords=[pickup_lat, pickup_lon],
                dropoff_coords=[dropoff_lat, dropoff_lon],
            )

            logs = eld_logs_calculator.get_eld_logs()

            return Response(
                {
                    "route": route,
                    "stops": stops,
                    "logs": logs,
                },
                status=200,
            )
        except Exception as e:
            return Response(
                {"detail": f"Routing error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})
