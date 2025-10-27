import math
import requests
import polyline
from typing import Optional
from .enums import TimeLineChangeType
from .constants import (
    OSRM_ROUTE_URL,
    NOMINATIM_URL,
    EARTH_RADIUS_M,
    FUEL_INTERVAL_M,
    MAX_CYCLE_HOURS,
    MAX_CYCLE_DAYS,
    MAX_DRIVING_HOURS_PER_DAY,
    MAX_DRIVING_HOURS_TO_REST,
    BREAK_DURATION_H,
    PICKUP_DURATION_H,
    DROPOFF_DURATION_H,
    TRIP_TIV_DURATION_H,
    SECONDS_TO_HOURS,
    HOURS_IN_DAY,
    NUMBER_OF_HOURS_FROM_MIDNIGHT_TO_SIX,
    METERS_TO_MILES,
)


def geocode(address: str) -> tuple[float, float]:
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "eld-trip-planner/1.0 (+https://example.com)"}

    r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    if not data:
        raise ValueError(f"Address not found: {address}")

    return float(data[0]["lat"]), float(data[0]["lon"])


def call_osrm_route(coords: str) -> dict:
    url = OSRM_ROUTE_URL.format(coords=coords)

    r = requests.get(url, timeout=20)
    r.raise_for_status()

    return r.json()


