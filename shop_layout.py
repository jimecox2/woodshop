# shop_layout.py — Woodworking Shop Layout, FreeCAD Python Console script
# Phase 1: Room shell, door, joists, electrical panel
# Paste entire file into: View → Panels → Python Console

import FreeCAD as App
import FreeCADGui as Gui
import Part
import math
from FreeCAD import Vector

# ── Helpers ──────────────────────────────────────────────────────────────────
def inch(n):       return n * 25.4
def ft(f, i=0):   return (f * 12 + i) * 25.4

# ── Document ──────────────────────────────────────────────────────────────────
DOC = "WoodshopLayout"
if DOC in App.listDocuments():
    App.closeDocument(DOC)
doc = App.newDocument(DOC)

# =============================================================================
# ROOM GEOMETRY  (mm, X=East, Y=North, Z=Up, origin = SW interior corner)
# =============================================================================
#
#  NW(0, 22') ──────────────────── NE(11', 22')
#     |                                  |
#     | West wall 22' concrete      East upper 6'6"
#     |                                  |
#     |                             ╱  ← ~45° jut
#     |                           ╱
#     |                      East lower 12'6"
#     |                          |
#  SW(0,0) ──────────── SE(7'8", 0)
#          South 7'8" concrete
#
# Jut maths: lower(12'6") + jut_Δy + upper(6'6") must equal west(22')
#   jut_Δy = 22' - 12'6" - 6'6" = 3' = 914.4 mm
#   jut_Δx = 11' - 7'8"        = 3'4" = 1016.0 mm  → ~48° (real world)

X_W          = 0
X_SE         = ft(7, 8)          # 2 336.8 mm
X_NE         = ft(11)            # 3 352.8 mm

Y_S          = 0
Y_N          = ft(22)            # 6 705.6 mm
Y_JUT_BOT    = ft(12, 6)         # 3 810.0 mm  — bottom of jut (east lower top)
Y_JUT_TOP    = Y_N - ft(6, 6)    # 4 724.4 mm  — top of jut (east upper bottom)

# Wall thicknesses
T_FRAME   = inch(4.5)   # 2×4 stud + drywall (north wall)
T_CONC    = inch(8)     # concrete (west, south, east walls)

# Heights
H_LOWER_BOT = inch(81)              # underside of lower joists (south zone)
H_JOIST     = inch(12)              # joist depth = 1 ft
H_ROOM      = H_LOWER_BOT + H_JOIST # wall height to top of joist  = 93"

# Door (north wall, 6" from east end, 36" wide × 80" tall)
DOOR_W  = inch(36)
DOOR_H  = inch(80)
DOOR_X2 = X_NE  - inch(6)          # east edge of door opening
DOOR_X1 = DOOR_X2 - DOOR_W         # west edge

# =============================================================================
# UTILITY
# =============================================================================
def box(name, x, y, z, dx, dy, dz, color=(0.8, 0.8, 0.75), transp=10):
    """Add a Part::Box at position (x,y,z) with size (dx,dy,dz)."""
    o = doc.addObject("Part::Box", name)
    o.Placement = App.Placement(Vector(x, y, z), App.Rotation())
    o.Length = dx   # X
    o.Width  = dy   # Y
    o.Height = dz   # Z
    o.ViewObject.ShapeColor   = color
    o.ViewObject.Transparency = transp
    return o

def part_feat(name, shape, color=(0.8, 0.8, 0.75), transp=10):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor   = color
    o.ViewObject.Transparency = transp
    return o

C_CONC    = (0.72, 0.70, 0.65)
C_FRAME   = (0.94, 0.91, 0.85)
C_JOIST   = (0.76, 0.60, 0.42)
C_PANEL   = (0.25, 0.35, 0.70)
C_DOOR    = (0.55, 0.35, 0.15)
C_FLOOR   = (0.50, 0.50, 0.48)

