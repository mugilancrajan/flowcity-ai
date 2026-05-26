from enum import Enum, auto


class VehicleArchetype(Enum):
    conservative = auto()
    normal = auto()
    aggressive = auto()
    reckless = auto()


class VehicleState(Enum):
    spawning = auto()
    driving = auto()
    waiting_light = auto()
    waiting_stop = auto()
    arrived = auto()


class Vehicle:
    def __init__(self, id, origin, destination, archetype, speed_multiplier, following_distance, spawn_tick):
        self._id = id
        self._origin = origin
        self._destination = destination
        self._archetype = archetype
        self._speed_multiplier = speed_multiplier
        self._following_distance = following_distance
        self._state = VehicleState.spawning
        self._path = []
        self._path_index = 0
        self._position = (float(origin[0]), float(origin[1]))
        self._current_speed = 0.0
        self._desired_speed = 0.0
        self._spawn_tick = spawn_tick

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        raise AttributeError("id is read-only")

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        raise AttributeError("origin is read-only")

    @property
    def destination(self):
        return self._destination

    @destination.setter
    def destination(self, value):
        raise AttributeError("destination is read-only")

    @property
    def archetype(self):
        return self._archetype

    @archetype.setter
    def archetype(self, value):
        raise AttributeError("archetype is read-only")

    @property
    def speed_multiplier(self):
        return self._speed_multiplier

    @speed_multiplier.setter
    def speed_multiplier(self, value):
        raise AttributeError("speed_multiplier is read-only")

    @property
    def following_distance(self):
        return self._following_distance

    @following_distance.setter
    def following_distance(self, value):
        raise AttributeError("following_distance is read-only")

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def path_index(self):
        return self._path_index

    @path_index.setter
    def path_index(self, value):
        self._path_index = value

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value

    @property
    def current_speed(self):
        return self._current_speed

    @current_speed.setter
    def current_speed(self, value):
        self._current_speed = value

    @property
    def desired_speed(self):
        return self._desired_speed

    @desired_speed.setter
    def desired_speed(self, value):
        self._desired_speed = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def spawn_tick(self):
        return self._spawn_tick

    @spawn_tick.setter
    def spawn_tick(self, value):
        raise AttributeError("spawn_tick is read-only")
