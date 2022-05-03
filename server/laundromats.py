import json, random

DEFAULT_NUM = 5

class Location:
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat

    def serialize(self):
        return json.dumps(self, default = lambda obj : obj.__dict__)


class LocationFactory:

    @staticmethod
    def generate_locations(num=DEFAULT_NUM):
        num = min(num, DEFAULT_NUM)
        lat_lon = [(38.635000, -90.232970), (38.656010, -90.300900), (38.623938, -90.192633), (38.713930, -90.254460), (38.725110, -90.228750)]
        locations = []
        for i in range(num):
            lat, lon = lat_lon[i]
            locations.append(Location(lon, lat))
        return locations

if __name__ == "__main__":
    locations = LocationFactory.generate_locations()
    for location in locations:
        print(location.serialize())

