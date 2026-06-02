"""
tests/test_renderer_logic.py
Pure-logic tests for Renderer: layout maths, coordinate helpers, color map,
and transition alpha curve.  No Pygame display window is opened.
"""
from __future__ import annotations

import os

# Must be set before pygame is imported so SDL uses the null/dummy driver.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import math
import pytest
import pygame

from src.visualizer.renderer import Renderer, TILE_COLORS
from src.world.world import World
from src.world.tile import TileType


# ---------------------------------------------------------------------------
# Fixture — single Renderer shared across all tests in this module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def renderer():
    pygame.init()
    pygame.font.init()
    surface = pygame.display.set_mode((1280, 720), pygame.NOFRAME)
    r = Renderer(surface)
    yield r
    pygame.quit()


# ===========================================================================
# GROUP 1 — Layout calculations
# ===========================================================================

class TestLayoutCalculations:

    def test_tile_size_20x15_window_1280x720(self, renderer):
        """tile_size = min((1280-300)/20, 720/15) = min(49.0, 48.0) = 48.0"""
        world = World(20, 15)
        renderer.recalculate_layout(1280, 720, world)
        expected = min((1280 - 300) / 20, 720 / 15)  # 48.0
        assert renderer._tile_size == pytest.approx(expected)

    def test_tile_size_10x10_window_800x600(self, renderer):
        """tile_size = min((800-300)/10, 600/10) = min(50.0, 60.0) = 50.0"""
        world = World(10, 10)
        renderer.recalculate_layout(800, 600, world)
        expected = min((800 - 300) / 10, 600 / 10)  # 50.0
        assert renderer._tile_size == pytest.approx(expected)

    def test_grid_offset_x_nonnegative(self, renderer):
        world = World(20, 15)
        renderer.recalculate_layout(1280, 720, world)
        assert renderer._grid_offset_x >= 0

    def test_grid_offset_y_nonnegative(self, renderer):
        world = World(20, 15)
        renderer.recalculate_layout(1280, 720, world)
        assert renderer._grid_offset_y >= 0

    def test_grid_centers_in_grid_area(self, renderer):
        """Grid pixel width must not exceed grid area width."""
        world = World(20, 15)
        renderer.recalculate_layout(1280, 720, world)
        grid_area_w = 1280 - 300
        assert renderer._grid_pixel_width <= grid_area_w + 1e-9

    def test_world_dims_stored(self, renderer):
        world = World(20, 15)
        renderer.recalculate_layout(1280, 720, world)
        assert renderer._world_cols == 20
        assert renderer._world_rows == 15


# ===========================================================================
# GROUP 2 — Tile pixel position
# ===========================================================================

class TestTilePixelPosition:

    @pytest.fixture(autouse=True)
    def setup(self, renderer):
        self.world = World(20, 15)
        renderer.recalculate_layout(1280, 720, self.world)
        self.r = renderer

    def test_tile_0_0_x(self):
        rect = self.r.get_tile_pixel_rect(0, 0)
        assert rect.x == int(self.r._grid_offset_x)

    def test_tile_0_0_y(self):
        rect = self.r.get_tile_pixel_rect(0, 0)
        assert rect.y == int(self.r._grid_offset_y)

    def test_tile_1_0_x(self):
        rect = self.r.get_tile_pixel_rect(1, 0)
        expected_x = int(self.r._grid_offset_x + self.r._tile_size)
        assert rect.x == expected_x

    def test_tile_last_col_last_row_x(self):
        cols, rows = self.world.cols, self.world.rows
        rect = self.r.get_tile_pixel_rect(cols - 1, rows - 1)
        expected_x = int(self.r._grid_offset_x + (cols - 1) * self.r._tile_size)
        assert rect.x == expected_x

    def test_tile_last_col_last_row_y(self):
        cols, rows = self.world.cols, self.world.rows
        rect = self.r.get_tile_pixel_rect(cols - 1, rows - 1)
        expected_y = int(self.r._grid_offset_y + (rows - 1) * self.r._tile_size)
        assert rect.y == expected_y

    def test_rect_dimensions_equal_tile_size(self):
        rect = self.r.get_tile_pixel_rect(3, 5)
        assert rect.width  == int(self.r._tile_size)
        assert rect.height == int(self.r._tile_size)


