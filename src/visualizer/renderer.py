from __future__ import annotations

import math
import pygame

from src.config import (
    UI_PANEL_WIDTH,
    COLOR_EMPTY,
    COLOR_ROAD,
    COLOR_HIGHWAY,
    COLOR_RESIDENTIAL,
    COLOR_COMMERCIAL,
    COLOR_WORKPLACE,
    COLOR_UI_BACKGROUND,
    COLOR_UI_ACCENT,
    COLOR_GRID_LINE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    SPEED_LIMIT_TO_MPH,
    # Edit mode
    PALETTE_TILE_ENTRIES,
    PALETTE_TRAFFIC_ENTRIES,
    TOOL_PAINT,
    COLOR_POPUP_BG,
    COLOR_POPUP_BORDER,
    HOVER_SHADOW_ALPHA,
    COLOR_SELECTION_FILL,
    COLOR_SELECTION_BORDER,
)
from src.world.tile import TileType, TrafficControl

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

TILE_COLORS: dict[TileType, tuple[int, int, int]] = {
    TileType.empty:       COLOR_EMPTY,
    TileType.road:        COLOR_ROAD,
    TileType.highway:     COLOR_HIGHWAY,
    TileType.residential: COLOR_RESIDENTIAL,
    TileType.commercial:  COLOR_COMMERCIAL,
    TileType.workplace:   COLOR_WORKPLACE,
}

_BG_GRID_SIZE: int = 40        # spacing of the animated startup background grid
_BG_LINE_COLOR = (35, 35, 55)  # subtle grid line, slightly brighter than bg

# Label used inside each palette entry (short form for narrow swatches)
_TILE_SHORT: dict[TileType, str] = {
    TileType.empty:       "Empty",
    TileType.road:        "Road",
    TileType.highway:     "Highway",
    TileType.residential: "Residential",
    TileType.commercial:  "Commercial",
    TileType.workplace:   "Workplace",
}