# =============================================================================
# FLOOR SLAB (4" concrete below Z=0)
# =============================================================================
floor_pts = [
    Vector(X_W,  Y_S,        0),
    Vector(X_SE, Y_S,        0),
    Vector(X_SE, Y_JUT_BOT,  0),
    Vector(X_NE, Y_JUT_TOP,  0),
    Vector(X_NE, Y_N,        0),
    Vector(X_W,  Y_N,        0),
    Vector(X_W,  Y_S,        0),   # close
]
floor_wire  = Part.makePolygon(floor_pts)
floor_face  = Part.Face(floor_wire)
floor_solid = floor_face.extrude(Vector(0, 0, -inch(4)))
floor_obj   = part_feat("Floor", floor_solid, color=C_FLOOR, transp=20)

# =============================================================================
# WALLS
# =============================================================================
# South wall — concrete, exterior face at Y = -T_CONC
south_wall = box("Wall_South",
    X_W, Y_S - T_CONC, 0,
    X_SE, T_CONC, H_ROOM,
    color=C_CONC)

# West wall — concrete, exterior face at X = -T_CONC
# Spans full north-south including corner overlaps
west_wall = box("Wall_West",
    X_W - T_CONC, Y_S - T_CONC, 0,
    T_CONC, Y_N + T_CONC + T_FRAME, H_ROOM,
    color=C_CONC)

# North wall — 2×4 + drywall, interior face at Y = Y_N
# Split into three pieces around door opening
# West piece
nw_west = box("Wall_North_West",
    X_W, Y_N, 0,
    DOOR_X1 - X_W, T_FRAME, H_ROOM,
    color=C_FRAME)

# East piece (6" stub between door and east corner)
nw_east = box("Wall_North_East",
    DOOR_X2, Y_N, 0,
    X_NE - DOOR_X2, T_FRAME, H_ROOM,
    color=C_FRAME)

# Header above door opening
nw_header = box("Wall_North_Header",
    DOOR_X1, Y_N, DOOR_H,
    DOOR_W, T_FRAME, H_ROOM - DOOR_H,
    color=C_FRAME)

# East wall — lower vertical section (concrete)
east_lower = box("Wall_East_Lower",
    X_SE, Y_S, 0,
    T_CONC, Y_JUT_BOT - Y_S, H_ROOM,
    color=C_CONC)

# East wall — upper vertical section (concrete)
east_upper = box("Wall_East_Upper",
    X_NE, Y_JUT_TOP, 0,
    T_CONC, Y_N - Y_JUT_TOP, H_ROOM,
    color=C_CONC)

# East wall — 45° jut section (concrete)
# Inner face: (X_SE, Y_JUT_BOT) → (X_NE, Y_JUT_TOP)
# Outer face offset perpendicular outward by T_CONC
jx = X_NE - X_SE
jy = Y_JUT_TOP - Y_JUT_BOT
jlen = math.sqrt(jx**2 + jy**2)
nx = jy / jlen   # outward normal X component
ny = -jx / jlen  # outward normal Y component

j_p1 = Vector(X_SE,              Y_JUT_BOT,              0)
j_p2 = Vector(X_NE,              Y_JUT_TOP,              0)
j_p3 = Vector(X_NE + nx*T_CONC, Y_JUT_TOP + ny*T_CONC, 0)
j_p4 = Vector(X_SE + nx*T_CONC, Y_JUT_BOT + ny*T_CONC, 0)

jut_face  = Part.Face(Part.makePolygon([j_p1, j_p2, j_p3, j_p4, j_p1]))
jut_solid = jut_face.extrude(Vector(0, 0, H_ROOM))
east_jut  = part_feat("Wall_East_Jut", jut_solid, color=C_CONC)

# =============================================================================
# DOOR (simple box placeholder in opening)
# =============================================================================
door_obj = box("Door_North",
    DOOR_X1, Y_N, 0,
    DOOR_W, inch(1.75), DOOR_H,
    color=C_DOOR, transp=0)

# =============================================================================
# JOIST SYSTEM
# =============================================================================
# Joists: wooden I-beam, modelled as 3.5" wide × 12" deep rectangular beam
# Underside of ALL joists at Z = H_LOWER_BOT = 81"
# 16" on-centre spacing

JOIST_W   = inch(3.5)
JOIST_SPC = inch(16)

