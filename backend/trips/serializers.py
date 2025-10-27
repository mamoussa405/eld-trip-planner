from rest_framework import serializers


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField()
    pickup_location = serializers.CharField()
    dropoff_location = serializers.CharField()
    current_cycle_hours = serializers.FloatField()


class RouteResponseSerializer(serializers.Serializer):
    route = serializers.DictField()
    stops = serializers.ListField()
    eld_logs = serializers.ListField()