class Renderer:
    """Reads simulation / world state and draws it.  Never modifies any state."""

    def __init__(self, surface: pygame.Surface) -> None:
        self._surface = surface

        # ---- fonts --------------------------------------------------------
        available = pygame.font.get_fonts()
        if "segoeui" in available:
            self._font_large  = pygame.font.SysFont("segoeui", 48, bold=True)
            self._font_medium = pygame.font.SysFont("segoeui", 24)
            self._font_small  = pygame.font.SysFont("segoeui", 14)
        else:
            self._font_large  = pygame.font.Font(None, 56)
            self._font_medium = pygame.font.Font(None, 32)
            self._font_small  = pygame.font.Font(None, 20)

        # ---- layout state (recalculated on resize / world change) ---------
        self._window_width:      float = 0
        self._window_height:     float = 0
        self._grid_area_width:   float = 0
        self._grid_area_height:  float = 0
        self._tile_size:         float = 0
        self._grid_pixel_width:  float = 0
        self._grid_pixel_height: float = 0
        self._grid_offset_x:     float = 0
        self._grid_offset_y:     float = 0
        self._world_cols:        int   = 0
        self._world_rows:        int   = 0

        # ---- animated background ------------------------------------------
        self._anim_offset: float = 0.0
        self._anim_speed:  float = 0.3   # pixels per frame
        self._anim_tick:   int   = 0     # integer tick counter (for pulse)

        # ---- startup button rects (set by _draw_startup) ------------------
        self._btn_new_map:  pygame.Rect | None = None
        self._btn_load_map: pygame.Rect | None = None

        # ---- edit mode UI rects (set by _draw_edit_ui) --------------------
        self._palette_tile_rects:    dict[TileType, pygame.Rect]         = {}
        self._palette_traffic_rects: dict[TrafficControl, pygame.Rect]   = {}
        self._btn_tool_paint:  pygame.Rect | None = None
        self._btn_tool_select: pygame.Rect | None = None
        self._btn_save:        pygame.Rect | None = None
        self._btn_load:        pygame.Rect | None = None
        self._btn_start_sim:   pygame.Rect | None = None
        self._speed_popup_rect: pygame.Rect | None = None

        self.recalculate_layout(surface.get_width(), surface.get_height())

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def recalculate_layout(
        self,
        window_width: float,
        window_height: float,
        world=None,
    ) -> None:
        self._window_width    = window_width
        self._window_height   = window_height
        self._grid_area_width = window_width - UI_PANEL_WIDTH
        self._grid_area_height = window_height

        if world is not None:
            self._world_cols = world.cols
            self._world_rows = world.rows
            self._tile_size = min(
                self._grid_area_width  / world.cols,
                self._grid_area_height / world.rows,
            )
            self._grid_pixel_width  = self._tile_size * world.cols
            self._grid_pixel_height = self._tile_size * world.rows
            self._grid_offset_x = (self._grid_area_width  - self._grid_pixel_width)  / 2
            self._grid_offset_y = (self._grid_area_height - self._grid_pixel_height) / 2

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def get_tile_pixel_rect(self, col: int, row: int) -> pygame.Rect:
        """Return the pixel rect for tile (col, row)."""
        x = self._grid_offset_x + col * self._tile_size
        y = self._grid_offset_y + row * self._tile_size
        return pygame.Rect(int(x), int(y), int(self._tile_size), int(self._tile_size))

    def get_tile_at_pixel(self, px: float, py: float) -> tuple[int, int] | None:
        """Return (col, row) for the tile under pixel (px, py), or None if outside grid."""
        if self._tile_size == 0:
            return None
        if (px < self._grid_offset_x
                or px >= self._grid_offset_x + self._grid_pixel_width
                or py < self._grid_offset_y
                or py >= self._grid_offset_y + self._grid_pixel_height):
            return None
        col = int((px - self._grid_offset_x) / self._tile_size)
        row = int((py - self._grid_offset_y) / self._tile_size)
        # clamp to valid range (floating-point edge case guard)
        col = max(0, min(col, self._world_cols - 1))
        row = max(0, min(row, self._world_rows - 1))
        return (col, row)

    # ------------------------------------------------------------------
    # Main draw entry point
    # ------------------------------------------------------------------

    def draw_frame(
        self,
        mode,
        world,
        transition_alpha: int,
        scale: float = 1.0,
        # Edit mode state
        selected_tile_type=None,
        selected_traffic_control=None,
        tool: str = "paint",
        hovered_tile=None,
        drag_start=None,
        drag_end=None,
        show_speed_popup: bool = False,
        speed_popup_input: str = "",
        speed_selection_tiles=None,
        # Tooltip state
        hovered_speed_limit=None,
        hovered_tile_type=None,
        tooltip_pos=None,
    ) -> None:
        """Draw one frame.  mode is an AppMode-like enum checked by .name."""
        self._update_animation()

        real_surface = self._surface

        # When zooming during first-half of transition, render to a temp
        # surface of the same size, then scale-blit onto the real surface.
        if scale != 1.0:
            temp = pygame.Surface(real_surface.get_size())
            self._surface = temp
        else:
            temp = None

        # ---- clear --------------------------------------------------------
        self._surface.fill((0, 0, 0))

        # ---- mode dispatch ------------------------------------------------
        name = mode.name if hasattr(mode, "name") else str(mode)

        if name == "STARTUP":
            self._draw_startup()

        elif name == "EDIT":
            if world is not None:
                self._draw_grid(world)
                self._draw_hover_shadow(hovered_tile, selected_tile_type)
                self._draw_selection_rect(drag_start, drag_end)
                self._draw_speed_popup(
                    show_speed_popup,
                    speed_popup_input,
                    speed_selection_tiles or [],
                )
            self._draw_edit_ui(
                world,
                selected_tile_type,
                selected_traffic_control,
                tool,
            )
            self._draw_speed_tooltip(hovered_speed_limit, hovered_tile_type, tooltip_pos)

        elif name == "SIMULATE":
            if world is not None:
                self._draw_grid(world)
            self._draw_ui_placeholder("SIMULATE MODE")

        # ---- scale and blit if needed -------------------------------------
        if temp is not None:
            self._surface = real_surface
            w, h = real_surface.get_size()
            sw = int(w * scale)
            sh = int(h * scale)
            scaled = pygame.transform.scale(temp, (sw, sh))
            x = (w - sw) // 2
            y = (h - sh) // 2
            real_surface.blit(scaled, (x, y))

        # ---- black overlay for fade effect --------------------------------
        if transition_alpha > 0:
            overlay = pygame.Surface(real_surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, max(0, min(255, transition_alpha))))
            real_surface.blit(overlay, (0, 0))

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _update_animation(self) -> None:
        self._anim_offset = (self._anim_offset + self._anim_speed) % _BG_GRID_SIZE
        self._anim_tick  += 1

    # ------------------------------------------------------------------
    # Startup screen
    # ------------------------------------------------------------------

    def _draw_startup(self) -> None:
        surface = self._surface
        w, h = surface.get_size()

        # Background
        surface.fill(COLOR_UI_BACKGROUND)

        # Animated diagonal scrolling grid
        offset = int(self._anim_offset)
        # Horizontal lines
        y = -_BG_GRID_SIZE + (offset % _BG_GRID_SIZE)
        while y < h:
            pygame.draw.line(surface, _BG_LINE_COLOR, (0, y), (w, y), 2)
            y += _BG_GRID_SIZE
        # Vertical lines
        x = -_BG_GRID_SIZE + (offset % _BG_GRID_SIZE)
        while x < w:
            pygame.draw.line(surface, _BG_LINE_COLOR, (x, 0), (x, h), 2)
            x += _BG_GRID_SIZE

        # ---- Title --------------------------------------------------------
        cx = w // 2
        title_y = int(h * 0.25)

        title_surf = self._font_large.render("FlowCity AI", True, COLOR_TEXT_PRIMARY)
        title_rect = title_surf.get_rect(centerx=cx, top=title_y)
        surface.blit(title_surf, title_rect)

        # Accent line — centered in the gap between title and subtitle
        accent_line_y = title_rect.bottom + 12
        pygame.draw.line(
            surface, (120, 120, 180),
            (cx - 60, accent_line_y), (cx + 60, accent_line_y), 2,
        )

        subtitle_surf = self._font_medium.render(
            "Urban Traffic Simulation", True, COLOR_TEXT_PRIMARY
        )
        subtitle_rect = subtitle_surf.get_rect(centerx=cx, top=title_rect.bottom + 24)
        surface.blit(subtitle_surf, subtitle_rect)

        # ---- Buttons ------------------------------------------------------
        btn_w, btn_h = 220, 52
        btn_gap      = 14
        btn_top      = subtitle_rect.bottom + 48

        btn_new_rect  = pygame.Rect(cx - btn_w // 2, btn_top, btn_w, btn_h)
        btn_load_rect = pygame.Rect(cx - btn_w // 2, btn_top + btn_h + btn_gap, btn_w, btn_h)

        # Store for click detection in App
        self._btn_new_map  = btn_new_rect
        self._btn_load_map = btn_load_rect

        mouse_pos = pygame.mouse.get_pos()

        # "New Map" — filled
        new_hover = btn_new_rect.collidepoint(mouse_pos)
        new_color = _brighten(COLOR_UI_ACCENT, 30) if new_hover else COLOR_UI_ACCENT
        pygame.draw.rect(surface, new_color, btn_new_rect, border_radius=8)

        new_label = self._font_medium.render("New Map", True, COLOR_TEXT_PRIMARY)
        surface.blit(new_label, new_label.get_rect(center=btn_new_rect.center))

        # "Load Map" — outline only
        load_hover = btn_load_rect.collidepoint(mouse_pos)
        outline_color = _brighten(COLOR_UI_ACCENT, 30) if load_hover else COLOR_UI_ACCENT
        if load_hover:
            pygame.draw.rect(surface, _brighten(COLOR_UI_ACCENT, 10), btn_load_rect, border_radius=8)
        pygame.draw.rect(surface, outline_color, btn_load_rect, width=2, border_radius=8)

        load_label = self._font_medium.render("Load Map", True, COLOR_TEXT_PRIMARY)
        surface.blit(load_label, load_label.get_rect(center=btn_load_rect.center))

        # ---- Credit line --------------------------------------------------
        credit_surf = self._font_small.render(
            "FlowCity AI — Georgia Tech IE Portfolio Project",
            True,
            COLOR_TEXT_SECONDARY,
        )
        credit_rect = credit_surf.get_rect(centerx=cx, bottom=h - 16)
        surface.blit(credit_surf, credit_rect)

    # ------------------------------------------------------------------
    # Grid
    # ------------------------------------------------------------------

    def _draw_grid(self, world) -> None:
        surface = self._surface
        w = int(self._grid_area_width)
        h = int(self._grid_area_height)

        # Fill the entire grid area with the background void color.
        pygame.draw.rect(surface, COLOR_UI_BACKGROUND, (0, 0, w, h))

        # Extension grid — draw full-area lines aligned with the tile grid so
        # the margin letterbox looks like an infinite continuation of the map.
        # Phase offset ensures lines pass exactly through tile boundaries.
        if self._tile_size > 0:
            ts = self._tile_size

            # Vertical lines: phase from grid origin, covering full area width
            x = self._grid_offset_x % ts
            while x <= self._grid_area_width:
                pygame.draw.line(surface, COLOR_GRID_LINE, (int(x), 0), (int(x), h), 2)
                x += ts

            # Horizontal lines: phase from grid origin, covering full area height
            y = self._grid_offset_y % ts
            while y <= self._grid_area_height:
                pygame.draw.line(surface, COLOR_GRID_LINE, (0, int(y)), (w, int(y)), 2)
                y += ts

        # City tiles on top — tile fill covers the extension lines inside the
        # map boundary; only the margin strips show the bare grid.
        for row in range(world.rows):
            for col in range(world.cols):
                tile = world.get_tile(col, row)
                rect = self.get_tile_pixel_rect(col, row)
                color = TILE_COLORS.get(tile.tile_type, COLOR_EMPTY)
                pygame.draw.rect(surface, color, rect)
                # Right edge only — each shared border drawn exactly once.
                pygame.draw.line(
                    surface, COLOR_GRID_LINE,
                    (rect.right - 1, rect.top),
                    (rect.right - 1, rect.bottom - 1),
                    2,
                )
                # Bottom edge only.
                pygame.draw.line(
                    surface, COLOR_GRID_LINE,
                    (rect.left, rect.bottom - 1),
                    (rect.right - 1, rect.bottom - 1),
                    2,
                )

    # ------------------------------------------------------------------
    # Edit mode overlays (drawn on top of the grid)
    # ------------------------------------------------------------------

    def _draw_hover_shadow(self, hovered_tile, selected_tile_type) -> None:
        """Semi-transparent preview of the selected tile type under the cursor."""
        if hovered_tile is None or selected_tile_type is None:
            return
        col, row = hovered_tile
        rect = self.get_tile_pixel_rect(col, row)
        if rect.width <= 0 or rect.height <= 0:
            return
        base_color = TILE_COLORS.get(selected_tile_type, COLOR_EMPTY)
        shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shadow.fill((*base_color, HOVER_SHADOW_ALPHA))
        self._surface.blit(shadow, rect.topleft)
        # 2px border ring at alpha 160 — marks the hovered tile clearly
        ring = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(ring, (*COLOR_TEXT_PRIMARY, 160), ring.get_rect(), 2)
        self._surface.blit(ring, rect.topleft)

    def _draw_selection_rect(self, drag_start, drag_end) -> None:
        """Yellow rectangle spanning the current drag selection."""
        if drag_start is None or drag_end is None:
            return
        c1, r1 = drag_start
        c2, r2 = drag_end
        col_min, col_max = min(c1, c2), max(c1, c2)
        row_min, row_max = min(r1, r2), max(r1, r2)
        tl = self.get_tile_pixel_rect(col_min, row_min)
        br = self.get_tile_pixel_rect(col_max, row_max)
        sel_rect = pygame.Rect(
            tl.left, tl.top,
            br.right - tl.left,
            br.bottom - tl.top,
        )
        if sel_rect.width <= 0 or sel_rect.height <= 0:
            return
        # Semi-transparent fill
        fill_surf = pygame.Surface((sel_rect.width, sel_rect.height), pygame.SRCALPHA)
        fill_surf.fill(COLOR_SELECTION_FILL)
        self._surface.blit(fill_surf, sel_rect.topleft)
        # Solid border
        pygame.draw.rect(self._surface, COLOR_SELECTION_BORDER, sel_rect, 2)

    def _draw_speed_popup(
        self,
        show: bool,
        input_str: str,
        tiles: list,
    ) -> None:
        """Centered popup card for speed limit input."""
        if not show or not tiles:
            return

        surface = self._surface

        # Find center of selection in screen space
        cols = [c for c, r in tiles]
        rows = [r for c, r in tiles]
        mid_col = (min(cols) + max(cols)) // 2
        mid_row = (min(rows) + max(rows)) // 2
        mid_rect = self.get_tile_pixel_rect(mid_col, mid_row)
        cx_px, cy_px = mid_rect.centerx, mid_rect.centery

        # Popup dimensions
        popup_w, popup_h = 270, 110
        grid_right = int(self._grid_area_width)
        px = max(10, min(cx_px - popup_w // 2, grid_right - popup_w - 10))
        py = max(10, min(cy_px - popup_h // 2, surface.get_height() - popup_h - 10))
        popup_rect = pygame.Rect(px, py, popup_w, popup_h)
        self._speed_popup_rect = popup_rect

        pygame.draw.rect(surface, COLOR_POPUP_BG, popup_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_POPUP_BORDER, popup_rect, 2, border_radius=8)

        # Title
        title_surf = self._font_small.render("Set Speed Limit", True, COLOR_TEXT_PRIMARY)
        surface.blit(title_surf, title_surf.get_rect(
            centerx=popup_rect.centerx, top=popup_rect.top + 10
        ))

        # Input display
        display = input_str if input_str else "___"
        input_surf = self._font_medium.render(display, True, COLOR_TEXT_PRIMARY)
        surface.blit(input_surf, input_surf.get_rect(
            centerx=popup_rect.centerx, top=popup_rect.top + 34
        ))

        # Instruction
        hint_surf = self._font_small.render(
            "Enter → apply    Esc → cancel", True, COLOR_TEXT_SECONDARY
        )
        surface.blit(hint_surf, hint_surf.get_rect(
            centerx=popup_rect.centerx, bottom=popup_rect.bottom - 10
        ))

    def _draw_speed_tooltip(
        self,
        speed_limit,
        tile_type_name: str | None,
        pos,
    ) -> None:
        """Small tooltip above the cursor showing road type and speed limit."""
        if speed_limit is None or tile_type_name is None or pos is None:
            return

        mph  = SPEED_LIMIT_TO_MPH.get(speed_limit, speed_limit)
        text = f"{tile_type_name.capitalize()}  •  {mph} MPH"
        text_surf = self._font_small.render(text, True, COLOR_TEXT_PRIMARY)

        pad_h, pad_v = 8, 5
        tw = text_surf.get_width()  + pad_h * 2
        th = text_surf.get_height() + pad_v * 2

        # Default: above and slightly right of cursor
        tx = pos[0] + 14
        ty = pos[1] - th - 8

        # Clamp to screen bounds
        sw, sh = self._surface.get_size()
        tx = max(4, min(tx, sw - tw - 4))
        ty = max(4, min(ty, sh - th - 4))

        tooltip_rect = pygame.Rect(tx, ty, tw, th)
        pygame.draw.rect(self._surface, (20, 20, 35), tooltip_rect, border_radius=4)
        pygame.draw.rect(self._surface, (100, 100, 150), tooltip_rect, 1, border_radius=4)
        self._surface.blit(text_surf, (tx + pad_h, ty + pad_v))

    # ------------------------------------------------------------------
    # Edit mode UI panel
    # ------------------------------------------------------------------

    def _draw_edit_ui(
        self,
        world,
        selected_tile_type,
        selected_traffic_control,
        tool: str,
    ) -> None:
        """Full right-panel UI for edit mode."""
        surface = self._surface
        sw, sh = surface.get_size()
        panel_x = sw - UI_PANEL_WIDTH
        pad = 10
        inner_w = UI_PANEL_WIDTH - pad * 2
        mouse_pos = pygame.mouse.get_pos()

        # ---- Panel background + separator ---------------------------------
        panel_rect = pygame.Rect(panel_x, 0, UI_PANEL_WIDTH, sh)
        pygame.draw.rect(surface, COLOR_UI_BACKGROUND, panel_rect)
        pygame.draw.line(surface, COLOR_UI_ACCENT, (panel_x, 0), (panel_x, sh), 1)

        cy = pad  # vertical cursor within panel (absolute y)

        # ==================================================================
        # TOOL TOOLBAR
        # ==================================================================
        btn_w  = (inner_w - 6) // 2
        btn_h  = 32
        pill_r = btn_h // 2

        paint_rect  = pygame.Rect(panel_x + pad,              cy, btn_w, btn_h)
        select_rect = pygame.Rect(panel_x + pad + btn_w + 6,  cy, btn_w, btn_h)
        self._btn_tool_paint  = paint_rect
        self._btn_tool_select = select_rect

        for rect, label, mode_key in (
            (paint_rect,  "Paint",  "paint"),
            (select_rect, "Select", "select"),
        ):
            active = (tool == mode_key)
            hover  = rect.collidepoint(mouse_pos)
            if active:
                fill_color = _brighten(COLOR_UI_ACCENT, 20) if hover else COLOR_UI_ACCENT
                # Soft glow — three inflated filled rects at decreasing alpha
                for inflate, alpha in ((3, 40), (2, 25), (1, 12)):
                    glow = pygame.Surface(
                        (rect.width + inflate * 2, rect.height + inflate * 2),
                        pygame.SRCALPHA,
                    )
                    pygame.draw.rect(
                        glow,
                        (*fill_color, alpha),
                        pygame.Rect(0, 0, rect.width + inflate * 2, rect.height + inflate * 2),
                        border_radius=pill_r + inflate,
                    )
                    surface.blit(glow, (rect.x - inflate, rect.y - inflate))
                pygame.draw.rect(surface, fill_color, rect, border_radius=pill_r)
                lbl = self._font_small.render(label, True, COLOR_TEXT_PRIMARY)
            else:
                border_col = _brighten(COLOR_UI_ACCENT, 20) if hover else COLOR_UI_ACCENT
                if hover:
                    pygame.draw.rect(
                        surface, _brighten(COLOR_UI_BACKGROUND, 10), rect,
                        border_radius=pill_r,
                    )
                pygame.draw.rect(surface, border_col, rect, 1, border_radius=pill_r)
                lbl = self._font_small.render(
                    label, True, COLOR_TEXT_PRIMARY if hover else COLOR_TEXT_SECONDARY,
                )
            surface.blit(lbl, lbl.get_rect(center=rect.center))

        cy += btn_h + 10

        # ==================================================================
        # TILE TYPE SECTION
        # ==================================================================
        cy = self._draw_section_header(surface, "TILE TYPE", panel_x, pad, inner_w, cy)

        swatch_h      = 44
        swatch_w      = (inner_w - 6) // 2
        color_block_h = 28
        label_strip_h = swatch_h - color_block_h
        pulse_v = int(180 + abs(math.sin(self._anim_tick * 0.05)) * 75)

        self._palette_tile_rects = {}

        for i, (type_name, label) in enumerate(PALETTE_TILE_ENTRIES):
            tile_type = TileType[type_name]
            col_idx = i % 2
            row_idx = i // 2
            sx = panel_x + pad + col_idx * (swatch_w + 6)
            sy = cy + row_idx * (swatch_h + 4)
            rect = pygame.Rect(sx, sy, swatch_w, swatch_h)
            self._palette_tile_rects[tile_type] = rect

            base_color = TILE_COLORS[tile_type]
            hover = rect.collidepoint(mouse_pos)
            fill  = _brighten(base_color, 20) if hover else base_color

            # Color block — top portion
            color_block = pygame.Rect(sx, sy, swatch_w, color_block_h)
            pygame.draw.rect(surface, fill, color_block, border_radius=4)

            # Label strip — bottom portion, slightly darker
            strip_color = (
                max(0, fill[0] - 25),
                max(0, fill[1] - 25),
                max(0, fill[2] - 25),
            )
            label_strip = pygame.Rect(sx, sy + color_block_h, swatch_w, label_strip_h)
            pygame.draw.rect(
                surface, strip_color, label_strip,
                border_bottom_left_radius=4, border_bottom_right_radius=4,
            )

            # Selection / hover border
            selected = (tile_type == selected_tile_type)
            if selected:
                pygame.draw.rect(
                    surface, (pulse_v, pulse_v, pulse_v), rect, 2, border_radius=4,
                )
            else:
                pygame.draw.rect(surface, COLOR_UI_ACCENT, rect, 1, border_radius=4)

            # Label centered in the strip
            lbl_surf = self._font_small.render(label, True, COLOR_TEXT_PRIMARY)
            surface.blit(lbl_surf, lbl_surf.get_rect(
                centerx=sx + swatch_w // 2,
                centery=sy + color_block_h + label_strip_h // 2,
            ))

        cy += 3 * (swatch_h + 4) + 6

        # ==================================================================
        # TRAFFIC CONTROL SECTION
        # ==================================================================
        cy = self._draw_section_header(surface, "TRAFFIC CONTROL", panel_x, pad, inner_w, cy)

        tc_count = len(PALETTE_TRAFFIC_ENTRIES)
        tc_w = (inner_w - (tc_count - 1) * 5) // tc_count
        tc_h = 50

        self._palette_traffic_rects = {}

        for i, (tc_name, tc_label) in enumerate(PALETTE_TRAFFIC_ENTRIES):
            tc = TrafficControl[tc_name]
            tx = panel_x + pad + i * (tc_w + 5)
            ty = cy
            rect = pygame.Rect(tx, ty, tc_w, tc_h)
            self._palette_traffic_rects[tc] = rect

            hover = rect.collidepoint(mouse_pos)
            bg = _brighten(COLOR_UI_BACKGROUND, 15) if hover else _brighten(COLOR_UI_BACKGROUND, 8)
            pygame.draw.rect(surface, bg, rect, border_radius=4)

            selected_tc = (tc == selected_traffic_control)
            border_col = COLOR_TEXT_PRIMARY if selected_tc else COLOR_UI_ACCENT
            border_w = 2 if selected_tc else 1
            pygame.draw.rect(surface, border_col, rect, border_w, border_radius=4)

            # Icon
            icon_cy = rect.top + rect.height // 2 - 6
            icon_cx = rect.centerx
            if tc == TrafficControl.none:
                # Two short horizontal dashes
                for dy in (-3, 3):
                    pygame.draw.line(surface, COLOR_TEXT_SECONDARY,
                                     (icon_cx - 8, icon_cy + dy),
                                     (icon_cx + 8, icon_cy + dy), 2)
            elif tc == TrafficControl.stop_sign:
                # Small red octagon approximated as a rotated square
                r = 7
                pts = [
                    (icon_cx - 3, icon_cy - r),
                    (icon_cx + 3, icon_cy - r),
                    (icon_cx + r, icon_cy - 3),
                    (icon_cx + r, icon_cy + 3),
                    (icon_cx + 3, icon_cy + r),
                    (icon_cx - 3, icon_cy + r),
                    (icon_cx - r, icon_cy + 3),
                    (icon_cx - r, icon_cy - 3),
                ]
                pygame.draw.polygon(surface, (180, 40, 40), pts)
                stop = self._font_small.render("STOP", True, COLOR_TEXT_PRIMARY)
                # Scale down to fit
                scaled = pygame.transform.scale(stop, (stop.get_width() * 9 // 14, stop.get_height() * 9 // 14))
                surface.blit(scaled, scaled.get_rect(center=(icon_cx, icon_cy)))
            elif tc == TrafficControl.traffic_light:
                # Dark housing
                housing = pygame.Rect(icon_cx - 5, icon_cy - 9, 10, 18)
                pygame.draw.rect(surface, (30, 30, 30), housing, border_radius=2)
                # Three circles: red / yellow / green
                for circle_i, circle_col in enumerate(
                    [(200, 50, 50), (200, 180, 50), (50, 180, 50)]
                ):
                    cy_circle = icon_cy - 6 + circle_i * 6
                    pygame.draw.circle(surface, circle_col, (icon_cx, cy_circle), 2)

            # Short label below icon
            short_lbl = self._font_small.render(tc_label.split()[0], True, COLOR_TEXT_SECONDARY)
            surface.blit(short_lbl, short_lbl.get_rect(
                centerx=rect.centerx, bottom=rect.bottom - 3
            ))

        cy += tc_h + 8

        # ==================================================================
        # LEGEND SECTION
        # ==================================================================
        cy = self._draw_section_header(surface, "LEGEND", panel_x, pad, inner_w, cy)

        legend_col_w = inner_w // 2
        legend_row_h = 16
        for i, (type_name, label) in enumerate(PALETTE_TILE_ENTRIES):
            tile_type = TileType[type_name]
            col_idx = i % 2
            row_idx = i // 2
            lx = panel_x + pad + col_idx * legend_col_w
            ly = cy + row_idx * legend_row_h
            # Color square
            pygame.draw.rect(surface, TILE_COLORS[tile_type], (lx, ly + 3, 8, 8))
            pygame.draw.rect(surface, COLOR_UI_ACCENT, (lx, ly + 3, 8, 8), 1)
            # Label
            lbl = self._font_small.render(label, True, COLOR_TEXT_SECONDARY)
            surface.blit(lbl, (lx + 11, ly))

        cy += 3 * legend_row_h + 8

        # ==================================================================
        # INFO
        # ==================================================================
        info_lines = []
        if world is not None:
            info_lines.append(f"Grid: {world.cols} × {world.rows}")
        info_lines.append(f"Tool: {tool.capitalize()}")
        if selected_tile_type is not None:
            info_lines.append(f"Paint: {selected_tile_type.name.capitalize()}")

        for line in info_lines:
            lbl = self._font_small.render(line, True, COLOR_TEXT_PRIMARY)
            surface.blit(lbl, (panel_x + pad, cy))
            cy += 18
        cy += 6

        # ==================================================================
        # ACTION BUTTONS
        # ==================================================================
        action_btn_h = 34
        sim_btn_h    = 38
        action_gap   = 6
        action_w     = inner_w

        save_rect = pygame.Rect(panel_x + pad, cy, action_w, action_btn_h)
        load_rect = pygame.Rect(
            panel_x + pad, cy + action_btn_h + action_gap, action_w, action_btn_h,
        )
        sim_rect  = pygame.Rect(
            panel_x + pad,
            cy + 2 * (action_btn_h + action_gap) + 4,
            action_w, sim_btn_h,
        )

        self._btn_save      = save_rect
        self._btn_load      = load_rect
        self._btn_start_sim = sim_rect

        # Save / Load — outline buttons
        for rect, label in ((save_rect, "Save Map"), (load_rect, "Load Map")):
            hover  = rect.collidepoint(mouse_pos)
            border = _brighten(COLOR_UI_ACCENT, 25) if hover else COLOR_UI_ACCENT
            if hover:
                pygame.draw.rect(
                    surface, _brighten(COLOR_UI_BACKGROUND, 20), rect, border_radius=5,
                )
            pygame.draw.rect(surface, border, rect, 1, border_radius=5)
            lbl = self._font_small.render(
                label, True, COLOR_TEXT_PRIMARY if hover else COLOR_TEXT_SECONDARY,
            )
            surface.blit(lbl, lbl.get_rect(center=rect.center))

        # Start Simulation — filled accent button, taller, medium font
        sim_hover = sim_rect.collidepoint(mouse_pos)
        sim_bg    = _brighten(COLOR_UI_ACCENT, 40) if sim_hover else _brighten(COLOR_UI_ACCENT, 20)
        pygame.draw.rect(surface, sim_bg, sim_rect, border_radius=6)
        # 1px inner top-edge highlight
        hl = _brighten(sim_bg, 50)
        pygame.draw.line(
            surface, hl,
            (sim_rect.left + 8,  sim_rect.top + 1),
            (sim_rect.right - 8, sim_rect.top + 1),
            1,
        )
        sim_lbl = self._font_medium.render("Start Simulation", True, COLOR_TEXT_PRIMARY)
        surface.blit(sim_lbl, sim_lbl.get_rect(center=sim_rect.center))

        cy += 2 * (action_btn_h + action_gap) + 4 + sim_btn_h + 8

        # ==================================================================
        # SHORTCUTS HINT
        # ==================================================================
        cy = self._draw_section_header(surface, "SHORTCUTS", panel_x, pad, inner_w, cy)
        shortcuts = [
            "1-6: Tile types   E: Erase",
            "Tab: Switch tool",
            "S: Save   L: Load",
            "Enter: Simulate",
        ]
        for line in shortcuts:
            lbl = self._font_small.render(line, True, COLOR_TEXT_SECONDARY)
            surface.blit(lbl, (panel_x + pad, cy))
            cy += 15

    # ------------------------------------------------------------------
    # UI panel placeholder (used by SIMULATE mode)
    # ------------------------------------------------------------------

    def _draw_ui_placeholder(self, label: str) -> None:
        surface = self._surface
        w, h = surface.get_size()
        panel_rect = pygame.Rect(w - UI_PANEL_WIDTH, 0, UI_PANEL_WIDTH, h)

        pygame.draw.rect(surface, COLOR_UI_BACKGROUND, panel_rect)
        # Vertical separator
        pygame.draw.line(
            surface,
            COLOR_UI_ACCENT,
            (panel_rect.left, 0),
            (panel_rect.left, h),
            1,
        )
        # Label centered in panel
        label_surf = self._font_medium.render(label, True, COLOR_TEXT_SECONDARY)
        label_rect = label_surf.get_rect(center=panel_rect.center)
        surface.blit(label_surf, label_rect)

    # ------------------------------------------------------------------
    # Private layout helpers
    # ------------------------------------------------------------------

    def _draw_section_header(
        self,
        surface: pygame.Surface,
        text: str,
        panel_x: int,
        pad: int,
        inner_w: int,
        cy: int,
    ) -> int:
        """Draw a thin accent line + uppercase section label. Returns updated cy."""
        cy += 8
        pygame.draw.line(
            surface, _brighten(COLOR_UI_ACCENT, 20),
            (panel_x + pad, cy), (panel_x + pad + inner_w, cy), 1
        )
        cy += 2
        lbl = self._font_small.render(text, True, _brighten(COLOR_TEXT_SECONDARY, 20))
        surface.blit(lbl, (panel_x + pad, cy))
        cy += lbl.get_height() + 4
        return cy


# ---------------------------------------------------------------------------
# Module-level private helpers
# ---------------------------------------------------------------------------

def _brighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    """Return color with each channel increased by amount, clamped to 255."""
    return (
        min(255, color[0] + amount),
        min(255, color[1] + amount),
        min(255, color[2] + amount),
    )
