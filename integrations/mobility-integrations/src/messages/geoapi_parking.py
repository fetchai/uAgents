from uagents import Model


class GeoParkingRequest(Model):
    """
    Represents a Geo Parking Request.

    Attributes:
        latitude (float): The latitude of the location for which parking is requested.
        longitude (float): The longitude of the location for which parking is requested.
        radius (int): The search radius (in miles) to find parking spots around the specified location.
        max_result (int, optional): The maximum number of parking spots to be returned. Default is 5.
    """

    latitude: float
    longitude: float
    radius: int
    max_result: int = 5