# ===========================================================================
# GROUP 3 — get_tile_at_pixel (inverse of get_tile_pixel_rect)
# ===========================================================================

class TestTileAtPixel:

    @pytest.fixture(autouse=True)
    def setup(self, renderer):
        self.world = World(20, 15)
        renderer.recalculate_layout(1280, 720, self.world)
        self.r = renderer

    def test_origin_pixel_returns_0_0(self):
        px = self.r._grid_offset_x + 0.5   # centre of first tile
        py = self.r._grid_offset_y + 0.5
        result = self.r.get_tile_at_pixel(px, py)
        assert result == (0, 0)

    def test_top_left_corner_of_grid_returns_0_0(self):
        px = self.r._grid_offset_x
        py = self.r._grid_offset_y
        result = self.r.get_tile_at_pixel(px, py)
        assert result == (0, 0)

    def test_pixel_left_of_grid_returns_none(self):
        px = self.r._grid_offset_x - 1
        py = self.r._grid_offset_y + self.r._tile_size / 2
        result = self.r.get_tile_at_pixel(px, py)
        assert result is None

    def test_pixel_right_of_grid_returns_none(self):
        px = self.r._grid_offset_x + self.r._grid_pixel_width + 1
        py = self.r._grid_offset_y + self.r._tile_size / 2
        result = self.r.get_tile_at_pixel(px, py)
        assert result is None

    def test_pixel_above_grid_returns_none(self):
        px = self.r._grid_offset_x + self.r._tile_size / 2
        py = self.r._grid_offset_y - 1
        result = self.r.get_tile_at_pixel(px, py)
        assert result is None

    def test_pixel_below_grid_returns_none(self):
        px = self.r._grid_offset_x + self.r._tile_size / 2
        py = self.r._grid_offset_y + self.r._grid_pixel_height + 1
        result = self.r.get_tile_at_pixel(px, py)
        assert result is None

    def test_pixel_at_right_edge_of_grid_area_returns_none(self):
        """Pixel in UI panel area (right of grid) must return None."""
        px = float(1280 - 300 + 1)   # inside UI panel, not in grid
        py = self.r._grid_offset_y + self.r._tile_size / 2
        result = self.r.get_tile_at_pixel(px, py)
        assert result is None

    def test_round_trip_several_tiles(self):
        """get_tile_at_pixel(get_tile_pixel_rect(col, row).center) == (col, row)"""
        for col, row in [(0, 0), (5, 3), (19, 14)]:
            rect = self.r.get_tile_pixel_rect(col, row)
            cx, cy = rect.centerx, rect.centery
            assert self.r.get_tile_at_pixel(cx, cy) == (col, row)


# ===========================================================================
# GROUP 4 — TILE_COLORS map completeness
# ===========================================================================

class TestColorMap:

    def test_every_tile_type_has_entry(self):
        for tile_type in TileType:
            assert tile_type in TILE_COLORS, (
                f"TileType.{tile_type.name} missing from TILE_COLORS"
            )

    def test_no_tile_type_maps_to_none(self):
        for tile_type, color in TILE_COLORS.items():
            assert color is not None, (
                f"TileType.{tile_type.name} maps to None in TILE_COLORS"
            )

    def test_all_colors_are_rgb_tuples(self):
        for tile_type, color in TILE_COLORS.items():
            assert isinstance(color, tuple), (
                f"TileType.{tile_type.name} color is not a tuple"
            )
            assert len(color) == 3, (
                f"TileType.{tile_type.name} color does not have 3 channels"
            )

    def test_tile_color_count_matches_enum(self):
        assert len(TILE_COLORS) == len(TileType)


# ===========================================================================
# GROUP 5 — Transition alpha curve (pure math, no Renderer needed)
# ===========================================================================

