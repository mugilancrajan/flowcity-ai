from __future__ import annotations

import sys
import time
import tkinter
import tkinter.filedialog
from enum import Enum, auto

import pygame

from src.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    DEFAULT_GRID_COLS,
    DEFAULT_GRID_ROWS,
    TRANSITION_DURATION_MS,
    TOOL_PAINT,
    TOOL_SELECT,
    SIMULATE_SPEEDS,
    DEFAULT_SPEED,
    SPEED_SLOW,
    SPEED_NORMAL,
    SPEED_FAST,
    SPEED_ULTRA,
    VEHICLE_SIZE_FRACTION,
)
from src.world.world import World
from src.world.tile import TileType, TrafficControl
from src.visualizer.renderer import Renderer
from src.simulation.simulation_engine import SimulationEngine


class AppMode(Enum):
    STARTUP  = auto()
    EDIT     = auto()
    SIMULATE = auto()


class App:
    """Top-level application: game loop, mode state, transitions."""

    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()

        self._screen: pygame.Surface = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE
        )
        pygame.display.set_caption("FlowCity AI")

        self._clock = pygame.time.Clock()

        # Mode / world state
        self._mode:   AppMode                   = AppMode.STARTUP
        self._world:  World | None              = None
        self._engine: SimulationEngine | None   = None

        # Renderer
        self._renderer = Renderer(self._screen)

        # Transition state
        self._transitioning:              bool           = False
        self._transition_alpha:           float          = 0.0
        self._transition_scale:           float          = 1.0
        self._transition_target_mode:     AppMode | None = None
        self._transition_start_ms:        int            = 0
        self._transition_midpoint_passed: bool           = False

        # ------------------------------------------------------------------
        # Edit mode state
        # ------------------------------------------------------------------

        # Active tool and selections
        self._tool:                       str            = TOOL_PAINT
        self._selected_tile_type:         TileType       = TileType.road
        self._selected_traffic_control:   TrafficControl = TrafficControl.none

        # Mouse drag state
        self._mouse_down:  bool                        = False
        self._drag_start:  tuple[int, int] | None      = None   # tile coords
        self._drag_end:    tuple[int, int] | None      = None   # tile coords

        # Speed limit popup state
        self._show_speed_popup:      bool                   = False
        self._speed_popup_input:     str                    = ""
        self._speed_popup_rect:      pygame.Rect | None     = None
        self._speed_selection_tiles: list[tuple[int, int]]  = []

        # Hovered tile (updated every MOUSEMOTION in edit mode)
        self._hovered_tile: tuple[int, int] | None = None

        # ------------------------------------------------------------------
        # Simulate mode state
        # ------------------------------------------------------------------

        self._sim_paused:                bool                  = True
        self._sim_speed_index:           int                   = 0
        self._selected_vehicle                                 = None
        self._chart_surface:             pygame.Surface | None = None
        self._chart_last_snapshot_count: int                   = 0

        # Tick advancement timing
        self._sim_tick_accumulator: float = 0.0
        self._sim_last_time:        float = 0.0

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        while True:
            dt_ms = self._clock.tick(FPS)
            self._handle_events()
            self._update_transition(dt_ms)
            self._advance_simulation()
            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _handle_events(self) -> None:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.VIDEORESIZE:
                self._renderer.recalculate_layout(event.w, event.h, self._world)

            elif event.type == pygame.WINDOWRESIZED:
                w, h = self._screen.get_size()
                self._renderer.recalculate_layout(w, h, self._world)

            elif event.type == pygame.MOUSEMOTION:
                if self._mode == AppMode.EDIT:
                    self._handle_mouse_motion_edit(event.pos)
                    if self._mouse_down:
                        if self._tool == TOOL_PAINT:
                            self._handle_paint(event.pos)
                        elif self._tool == TOOL_SELECT:
                            tile = self._renderer.get_tile_at_pixel(*event.pos)
                            if tile is not None:
                                self._drag_end = tile

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._mode == AppMode.STARTUP:
                    self._handle_click_startup(event.pos)
                elif self._mode == AppMode.EDIT:
                    self._handle_mousedown_edit(event.pos)
                elif self._mode == AppMode.SIMULATE:
                    self._handle_click_simulate(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self._mode == AppMode.EDIT:
                    self._handle_mouseup_edit(event.pos)

            elif event.type == pygame.KEYDOWN:
                if self._mode == AppMode.EDIT:
                    self._handle_keydown_edit(event)
                elif self._mode == AppMode.SIMULATE:
                    self._handle_keydown_simulate(event)

    # ------------------------------------------------------------------
    # Startup click handler
    # ------------------------------------------------------------------

    def _handle_click_startup(self, pos: tuple[int, int]) -> None:
        btn_new  = self._renderer._btn_new_map
        btn_load = self._renderer._btn_load_map

        if btn_new is not None and btn_new.collidepoint(pos):
            self._world = World(DEFAULT_GRID_COLS, DEFAULT_GRID_ROWS)
            self._start_transition(AppMode.EDIT)

        elif btn_load is not None and btn_load.collidepoint(pos):
            loaded = self._load_world_from_file()
            if loaded is not None:
                self._world = loaded
                self._start_transition(AppMode.EDIT)

    # ------------------------------------------------------------------
    # Edit mode — mouse handlers
    # ------------------------------------------------------------------

    def _handle_mouse_motion_edit(self, pos: tuple[int, int]) -> None:
        self._hovered_tile = self._renderer.get_tile_at_pixel(*pos)

    def _handle_mousedown_edit(self, pos: tuple[int, int]) -> None:
        # While the popup is open, ignore all grid/palette interaction.
        if self._show_speed_popup:
            return

        r = self._renderer

        # Tool buttons
        if r._btn_tool_paint is not None and r._btn_tool_paint.collidepoint(pos):
            self._tool = TOOL_PAINT
            return
        if r._btn_tool_select is not None and r._btn_tool_select.collidepoint(pos):
            self._tool = TOOL_SELECT
            return

        # Tile palette swatches
        for tile_type, rect in r._palette_tile_rects.items():
            if rect.collidepoint(pos):
                self._selected_tile_type = tile_type
                self._tool = TOOL_PAINT
                return

        # Traffic control swatches
        for tc, rect in r._palette_traffic_rects.items():
            if rect.collidepoint(pos):
                self._selected_traffic_control = tc
                return

        # Action buttons
        if r._btn_save is not None and r._btn_save.collidepoint(pos):
            if self._world is not None:
                self._save_world_to_file(self._world)
            return
        if r._btn_load is not None and r._btn_load.collidepoint(pos):
            loaded = self._load_world_from_file()
            if loaded is not None:
                self._world = loaded
                w, h = self._screen.get_size()
                self._renderer.recalculate_layout(w, h, self._world)
            return
        if r._btn_start_sim is not None and r._btn_start_sim.collidepoint(pos):
            self._start_transition(AppMode.SIMULATE)
            return

        # Grid area
        tile = self._renderer.get_tile_at_pixel(*pos)
        if tile is None:
            return

        self._mouse_down = True
        if self._tool == TOOL_PAINT:
            self._handle_paint(pos)
        elif self._tool == TOOL_SELECT:
            self._drag_start = tile
            self._drag_end   = tile

    def _handle_mouseup_edit(self, pos: tuple[int, int]) -> None:
        self._mouse_down = False

        if self._tool == TOOL_SELECT and self._drag_start is not None:
            tiles = self._get_selection_rect_tiles()
            road_tiles = [
                (col, row) for col, row in tiles
                if self._world is not None
                and self._world.get_tile(col, row).tile_type
                in (TileType.road, TileType.highway)
            ]
            if road_tiles:
                self._speed_selection_tiles = road_tiles
                self._show_speed_popup      = True
                self._speed_popup_input     = ""

            # Always clear drag state after releasing select
            self._drag_start = None

        self._drag_end = None

    def _handle_paint(self, pos: tuple[int, int]) -> None:
        if self._world is None:
            return
        tile = self._renderer.get_tile_at_pixel(*pos)
        if tile is None:
            return
        col, row = tile
        self._world.set_tile(col, row, tile_type=self._selected_tile_type)
        if self._selected_traffic_control != TrafficControl.none:
            self._world.set_tile(col, row, traffic_control=self._selected_traffic_control)

    # ------------------------------------------------------------------
    # Edit mode — keyboard handler
    # ------------------------------------------------------------------

    def _handle_keydown_edit(self, event: pygame.event.Event) -> None:
        # ---- Speed popup input ----------------------------------------
        if self._show_speed_popup:
            if event.unicode.isdigit() and len(self._speed_popup_input) < 3:
                self._speed_popup_input += event.unicode

            elif event.key == pygame.K_BACKSPACE:
                self._speed_popup_input = self._speed_popup_input[:-1]

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self._speed_popup_input and self._world is not None:
                    value = int(self._speed_popup_input)
                    for col, row in self._speed_selection_tiles:
                        self._world.set_tile(col, row, speed_limit=value)
                self._show_speed_popup      = False
                self._speed_popup_input     = ""
                self._speed_selection_tiles = []

            elif event.key == pygame.K_ESCAPE:
                self._show_speed_popup      = False
                self._speed_popup_input     = ""
                self._speed_selection_tiles = []

            return  # all other keys ignored while popup is open

        # ---- Normal edit mode shortcuts --------------------------------
        key = event.key

        if key == pygame.K_s:
            if self._world is not None:
                self._save_world_to_file(self._world)

        elif key == pygame.K_l:
            loaded = self._load_world_from_file()
            if loaded is not None:
                self._world = loaded
                w, h = self._screen.get_size()
                self._renderer.recalculate_layout(w, h, self._world)

        elif key == pygame.K_1:
            self._selected_tile_type = TileType.empty
        elif key == pygame.K_2:
            self._selected_tile_type = TileType.road
        elif key == pygame.K_3:
            self._selected_tile_type = TileType.highway
        elif key == pygame.K_4:
            self._selected_tile_type = TileType.residential
        elif key == pygame.K_5:
            self._selected_tile_type = TileType.commercial
        elif key == pygame.K_6:
            self._selected_tile_type = TileType.workplace
        elif key == pygame.K_e:
            self._selected_tile_type = TileType.empty

        elif key == pygame.K_TAB:
            self._tool = TOOL_SELECT if self._tool == TOOL_PAINT else TOOL_PAINT

        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._start_transition(AppMode.SIMULATE)

        elif key == pygame.K_ESCAPE:
            # Cancel any in-progress drag
            self._drag_start = None
            self._drag_end   = None

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------

    def _get_selection_rect_tiles(self) -> list[tuple[int, int]]:
        """Return all (col, row) in the bounding rect of the current drag."""
        if self._drag_start is None or self._drag_end is None:
            return []
        c1, r1 = self._drag_start
        c2, r2 = self._drag_end
        col_min, col_max = min(c1, c2), max(c1, c2)
        row_min, row_max = min(r1, r2), max(r1, r2)
        return [
            (col, row)
            for row in range(row_min, row_max + 1)
            for col in range(col_min, col_max + 1)
        ]

    # ------------------------------------------------------------------
    # Simulate mode — handlers
    # ------------------------------------------------------------------

    def _handle_click_simulate(self, pos: tuple[int, int]) -> None:
        r = self._renderer

        # Playback control buttons (set by renderer each frame)
        if r._btn_sim_pause is not None and r._btn_sim_pause.collidepoint(pos):
            self._sim_paused = not self._sim_paused
            return
        if r._btn_sim_reset is not None and r._btn_sim_reset.collidepoint(pos):
            self._start_transition(AppMode.EDIT)
            return
        for i, rect in enumerate(r._btn_sim_speeds):
            if rect.collidepoint(pos):
                self._sim_speed_index = i
                return
        if r._btn_inspector_close is not None and r._btn_inspector_close.collidepoint(pos):
            self._selected_vehicle = None
            return

        # Vehicle hit detection
        if self._engine is None:
            return
        half = max(2, int(r._tile_size * VEHICLE_SIZE_FRACTION) // 2)
        for vehicle in self._engine.active_vehicles:
            vpx, vpy = r._vehicle_pixel_pos(vehicle)
            hit_rect = pygame.Rect(
                int(vpx) - half, int(vpy) - half, half * 2, half * 2
            )
            if hit_rect.collidepoint(pos):
                self._selected_vehicle = vehicle
                return

        # Click on grid area with no vehicle hit — deselect
        if r.get_tile_at_pixel(*pos) is not None:
            self._selected_vehicle = None

    def _handle_keydown_simulate(self, event: pygame.event.Event) -> None:
        key = event.key
        if key == pygame.K_SPACE:
            self._sim_paused = not self._sim_paused
        elif key == pygame.K_r:
            self._start_transition(AppMode.EDIT)
        elif key == pygame.K_1:
            self._sim_speed_index = 0
        elif key == pygame.K_2:
            self._sim_speed_index = 1
        elif key == pygame.K_4:
            self._sim_speed_index = 2
        elif key == pygame.K_8:
            self._sim_speed_index = 3
        elif key == pygame.K_ESCAPE:
            self._selected_vehicle = None

    def _advance_simulation(self) -> None:
        if self._engine is None or self._sim_paused or self._transitioning:
            self._sim_last_time = time.time()
            return

        now = time.time()
        dt  = now - self._sim_last_time
        self._sim_last_time = now

        ticks_per_second = SIMULATE_SPEEDS[self._sim_speed_index][0] * self._engine.speed
        self._sim_tick_accumulator += dt * ticks_per_second

        # Cap to prevent spiral-of-death on frame drops
        max_ticks_per_frame = 20
        ticks_to_step = min(int(self._sim_tick_accumulator), max_ticks_per_frame)
        self._sim_tick_accumulator -= ticks_to_step

        for _ in range(ticks_to_step):
            self._engine.step()

        # Refresh chart if new snapshots arrived
        if len(self._engine.metrics_snapshots) != self._chart_last_snapshot_count:
            self._chart_surface = self._renderer.render_congestion_chart(
                self._engine.metrics_snapshots
            )
            self._chart_last_snapshot_count = len(self._engine.metrics_snapshots)

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------

    def _start_transition(self, target_mode: AppMode) -> None:
        self._transitioning              = True
        self._transition_target_mode     = target_mode
        self._transition_start_ms        = pygame.time.get_ticks()
        self._transition_alpha           = 0.0
        self._transition_scale           = 1.0
        self._transition_midpoint_passed = False

    def _update_transition(self, dt_ms: int) -> None:
        if not self._transitioning:
            return

        now   = pygame.time.get_ticks()
        raw_t = (now - self._transition_start_ms) / TRANSITION_DURATION_MS
        t     = max(0.0, min(1.0, raw_t))

        # Smooth-step ease-in-out: f(t) = t² (3 − 2t)
        eased = t * t * (3.0 - 2.0 * t)

        if eased < 0.5:
            # First half — fade out, subtle zoom in
            self._transition_alpha = eased * 2.0 * 255.0
            self._transition_scale = 1.0 + eased * 0.04
        else:
            # At midpoint: switch mode and recalculate layout
            if not self._transition_midpoint_passed:
                self._mode = self._transition_target_mode  # type: ignore[assignment]
                w, h = self._screen.get_size()
                self._renderer.recalculate_layout(w, h, self._world)
                self._transition_midpoint_passed = True

                if self._transition_target_mode.name == "SIMULATE":
                    if self._world is not None:
                        self._engine = SimulationEngine(self._world)
                        self._engine.start()
                        self._sim_paused = True
                        self._sim_tick_accumulator = 0.0
                        self._sim_last_time = time.time()
                        self._selected_vehicle = None
                        self._chart_surface = None
                        self._chart_last_snapshot_count = 0

                elif self._transition_target_mode.name == "EDIT":
                    # Returning to edit — destroy engine, keep world intact
                    self._engine = None
                    self._selected_vehicle = None
                    self._chart_surface = None

            # Second half — fade back in, no zoom
            self._transition_alpha = (1.0 - eased) * 2.0 * 255.0
            self._transition_scale = 1.0

        if t >= 1.0:
            self._transitioning    = False
            self._transition_alpha = 0.0
            self._transition_scale = 1.0

    def _get_transition_scale(self) -> float:
        """Return zoom scale for current frame.  Only > 1.0 in first half of transition."""
        if self._transitioning and not self._transition_midpoint_passed:
            return self._transition_scale
        return 1.0

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        # Compute tooltip data — only for road/highway tiles in edit mode
        hovered_speed_limit   = None
        hovered_tile_type_name = None
        if self._hovered_tile is not None and self._world is not None:
            col, row = self._hovered_tile
            tile = self._world.get_tile(col, row)
            if tile.tile_type in (TileType.road, TileType.highway):
                hovered_speed_limit    = tile.speed_limit
                hovered_tile_type_name = tile.tile_type.name

        self._renderer.draw_frame(
            self._mode,
            self._world,
            int(self._transition_alpha),
            self._get_transition_scale(),
            selected_tile_type=self._selected_tile_type,
            selected_traffic_control=self._selected_traffic_control,
            tool=self._tool,
            hovered_tile=self._hovered_tile,
            drag_start=self._drag_start,
            drag_end=self._drag_end,
            show_speed_popup=self._show_speed_popup,
            speed_popup_input=self._speed_popup_input,
            speed_selection_tiles=self._speed_selection_tiles,
            hovered_speed_limit=hovered_speed_limit,
            hovered_tile_type=hovered_tile_type_name,
            tooltip_pos=pygame.mouse.get_pos(),
            # Simulate mode
            engine=self._engine,
            sim_paused=self._sim_paused,
            sim_speed_index=self._sim_speed_index,
            selected_vehicle=self._selected_vehicle,
            chart_surface=self._chart_surface,
        )

    # ------------------------------------------------------------------
    # File I/O helpers (tkinter dialogs)
    # ------------------------------------------------------------------

    def _load_world_from_file(self) -> World | None:
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = tkinter.filedialog.askopenfilename(
            title="Load Map",
            filetypes=[("JSON files", "*.json")],
        )
        root.destroy()
        if path:
            return World.load(path)
        return None

    def _save_world_to_file(self, world: World) -> None:
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = tkinter.filedialog.asksaveasfilename(
            title="Save Map",
            filetypes=[("JSON files", "*.json")],
            defaultextension=".json",
        )
        root.destroy()
        if path:
            world.save(path)