# ── Lower joists (south zone, Y = 6" to ≤7' from south wall) ─────────────────
lower_joist_objs = []
y = inch(6)
idx = 1
while y <= ft(7) + inch(0.5):          # include joist exactly at 7'
    # X extent: full width of south section
    def _x_at_y(yy):
        if yy <= Y_JUT_BOT:   return X_SE
        elif yy <= Y_JUT_TOP:
            t = (yy - Y_JUT_BOT) / (Y_JUT_TOP - Y_JUT_BOT)
            return X_SE + t * (X_NE - X_SE)
        else:                  return X_NE

    x_end = _x_at_y(y)
    o = box(f"LowerJoist_{idx:02d}",
        X_W, y - JOIST_W/2, H_LOWER_BOT,
        x_end - X_W, JOIST_W, H_JOIST,
        color=C_JOIST)
    lower_joist_objs.append(o)
    y   += JOIST_SPC
    idx += 1

last_lower_y = y - JOIST_SPC   # actual Y of last lower joist

# ── Main ceiling joists (from 7' northward, plus 2 shown south of south wall) ─
# Continue 16" OC from last lower joist position northward; also 2 joists
# shown extending south below Y_S (representing floor system beyond this room).

main_joist_objs = []
# Two reference joists south of south wall
for k in (2, 1):
    yy = Y_S - k * JOIST_SPC
    o  = box(f"MainJoist_S{k:02d}",
        X_W, yy - JOIST_W/2, H_LOWER_BOT,
        X_SE - X_W, JOIST_W, H_JOIST,
        color=C_JOIST, transp=40)
    main_joist_objs.append(o)

# Main joists from (last_lower_y + JOIST_SPC) through north wall + 2 beyond
y   = last_lower_y + JOIST_SPC
idx = 1
while y <= Y_N + 2 * JOIST_SPC + inch(0.5):
    x_end = _x_at_y(y)
    # Joists beyond north wall shown at full-north-width for context
    if y > Y_N:
        x_end = X_NE
    o = box(f"MainJoist_{idx:02d}",
        X_W, y - JOIST_W/2, H_LOWER_BOT,
        x_end - X_W, JOIST_W, H_JOIST,
        color=C_JOIST)
    main_joist_objs.append(o)
    y   += JOIST_SPC
    idx += 1

# =============================================================================
# ELECTRICAL PANEL
# =============================================================================
# West wall, surface-mounted on interior face (X=0), extending into room +8"
# 16" wide × 28" tall, bottom at 38" AFF
# "2 feet from north wall" → top of panel 2' from north wall interior face
#   top_Y = Y_N - ft(2);  bottom_Y = top_Y - inch(16)
panel_top_y = Y_N - ft(2)
panel_bot_y = panel_top_y - inch(16)
panel_obj = box("ElectricalPanel",
    X_W, panel_bot_y, inch(38),
    inch(8), inch(16), inch(28),
    color=C_PANEL, transp=0)

# =============================================================================
# TOOLS — West wall, south of electrical panel
# =============================================================================
# Coordinate reminders: X=East (depth from west wall), Y=North, Z=Up
# Panel bottom face is at panel_bot_y; tools run south from there.

C_TOOL   = (0.25, 0.25, 0.30)   # dark steel / cast iron
C_TOPTBL = (0.48, 0.48, 0.53)   # cast-iron table surface

# ── Band Saw ──────────────────────────────────────────────────────────────────
# Floor-mount on wheels, 6' tall overall
# Base footprint: 24" deep (into room, X) × 18" wide (along wall, Y)
# Table: 21-3/8" × 15-5/8" tilting, at ~40" AFF
# Positioned against west wall, 6" south of panel bottom

BS_GAP  = inch(6)
BS_DX   = inch(24)         # depth from west wall into room
BS_DY   = inch(18)         # width along west wall
BS_DZ   = inch(72)         # 6' overall height (incl. wheels)
BS_X    = X_W              # flush against west wall (interior face)
BS_Y    = panel_bot_y - BS_GAP - BS_DY   # south face of saw footprint

