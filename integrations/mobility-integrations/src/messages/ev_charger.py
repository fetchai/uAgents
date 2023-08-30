from uagents import Model


class EVRequest(Model):
    """
    Represents an Electric Vehicle (EV) Charging Request.

    Attributes:
        latitude (float): The latitude of the location where EV charging is requested.
        longitude (float): The longitude of the location where EV charging is requested.
        miles_radius (float): The search radius (in miles) to find available EV charging stations
                             around the specified location.
    """

    latitude: float
    longitude: float
    miles_radius: float
