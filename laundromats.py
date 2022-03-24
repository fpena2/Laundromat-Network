import json, random


class Location:
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat

    def serialize(self):
        return json.dumps(self, default = lambda obj : obj.__dict__)


class LocationFactory:
    @staticmethod
    def generate_locations(num):
        locations = []
        for i in range(num):
            locations.append(Location(random.random(), random.random()))
        return locations

if __name__ == "__main__":
    factory = LocationFactory.generate_locations(5)