# Main body — column + housing
bs_body = box("BandSaw_Body",
    BS_X, BS_Y, 0,
    BS_DX, BS_DY, BS_DZ,
    color=C_TOOL, transp=0)

# Tilting table — centred on body at 40" AFF, 1.5" thick
BS_TW = inch(21 + 3/8)     # 21-3/8" (E-W, sticks out from body)
BS_TD = inch(15 + 5/8)     # 15-5/8" (N-S)
BS_TZ = inch(40)            # table surface height AFF
BS_TT = inch(1.5)           # table slab thickness

bs_table = box("BandSaw_Table",
    BS_X + (BS_DX - BS_TW) / 2,
    BS_Y + (BS_DY - BS_TD) / 2,
    BS_TZ,
    BS_TW, BS_TD, BS_TT,
    color=C_TOPTBL, transp=0)

west_wall_objs = [bs_body, bs_table]

# =============================================================================
# DRILL PRESS — west wall, 6" south of band saw
# =============================================================================
# Floor-standing, 18" × 18" base, 66" overall height
# Column 6"×6" centred on base; head 18" wide × 14" deep at ~52" AFF

DP_GAP  = inch(6)
DP_DX   = inch(18)          # base depth into room (E-W)
DP_DY   = inch(18)          # base width along wall (N-S)
DP_Y1   = BS_Y - DP_GAP - DP_DY   # south face of base

dp_base = box("DrillPress_Base",
    X_W, DP_Y1, 0,
    DP_DX, DP_DY, inch(4),
    color=C_TOOL, transp=0)

dp_col = box("DrillPress_Column",
    X_W + inch(6), DP_Y1 + inch(6), inch(4),
    inch(6), inch(6), inch(58),
    color=C_TOOL, transp=0)

dp_head = box("DrillPress_Head",
    X_W, DP_Y1 + inch(2), inch(52),
    DP_DX, DP_DY - inch(4), inch(14),
    color=C_TOOL, transp=0)

west_wall_objs += [dp_base, dp_col, dp_head]

# =============================================================================
# CHOP SAW STATION — east lower wall, Y=1' to Y=7'
# =============================================================================
# 24"-deep bench runs 6' along east wall. Saw centred at Y=4'.
# Provides 3' of built-in support each side; roller stand at each end
# gives full 8'-board clearance without leaving the station.

C_BENCH = (0.55, 0.40, 0.25)   # bench-top wood colour

CS_Y1 = ft(1)                   # south end (1' from south wall)
CS_Y2 = ft(7)                   # north end
CS_DY = CS_Y2 - CS_Y1           # 6' long
CS_DX = inch(24)                # 24" deep from east wall
CS_X2 = X_SE
CS_X1 = X_SE - CS_DX

# Bench carcass (34" tall)
cs_bench = box("ChopSaw_Bench",
    CS_X1, CS_Y1, 0,
    CS_DX, CS_DY, inch(34),
    color=C_FRAME, transp=15)

# Bench top — 1.5" hardwood/MDF surface
cs_top = box("ChopSaw_BenchTop",
    CS_X1, CS_Y1, inch(34),
    CS_DX, CS_DY, inch(1.5),
    color=C_BENCH, transp=0)

# Miter saw body — centred on bench at Y=4', sitting on bench top
# Approx. 20" wide × 15" deep × 14" tall (head at rest / lowered)
CS_SAW_W = inch(20)
CS_SAW_D = inch(15)
cs_saw = box("ChopSaw_Saw",
    CS_X1 + (CS_DX - CS_SAW_W) / 2,
    ft(4) - CS_SAW_D / 2,
    inch(35.5),
    CS_SAW_W, CS_SAW_D, inch(14),
    color=C_TOOL, transp=0)

chop_objs = [cs_bench, cs_top, cs_saw]

# =============================================================================
# THICKNESS PLANER — east lower wall, 6" north of chop saw bench
# =============================================================================
# DeWalt 735-class: 22" wide (N-S) × 24" deep (E-W) × 18" machine body.
# On a stand + wheels: ~48" total height. Sits against east wall when stored;
# rolls into open centre for use (8'+ infeed/outfeed available there).

