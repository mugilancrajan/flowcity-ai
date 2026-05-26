from __future__ import annotations

import networkx as nx

from src.world.world import World
from src.world.tile import TileType
from src.exceptions import NoPathError


class RoadNetwork:
    def __init__(self, world: World) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._build(world)

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    def _build(self, world: World) -> None:
        for row in range(world.rows):
            for col in range(world.cols):
                tile = world.get_tile(col, row)
                if tile.tile_type == TileType.empty:
                    continue
                node = (col, row)
                self._graph.add_node(
                    node,
                    tile_type=tile.tile_type,
                    speed_limit=tile.speed_limit,
                    traffic_control=tile.traffic_control,
                )
                for neighbor in world.get_neighbors(col, row):
                    if neighbor.tile_type == TileType.empty:
                        continue
                    neighbor_node = neighbor.position
                    self._graph.add_edge(node, neighbor_node, weight=1)
                    self._graph.add_edge(neighbor_node, node, weight=1)

    def get_path(self, origin: tuple, destination: tuple) -> list:
        if origin not in self._graph or destination not in self._graph:
            raise NoPathError(f"No path from {origin} to {destination}")
        if origin == destination:
            return [origin]
        try:
            return nx.shortest_path(self._graph, origin, destination, weight="weight")
        except (nx.exception.NetworkXNoPath, nx.exception.NodeNotFound):
            raise NoPathError(f"No path from {origin} to {destination}")

    def rebuild(self, world: World) -> None:
        self._graph = nx.DiGraph()
        self._build(world)