def _compute_alpha(t: float) -> float:
    """Mirror of the alpha calculation in App._update_transition."""
    t = max(0.0, min(1.0, t))
    eased = t * t * (3.0 - 2.0 * t)
    if eased < 0.5:
        return eased * 2.0 * 255.0
    else:
        return (1.0 - eased) * 2.0 * 255.0


def _compute_eased(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class TestTransitionAlpha:

    def test_alpha_at_t0_is_zero(self):
        assert _compute_alpha(0.0) == pytest.approx(0.0, abs=1e-6)

    def test_alpha_at_t_half_is_255(self):
        # eased(0.5) = 0.5*0.5*(3-1) = 0.5 → boundary between halves
        # (1 - 0.5) * 2 * 255 = 255
        assert _compute_alpha(0.5) == pytest.approx(255.0, abs=1e-6)

    def test_alpha_at_t1_is_zero(self):
        assert _compute_alpha(1.0) == pytest.approx(0.0, abs=1e-6)

    def test_alpha_is_symmetric(self):
        """Alpha at t and (1-t) should be the same by the smoothstep symmetry."""
        for t in [0.1, 0.2, 0.3, 0.4]:
            assert _compute_alpha(t) == pytest.approx(_compute_alpha(1.0 - t), abs=1e-4)

    def test_eased_always_between_0_and_1(self):
        for i in range(101):
            t = i / 100.0
            e = _compute_eased(t)
            assert 0.0 <= e <= 1.0, f"eased({t}) = {e} is out of [0, 1]"

    def test_alpha_never_exceeds_255(self):
        for i in range(101):
            t = i / 100.0
            assert _compute_alpha(t) <= 255.0 + 1e-6

    def test_alpha_never_negative(self):
        for i in range(101):
            t = i / 100.0
            assert _compute_alpha(t) >= -1e-6

    def test_eased_at_t0_is_0(self):
        assert _compute_eased(0.0) == pytest.approx(0.0)

    def test_eased_at_t_half_is_half(self):
        assert _compute_eased(0.5) == pytest.approx(0.5)

    def test_eased_at_t1_is_1(self):
        assert _compute_eased(1.0) == pytest.approx(1.0)


# ===========================================================================
# GROUP 6 — Edit mode UI (palette, tool buttons, action buttons)
# ===========================================================================

def _make_edit_frame(renderer, world):
    """Helper: draw one EDIT frame and return the renderer for inspection."""
    from src.visualizer.app import AppMode
    from src.world.tile import TileType, TrafficControl
    from src.config import TOOL_PAINT
    renderer.recalculate_layout(1280, 720, world)
    renderer.draw_frame(
        AppMode.EDIT, world, 0, 1.0,
        selected_tile_type=TileType.road,
        selected_traffic_control=TrafficControl.none,
        tool=TOOL_PAINT,
        hovered_tile=None,
        drag_start=None,
        drag_end=None,
        show_speed_popup=False,
        speed_popup_input="",
        speed_selection_tiles=[],
    )
    return renderer


class TestEditUI:

    @pytest.fixture(autouse=True)
    def setup(self, renderer):
        self.world = World(20, 15)
        self.r = _make_edit_frame(renderer, self.world)
        self.panel_x = 1280 - 300  # UI_PANEL_WIDTH

    # ---- Palette tile rects -----------------------------------------------

    def test_palette_tile_rects_has_all_tile_types(self):
        for tt in TileType:
            assert tt in self.r._palette_tile_rects, (
                f"TileType.{tt.name} missing from _palette_tile_rects"
            )

    def test_palette_tile_rects_count_matches_enum(self):
        assert len(self.r._palette_tile_rects) == len(TileType)

    def test_palette_rects_within_panel_bounds(self):
        for tt, rect in self.r._palette_tile_rects.items():
            assert rect.left >= self.panel_x, (
                f"TileType.{tt.name} swatch starts left of panel"
            )
            assert rect.right <= 1280, (
                f"TileType.{tt.name} swatch extends past screen right"
            )

    # ---- Tool buttons -------------------------------------------------------

    def test_btn_tool_paint_not_none(self):
        assert self.r._btn_tool_paint is not None

    def test_btn_tool_select_not_none(self):
        assert self.r._btn_tool_select is not None

    def test_tool_buttons_within_panel(self):
        assert self.r._btn_tool_paint.left  >= self.panel_x
        assert self.r._btn_tool_select.left >= self.panel_x

    def test_tool_buttons_do_not_overlap(self):
        assert not self.r._btn_tool_paint.colliderect(self.r._btn_tool_select)

    # ---- Action buttons -----------------------------------------------------

    def test_btn_save_not_none(self):
        assert self.r._btn_save is not None

    def test_btn_load_not_none(self):
        assert self.r._btn_load is not None

    def test_btn_start_sim_not_none(self):
        assert self.r._btn_start_sim is not None

    def test_action_buttons_within_panel(self):
        for btn in (self.r._btn_save, self.r._btn_load, self.r._btn_start_sim):
            assert btn.left  >= self.panel_x
            assert btn.right <= 1280

    def test_action_buttons_do_not_overlap(self):
        assert not self.r._btn_save.colliderect(self.r._btn_load)
        assert not self.r._btn_load.colliderect(self.r._btn_start_sim)

    # ---- Traffic control rects ----------------------------------------------

    def test_palette_traffic_rects_has_all_controls(self):
        from src.world.tile import TrafficControl
        for tc in TrafficControl:
            assert tc in self.r._palette_traffic_rects, (
                f"TrafficControl.{tc.name} missing from _palette_traffic_rects"
            )


# ===========================================================================
# GROUP 7 — Selection rect calculation (pure math, no renderer needed)
# ===========================================================================

def _get_selection_tiles(drag_start, drag_end):
    """Mirror of App._get_selection_rect_tiles — tested in isolation."""
    if drag_start is None or drag_end is None:
        return []
    c1, r1 = drag_start
    c2, r2 = drag_end
    col_min, col_max = min(c1, c2), max(c1, c2)
    row_min, row_max = min(r1, r2), max(r1, r2)
    return [
        (col, row)
        for row in range(row_min, row_max + 1)
        for col in range(col_min, col_max + 1)
    ]


class TestSelectionRect:

    def test_forward_drag_tile_count(self):
        # cols 2-4 = 3, rows 2-5 = 4 → 12 tiles
        tiles = _get_selection_tiles((2, 2), (4, 5))
        assert len(tiles) == 12

    def test_forward_drag_contains_corners(self):
        tiles = _get_selection_tiles((2, 2), (4, 5))
        assert (2, 2) in tiles
        assert (4, 5) in tiles
        assert (4, 2) in tiles
        assert (2, 5) in tiles

    def test_forward_drag_contains_interior(self):
        tiles = _get_selection_tiles((2, 2), (4, 5))
        assert (3, 3) in tiles

    def test_reverse_drag_same_tiles_as_forward(self):
        forward = set(_get_selection_tiles((2, 2), (4, 5)))
        reverse = set(_get_selection_tiles((4, 5), (2, 2)))
        assert forward == reverse

    def test_diagonal_reverse_drag_same_tiles(self):
        # Drag from bottom-left to top-right
        a = set(_get_selection_tiles((2, 5), (4, 2)))
        b = set(_get_selection_tiles((4, 2), (2, 5)))
        assert a == b
        assert len(a) == 12

    def test_single_tile_selection(self):
        tiles = _get_selection_tiles((3, 3), (3, 3))
        assert tiles == [(3, 3)]

    def test_none_start_returns_empty(self):
        assert _get_selection_tiles(None, (3, 3)) == []

    def test_none_end_returns_empty(self):
        assert _get_selection_tiles((3, 3), None) == []


# ===========================================================================
# GROUP 8 — Speed popup rendering
# ===========================================================================

class TestSpeedPopup:

    def test_popup_renders_without_error(self, renderer):
        from src.visualizer.app import AppMode
        from src.world.tile import TileType, TrafficControl

        world = World(20, 15)
        for col in range(5, 8):
            world.set_tile(col, 7, tile_type=TileType.road)
        renderer.recalculate_layout(1280, 720, world)

        # Should complete without raising
        renderer.draw_frame(
            AppMode.EDIT, world, 0, 1.0,
            selected_tile_type=TileType.road,
            selected_traffic_control=TrafficControl.none,
            tool="select",
            hovered_tile=None,
            drag_start=None,
            drag_end=None,
            show_speed_popup=True,
            speed_popup_input="45",
            speed_selection_tiles=[(5, 7), (6, 7), (7, 7)],
        )
        assert renderer._speed_popup_rect is not None

    def test_popup_hidden_when_show_false(self, renderer):
        from src.visualizer.app import AppMode
        from src.world.tile import TileType, TrafficControl

        world = World(20, 15)
        renderer.recalculate_layout(1280, 720, world)
        renderer._speed_popup_rect = None  # reset

        renderer.draw_frame(
            AppMode.EDIT, world, 0, 1.0,
            selected_tile_type=TileType.road,
            selected_traffic_control=TrafficControl.none,
            tool="select",
            show_speed_popup=False,
            speed_popup_input="",
            speed_selection_tiles=[(5, 7)],
        )
        # Popup rect not set when show=False
        assert renderer._speed_popup_rect is None

    def test_popup_hidden_when_no_tiles(self, renderer):
        from src.visualizer.app import AppMode
        from src.world.tile import TileType, TrafficControl

        world = World(20, 15)
        renderer.recalculate_layout(1280, 720, world)
        renderer._speed_popup_rect = None

        renderer.draw_frame(
            AppMode.EDIT, world, 0, 1.0,
            selected_tile_type=TileType.road,
            selected_traffic_control=TrafficControl.none,
            tool="select",
            show_speed_popup=True,
            speed_popup_input="",
            speed_selection_tiles=[],   # empty list → no popup
        )
        assert renderer._speed_popup_rect is None


# ===========================================================================
# GROUP 9 — Simulate mode logic
# ===========================================================================

class TestSimulateModeLogic:

    def test_render_congestion_chart_empty_returns_none(self, renderer):
        """Empty snapshot list must return None without raising."""
        result = renderer.render_congestion_chart([])
        assert result is None

    def test_health_color_zero_is_reddish(self, renderer):
        r, g, b = renderer._health_color(0)
        assert r > g, "score=0 should be red-dominant"
        assert r > b, "score=0 should be red-dominant"

    def test_health_color_hundred_is_greenish(self, renderer):
        r, g, b = renderer._health_color(100)
        assert g > r, "score=100 should be green-dominant"
        assert g > b, "score=100 should be green-dominant"

    def test_health_color_fifty_is_yellowish(self, renderer):
        r, g, b = renderer._health_color(50)
        assert r > 50, "score=50 should have significant red (yellow mix)"
        assert g > 50, "score=50 should have significant green (yellow mix)"

    def test_vehicle_pixel_pos_known_position(self, renderer):
        """_vehicle_pixel_pos at (5,7) going right places vehicle at tile centre, right lane."""
        from src.vehicle.vehicle import Vehicle, VehicleArchetype
        from src.config import VEHICLE_ROAD_OFFSET

        world = World(20, 15)
        renderer.recalculate_layout(1280, 720, world)

        v = Vehicle(1, (5, 7), (10, 7), VehicleArchetype.normal, 1.0, 1.5, 0)
        v.path       = [(5, 7), (6, 7), (7, 7)]
        v.path_index = 0
        v.position   = (5.0, 7.0)

        px, py = renderer._vehicle_pixel_pos(v)

        # Segment direction (5,7)→(6,7): dx=1, dy=0.
        # +0.5 centres vehicle on tile; right-hand perp in screen space = (−dy, dx) = (0, +1)
        # → no x-offset, positive y-offset (downward in screen = right lane for rightward travel).
        ts     = renderer._tile_size
        base_x = renderer._grid_offset_x + (5.0 + 0.5) * ts
        base_y = renderer._grid_offset_y + (7.0 + 0.5) * ts
        offset = VEHICLE_ROAD_OFFSET * ts

        assert px == pytest.approx(base_x,          abs=0.1)
        assert py == pytest.approx(base_y + offset,  abs=0.1)