TP_GAP = inch(6)
TP_Y1  = CS_Y2 + TP_GAP         # south face
TP_DY  = inch(22)               # N-S footprint
TP_DX  = inch(24)               # E-W depth (against wall)
TP_X1  = X_SE - TP_DX

tp_body = box("Planer_Body",
    TP_X1, TP_Y1, 0,
    TP_DX, TP_DY, inch(48),
    color=C_TOOL, transp=0)

# Infeed/outfeed table suggestion (lighter, semi-transparent)
tp_tables = box("Planer_Tables",
    TP_X1 - inch(10), TP_Y1, inch(44),
    TP_DX + inch(20), TP_DY, inch(2),
    color=C_TOPTBL, transp=30)

planer_objs = [tp_body, tp_tables]

# =============================================================================
# TABLE SAW — floating in wider north zone
# =============================================================================
# Cabinet saw: 22" E-W × 27" N-S, table surface at 34" AFF.
# Blade at X≈4' from west wall; extension table 36" to the east (right/fence side).
# South face at Y=13' → infeed clearance 13', outfeed to north wall = 9'.
# At Y=13' the east wall is at X≈8'2", well clear of the 36" extension.
# Workflow: feed south→north, offcuts go east past fence into clear zone.

TS_Y1 = ft(13)                  # south face
TS_DY = inch(27)                # N-S depth of cabinet
TS_X1 = inch(36)                # 3' from west wall (left side of cabinet)
TS_DX = inch(22)                # cabinet E-W width  (blade at X≈47")
TS_DZ = inch(34)                # table surface AFF

# Cabinet body
ts_cab = box("TableSaw_Cabinet",
    TS_X1, TS_Y1, 0,
    TS_DX, TS_DY, TS_DZ,
    color=C_TOOL, transp=0)

# Cast-iron table surface (1.5" thick)
ts_top = box("TableSaw_Top",
    TS_X1, TS_Y1, TS_DZ,
    TS_DX, TS_DY, inch(1.5),
    color=C_TOPTBL, transp=0)

# Right extension table — 36" east of cabinet (fence side)
ts_ext = box("TableSaw_Extension",
    TS_X1 + TS_DX, TS_Y1, TS_DZ,
    inch(36), TS_DY, inch(1.5),
    color=C_TOPTBL, transp=15)

# Outfeed roller stand hint — 4' north of blade, centred on cabinet
ts_roller = box("TableSaw_RollerStand",
    TS_X1 + inch(4), TS_Y1 + TS_DY + ft(4), TS_DZ - inch(2),
    inch(14), inch(14), inch(2),
    color=(0.6, 0.6, 0.6), transp=20)

tablesaw_objs = [ts_cab, ts_top, ts_ext, ts_roller]

# =============================================================================
# NORTH WALL STORAGE
# =============================================================================
# Lower cabinets: 15" deep × 7' tall, full width of north wall.
# Gap reserved at door (east 3'6") so cabinets stop at door frame.
# Lumber rack above: wall-mounted brackets at 6'6" AFF, 8" deep.
# Stores 8' boards horizontally (shown as a representative mass).

C_STORAGE = C_FRAME             # same pale wood tone as framing
C_LUMBER  = C_JOIST             # warm wood for stored lumber

NC_DY = inch(15)                # cabinet depth (N-S, from north wall)
NC_DZ = inch(84)                # 7' tall

# West cabinet run: X=0 to X=7' (stops before door zone)
nc_west = box("Storage_CabWest",
    X_W, Y_N - NC_DY, 0,
    ft(7), NC_DY, NC_DZ,
    color=C_STORAGE, transp=20)

# East cabinet run: door is at DOOR_X1 to DOOR_X2, so stop at DOOR_X1
# (east stub between door and east corner is only 6" — skip it)
nc_east_w = X_W                 # same as DOOR_X1 adjusted below
nc_east = box("Storage_CabEast",
    ft(7), Y_N - NC_DY, 0,
    DOOR_X1 - ft(7), NC_DY, NC_DZ,
    color=C_STORAGE, transp=20)