def haversine(
    first_point_coords: list[float, float],
    second_point_coords: list[float, float],
) -> float:
    """
    Calculate the great-circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(
        math.radians, [*first_point_coords, *second_point_coords]
    )

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return c * EARTH_RADIUS_M


def _interpolate_along_step_geometry(
    geometry: str, target_m: float
) -> Optional[list[float]]:
    """Finds a point at a target distance along a single encoded polyline."""
    try:
        points = polyline.decode(geometry)
        if len(points) < 2:
            return None

        travelled_m = 0.0
        for i in range(1, len(points)):
            p1 = points[i - 1]
            p2 = points[i]
            segment_dist_m = haversine(p1, p2)

            if travelled_m + segment_dist_m >= target_m:
                dist_into_segment_m = target_m - travelled_m
                fraction = (
                    dist_into_segment_m / segment_dist_m
                    if segment_dist_m > 0
                    else 0
                )

                lat = p1[0] + fraction * (p2[0] - p1[0])
                lon = p1[1] + fraction * (p2[1] - p1[1])
                return [lat, lon]

            travelled_m += segment_dist_m
    except (ValueError, KeyError, ImportError):
        return None

    return None


def interpolate_point_along_legs(
    legs: list, target_m: float
) -> Optional[list[float]]:
    """
    Find a lat-lon at a target distance from the start by walking the legs' and steps' geometry.
    """
    travelled_m = 0.0
    for leg in legs:
        leg_dist_m = leg.get("distance", 0)

        if travelled_m + leg_dist_m >= target_m:
            # This leg contains our target point.
            distance_into_leg_m = target_m - travelled_m

            travelled_on_steps_m = 0.0
            for step in leg.get("steps", []):
                step_dist_m = step.get("distance", 0)

                if travelled_on_steps_m + step_dist_m >= distance_into_leg_m:
                    # This step contains our target point.
                    distance_into_step_m = (
                        distance_into_leg_m - travelled_on_steps_m
                    )
                    return _interpolate_along_step_geometry(
                        step.get("geometry"), distance_into_step_m
                    )

                travelled_on_steps_m += step_dist_m

        travelled_m += leg_dist_m

    return None


def get_stops(
    route: dict, cur_coords: list, pickup_coords: list, dropoff_coords: list
):
    route_distance_m = route.get("distance", 0)
    legs = route.get("legs", [])

    stops = [
        {
            "type": "current",
            "coords": cur_coords,
            "label": "Current location",
        },
        {
            "type": "pickup",
            "coords": pickup_coords,
            "label": "Pickup (1h)",
        },
    ]

    if route_distance_m <= FUEL_INTERVAL_M:
        return stops + [
            {
                "type": "dropoff",
                "coords": dropoff_coords,
                "label": "Dropoff (1h)",
            },
        ]

    # Create fuel stop suggestions:
    num_stops = math.floor(route_distance_m / FUEL_INTERVAL_M)

    # Place stops at fuel_interval_m, 2*fuel_interval_m, ... up to
    # before dropoff
    for i in range(1, num_stops + 1):
        target_distance_m = min(i * FUEL_INTERVAL_M, route_distance_m - 1)
        # attempt to interpolate position along legs:
        fuel_stop_position = interpolate_point_along_legs(
            legs, target_distance_m
        )

        stops.append(
            {
                "type": "fuel",
                "coords": fuel_stop_position,
                "label": f"Fuel stop #{i}",
            }
            if fuel_stop_position
            else {
                "type": "fuel",
                "progress": target_distance_m / route_distance_m,
                "label": f"Fuel stop #{i}",
            }  # TODO: check if this is the case
        )

    stops.append(
        {
            "type": "dropoff",
            "coords": dropoff_coords,
            "label": "Dropoff (1h)",
        }
    )

    return stops


class ELDCalculator:
    def __init__(
        self,
        route: dict,
        route_from_curr_to_pickup_location: dict,
        curr_cycle_used_hours: float,
    ):
        self.route = route
        self.route_from_curr_to_pickup_location = (
            route_from_curr_to_pickup_location
        )
        self.curr_cycle_available = max(
            0, MAX_CYCLE_HOURS - curr_cycle_used_hours
        )
        self._init_calculator()

    def get_eld_logs(self) -> list[dict]:
        logs = []
        remaining_hours = self.route_total_hours

        while remaining_hours > 0:
            self._init_day_data()

            if self.curr_cycle_available < min(
                remaining_hours, MAX_DRIVING_HOURS_PER_DAY
            ):
                self._reset_cycle_hours(logs)
                continue

            self._add_start_day_activities()
            self._add_day_activities(remaining_hours=remaining_hours)
            self._add_end_day_activities(
                is_last_day=(remaining_hours - self.driving_hours <= 0)
            )

            logs.append(
                {
                    "day": self.day_index,
                    "off_duty_hours": round(self.off_duty_hours, 2),
                    "sleeper_berth_hours": round(self.sleeper_berth_hours, 2),
                    "driving_hours": round(self.driving_hours, 2),
                    "on_duty_hours": round(self.on_duty_hours, 2),
                    "total_on_duty": round(
                        self.driving_hours + self.on_duty_hours, 2
                    ),
                    "daily_distance_miles": round(
                        self.driving_hours * self.speed_mph, 2
                    ),
                    "duty_status_timeline": self.duty_status_timeline,
                }
            )

            remaining_hours -= self.driving_hours
            self.curr_cycle_available -= self.driving_hours

            if not self.pickup_done:
                self.driving_hours_to_pickup -= self.driving_hours

            self.day_index += 1
            self.cycle_day += 1

            if self.cycle_day >= MAX_CYCLE_DAYS:
                self.curr_cycle_available += MAX_DRIVING_HOURS_PER_DAY

        return logs

    def _init_calculator(self):
        duration_s = self.route.get("duration", 0)
        route_distance_m = self.route.get("distance", 0)

        route_driving_hours = duration_s / SECONDS_TO_HOURS

        self.route_distance_miles = route_distance_m * METERS_TO_MILES
        self.speed_mph = self.route_distance_miles / route_driving_hours
        # include pickup (1h) and dropoff (1h)
        self.route_total_hours = route_driving_hours + 2.0
        self.driving_hours_to_pickup = (
            self.route_from_curr_to_pickup_location.get("duration", 0)
            / SECONDS_TO_HOURS
        )
        self.day_index = 1
        self.cycle_day = 1
        self.pickup_done = False

    def _init_day_data(self):
        self.off_duty_hours = 0
        self.sleeper_berth_hours = 0
        self.driving_hours = 0
        self.on_duty_hours = 0
        self.current_day_time = 0
        self.duty_status_timeline: list[dict] = []

    def _add_change_to_time_line(
        self,
        status: TimeLineChangeType,
        time_to_add: float,
        activity: str,
    ):
        self.duty_status_timeline.append(
            {
                "status": status,
                "start": self.current_day_time,
                "end": self.current_day_time + time_to_add,
                "activity": activity,
            }
        )

        self.off_duty_hours += (
            time_to_add if status == TimeLineChangeType.OFF_DUTY else 0
        )
        self.sleeper_berth_hours += (
            time_to_add if status == TimeLineChangeType.SLEEPER_BERTH else 0
        )
        self.driving_hours += (
            time_to_add if status == TimeLineChangeType.DRIVING else 0
        )
        self.on_duty_hours += (
            time_to_add if status == TimeLineChangeType.ON_DUTY else 0
        )

        self.current_day_time += time_to_add
        if status != TimeLineChangeType.DRIVING:
            current_covered_distance = round(
                self.driving_hours * self.speed_mph, 2
            )

    def _add_start_day_activities(self):
        start_day_activities = [
            {
                "status": TimeLineChangeType.OFF_DUTY,
                "time_to_add": NUMBER_OF_HOURS_FROM_MIDNIGHT_TO_SIX,
                "activity": "Off duty",
            }
            if self.day_index == 1
            else {
                "status": TimeLineChangeType.SLEEPER_BERTH,
                "time_to_add": NUMBER_OF_HOURS_FROM_MIDNIGHT_TO_SIX,
                "activity": "Sleeper berth",
            },
            {
                "status": TimeLineChangeType.ON_DUTY,
                "time_to_add": TRIP_TIV_DURATION_H,
                "activity": "Pre-Trip/TIV (30 min)",
            },
        ]

        if (
            self.driving_hours_to_pickup <= MAX_DRIVING_HOURS_PER_DAY
            and not self.pickup_done
        ):
            self._include_pickup(start_day_activities)
            self.pickup_done = True

        for day_activity in start_day_activities:
            self._add_change_to_time_line(
                status=day_activity.get("status"),
                time_to_add=day_activity.get("time_to_add"),
                activity=day_activity.get("activity"),
            )

    def _include_pickup(self, day_activities: list[dict]):
        day_activities.append(
            {
                "status": TimeLineChangeType.DRIVING,
                "time_to_add": min(
                    self.driving_hours_to_pickup,
                    MAX_DRIVING_HOURS_TO_REST,
                ),
                "activity": "Driving to pickup",
            },
        )

        if self.driving_hours_to_pickup > MAX_DRIVING_HOURS_TO_REST:
            self.driving_hours_to_pickup -= MAX_DRIVING_HOURS_TO_REST
            day_activities.extend(
                [
                    {
                        "status": TimeLineChangeType.OFF_DUTY,
                        "time_to_add": BREAK_DURATION_H,
                        "activity": "Off duty, 8 hours driving break (30 min)",
                    },
                    {
                        "status": TimeLineChangeType.DRIVING,
                        "time_to_add": self.driving_hours_to_pickup,
                        "activity": "Driving to pickup",
                    },
                ]
            )

        day_activities.append(
            {
                "status": TimeLineChangeType.ON_DUTY,
                "time_to_add": PICKUP_DURATION_H,
                "activity": "Pickup (1 hour)",
            },
        )

    def _add_end_day_activities(self, is_last_day: bool = False):
        end_day_activities = [
            {
                "status": TimeLineChangeType.ON_DUTY,
                "time_to_add": DROPOFF_DURATION_H,
                "activity": "Dropoff (1 hour)",
            }
            if is_last_day
            else {
                "status": TimeLineChangeType.ON_DUTY,
                "time_to_add": TRIP_TIV_DURATION_H,
                "activity": "Post-Trip/TIV (30 min)",
            },
            {
                "status": TimeLineChangeType.OFF_DUTY,
                "time_to_add": (BREAK_DURATION_H * 3),
                "activity": "Off duty, end day rest (1.5 hours)",
            },
            {
                "status": TimeLineChangeType.SLEEPER_BERTH,
                "time_to_add": 0,
                "activity": "Sleeper berth",
            }
            if not is_last_day
            else {
                "status": TimeLineChangeType.OFF_DUTY,
                "time_to_add": 0,
                "activity": "Off duty, trip is done",
            },
        ]

        for day_activity in end_day_activities:
            activity = day_activity.get("activity")
            time_to_add = day_activity.get("time_to_add")

            if activity in ["Sleeper berth", "Off duty, trip is done"]:
                time_to_add = HOURS_IN_DAY - self.current_day_time

            self._add_change_to_time_line(
                status=day_activity.get("status"),
                time_to_add=time_to_add,
                activity=activity,
            )

    def _add_day_activities(self, remaining_hours: float):
        day_activities = [
            {
                "status": TimeLineChangeType.DRIVING,
                "time_to_add": 0,
                "activity": "Driving before 8 hours rest",
            },
            {
                "status": TimeLineChangeType.OFF_DUTY,
                "time_to_add": BREAK_DURATION_H,
                "activity": "Off duty, 8 hours driving break (30 min)",
            },
            {
                "status": TimeLineChangeType.DRIVING,
                "time_to_add": 0,
                "activity": "Driving after 8 hours rest",
            },
        ]

        for day_activity in day_activities:
            time_to_add = day_activity["time_to_add"]
            activity = day_activity["activity"]

            match activity:
                case "Driving before 8 hours rest":
                    time_to_add = min(
                        remaining_hours,
                        MAX_DRIVING_HOURS_TO_REST - self.driving_hours,
                    )
                case "Driving after 8 hours rest":
                    time_to_add = min(
                        remaining_hours - self.driving_hours,
                        MAX_DRIVING_HOURS_PER_DAY - self.driving_hours,
                    )

            self._add_change_to_time_line(
                status=day_activity["status"],
                time_to_add=time_to_add,
                activity=activity,
            )

            if remaining_hours - self.driving_hours <= 0:
                break

    def _reset_cycle_hours(self, logs: list[dict]):
        for _ in range(2):
            self._init_day_data()
            self._add_change_to_time_line(
                status=TimeLineChangeType.OFF_DUTY,
                time_to_add=HOURS_IN_DAY,
                activity="Off duty, cycle reset",
            )

            logs.append(
                {
                    "day": self.day_index,
                    "off_duty_hours": round(self.off_duty_hours, 2),
                    "sleeper_berth_hours": round(self.sleeper_berth_hours, 2),
                    "driving_hours": round(self.driving_hours, 2),
                    "on_duty_hours": round(self.on_duty_hours, 2),
                    "total_on_duty": round(
                        self.driving_hours + self.on_duty_hours, 2
                    ),
                    "daily_distance_miles": round(
                        self.driving_hours * self.speed_mph, 2
                    ),
                    "duty_status_timeline": self.duty_status_timeline,
                }
            )

            self.day_index += 1

        self.curr_cycle_available = MAX_CYCLE_HOURS
        self.cycle_day = 0