# Lumber rack — wall-mounted at 6'6" AFF, 8" deep, full usable width
# (stops 3' from east corner to keep door clearance)
LR_Z1  = inch(78)              # bottom of lumber stack (6'6" AFF)
LR_DZ  = inch(10)              # rack height (a course of boards)
LR_DY  = inch(8)               # bracket depth from wall

lr_rack = box("LumberRack",
    X_W, Y_N - LR_DY, LR_Z1,
    X_NE - ft(3), LR_DY, LR_DZ,
    color=C_LUMBER, transp=25)

storage_objs = [nc_west, nc_east, lr_rack]

# =============================================================================
# GROUPS
# =============================================================================
def grp(name, objs):
    g = doc.addObject("App::DocumentObjectGroup", name)
    g.addObjects([o for o in objs if o is not None])
    return g

grp("Grp_Floor",      [floor_obj])
grp("Grp_Walls",      [south_wall, west_wall,
                       nw_west, nw_east, nw_header,
                       east_lower, east_upper, east_jut])
grp("Grp_Door",       [door_obj])
grp("Grp_Joists",     lower_joist_objs + main_joist_objs)
grp("Grp_Electrical", [panel_obj])
grp("Grp_Tools_West", west_wall_objs)
grp("Grp_Tools_East", chop_objs + planer_objs + tablesaw_objs)
grp("Grp_Storage",    storage_objs)

# =============================================================================
# FINALISE
# =============================================================================
doc.recompute()
Gui.activeDocument().activeView().viewIsometric()
Gui.SendMsgToActiveView("ViewFit")

print("=" * 60)
print("Woodshop Layout — Full Tool Layout")
print("=" * 60)
print(f"  Room extents  : {X_NE/25.4/12:.2f}' E  x  {Y_N/25.4/12:.2f}' N")
print(f"  Joist underside: {H_LOWER_BOT/25.4:.0f}\" AFF")
print("─" * 60)
print("  WEST WALL (south → north)")
print(f"    Drill press   : Y={DP_Y1/25.4/12:.2f}' – {(DP_Y1+DP_DY)/25.4/12:.2f}'  (18\"×18\" base)")
print(f"    Band saw      : Y={BS_Y/25.4/12:.2f}' – {(BS_Y+BS_DY)/25.4/12:.2f}'  (24\"×18\" on wheels)")
print(f"    Elec. panel   : Y={panel_bot_y/25.4/12:.2f}' – {panel_top_y/25.4/12:.2f}'")
print("─" * 60)
print("  EAST WALL (south → north)")
print(f"    Chop saw stn  : Y={CS_Y1/25.4/12:.2f}' – {CS_Y2/25.4/12:.2f}'  (6' bench, 24\" deep)")
print(f"    Thickness plnr: Y={TP_Y1/25.4/12:.2f}' – {(TP_Y1+TP_DY)/25.4/12:.2f}'  (on wheels)")
print(f"    Assembly zone : Y=~{(TP_Y1+TP_DY)/25.4/12:.1f}' – {TS_Y1/25.4/12:.1f}'  (open floor)")
print("─" * 60)
print("  TABLE SAW (floating)")
print(f"    Cabinet       : X={TS_X1/25.4/12:.2f}' – {(TS_X1+TS_DX)/25.4/12:.2f}', "
      f"Y={TS_Y1/25.4/12:.2f}' – {(TS_Y1+TS_DY)/25.4/12:.2f}'")
print(f"    Extension tbl : +36\" east (fence side)")
print(f"    Infeed clear  : {TS_Y1/25.4/12:.1f}' south  |  "
      f"Outfeed clear: {(Y_N-TS_Y1-TS_DY)/25.4/12:.1f}' north")
print("─" * 60)
print("  NORTH WALL")
print(f"    Cabinets      : 15\" deep, 7' tall, full width (gap at door)")
print(f"    Lumber rack   : 8\" deep at 6'6\" AFF (8' boards horizontal)")
print("=" * 60)
print("Groups: Grp_Walls / Grp_Joists / Grp_Electrical /")
print("        Grp_Tools_West / Grp_Tools_East / Grp_Storage")
print("Tip: hide Grp_Joists + Grp_Walls to see tool layout clearly.")
