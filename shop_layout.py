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

# =============================================================================
# WEST WALL — south to north: dust collector, drill press, band saw,
#             thickness planer, storage cabinets, electrical panel
# =============================================================================
C_BENCH   = (0.55, 0.40, 0.25)   # bench-top / wood-tone
C_STORAGE = C_FRAME
C_LUMBER  = C_JOIST

# ── Dust Collector — SW corner ────────────────────────────────────────────────
# Base: 26" along west wall (N-S) × 16" deep (E-W), on casters 2" above floor
# Two filter bags: 15" dia × 24" tall, stacked with 6" metal spacer between
# Small motor box on base, north of bags

DC_DX     = inch(16)           # base depth into room
DC_DY     = inch(26)           # base width along wall
DC_BASE_Z = inch(2)            # caster height (underside of base)
DC_BASE_H = inch(4)            # base platform thickness  → top at 6" AFF

dc_base = box("DustColl_Base",
    X_W, Y_S, DC_BASE_Z,
    DC_DX, DC_DY, DC_BASE_H,
    color=(0.40, 0.40, 0.45), transp=0)

# Bags centred in the base footprint (leave 5" on north side for motor)
BAG_R  = inch(7.5)             # 15" dia
BAG_H  = inch(24)
BAG_Z0 = DC_BASE_Z + DC_BASE_H  # bottom of first bag = top of base platform
BAG_CX = X_W + inch(8)         # centre X  (middle of 16" depth)
BAG_CY = Y_S + inch(10)        # centre Y  (5.5" south clearance, motor north)

bag1_shape = Part.makeCylinder(BAG_R, BAG_H,
    Vector(BAG_CX, BAG_CY, BAG_Z0), Vector(0, 0, 1))
dc_bag1 = part_feat("DustColl_Bag1", bag1_shape,
    color=(0.70, 0.70, 0.74), transp=15)

# Metal spacer between bags
SPACER_H = inch(6)
spacer_shape = Part.makeCylinder(inch(6), SPACER_H,
    Vector(BAG_CX, BAG_CY, BAG_Z0 + BAG_H), Vector(0, 0, 1))
dc_spacer = part_feat("DustColl_Spacer", spacer_shape,
    color=(0.45, 0.45, 0.50), transp=0)

# Second bag
bag2_shape = Part.makeCylinder(BAG_R, BAG_H,
    Vector(BAG_CX, BAG_CY, BAG_Z0 + BAG_H + SPACER_H), Vector(0, 0, 1))
dc_bag2 = part_feat("DustColl_Bag2", bag2_shape,
    color=(0.70, 0.70, 0.74), transp=15)

# Motor — small box on base, north of bags
dc_motor = box("DustColl_Motor",
    X_W + inch(2), Y_S + inch(19), BAG_Z0,
    inch(10), inch(6), inch(10),
    color=(0.28, 0.28, 0.32), transp=0)

dust_objs = [dc_base, dc_bag1, dc_spacer, dc_bag2, dc_motor]

# ── Drill Press — 1 foot north of dust collector ──────────────────────────────
DP_GAP = inch(12)              # 1' gap from collector north face
DP_DX  = inch(18)
DP_DY  = inch(18)
DP_Y1  = Y_S + DC_DY + DP_GAP # south face of base

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

drillpress_objs = [dp_base, dp_col, dp_head]

# ── Band Saw — 1 foot north of drill press ────────────────────────────────────
# Floor-mount on wheels, 6' tall
# Base: 24" deep (E-W) × 18" wide (N-S)
# Tilting table: 21-3/8" × 15-5/8" at 40" AFF

BS_GAP = inch(12)              # 1' gap from drill press north face
BS_DX  = inch(24)
BS_DY  = inch(18)
BS_DZ  = inch(72)
BS_X   = X_W
BS_Y   = DP_Y1 + DP_DY + BS_GAP   # south face

bs_body = box("BandSaw_Body",
    BS_X, BS_Y, 0,
    BS_DX, BS_DY, BS_DZ,
    color=C_TOOL, transp=0)

BS_TW = inch(21 + 3/8)
BS_TD = inch(15 + 5/8)
bs_table = box("BandSaw_Table",
    BS_X + (BS_DX - BS_TW) / 2,
    BS_Y + (BS_DY - BS_TD) / 2,
    inch(40),
    BS_TW, BS_TD, inch(1.5),
    color=C_TOPTBL, transp=0)

bandssaw_objs = [bs_body, bs_table]

# ── Thickness Planer — 6" north of band saw ───────────────────────────────────
# Machine: 20"×20"×16" body  on a  24"×24"×36" stand on castors (~38" w/casters)
# Stored against west wall; rolls into open centre for infeed/outfeed

PL_GAP      = inch(6)
PL_STAND_DX = inch(24)        # stand depth into room
PL_STAND_DY = inch(24)        # stand width along wall
PL_STAND_DZ = inch(38)        # 36" stand + ~2" casters
PL_MACH_W   = inch(20)        # machine body E-W
PL_MACH_D   = inch(20)        # machine body N-S
PL_MACH_H   = inch(16)        # machine body height
PL_Y1       = BS_Y + BS_DY + PL_GAP   # south face of stand

pl_stand = box("Planer_Stand",
    X_W, PL_Y1, 0,
    PL_STAND_DX, PL_STAND_DY, PL_STAND_DZ,
    color=(0.45, 0.45, 0.48), transp=0)

pl_body = box("Planer_Body",
    X_W + (PL_STAND_DX - PL_MACH_W) / 2,
    PL_Y1 + (PL_STAND_DY - PL_MACH_D) / 2,
    PL_STAND_DZ,
    PL_MACH_W, PL_MACH_D, PL_MACH_H,
    color=C_TOOL, transp=0)

planer_objs = [pl_stand, pl_body]

# ── West Wall Storage Cabinets — 6" north of planer, to 6" south of panel ────
# 24" deep × 7' tall cabinets run the full gap between planer and panel

ST_GAP = inch(6)
ST_Y1  = PL_Y1 + PL_STAND_DY + ST_GAP     # south face
ST_Y2  = panel_bot_y - ST_GAP              # north face
ST_DY  = ST_Y2 - ST_Y1
ST_DX  = inch(24)
ST_DZ  = inch(84)                          # 7' tall

st_cabs = box("Storage_WestCabs",
    X_W, ST_Y1, 0,
    ST_DX, ST_DY, ST_DZ,
    color=C_STORAGE, transp=20)

storage_west_objs = [st_cabs]

west_wall_objs = (dust_objs + drillpress_objs + bandssaw_objs
                  + planer_objs + storage_west_objs)

# =============================================================================
# EAST WALL — chop saw station starting at the jut
# =============================================================================
# Bench north face sits at the bottom of the jut (Y=12'6"), runs 6' south.
# Saw centred at Y=9'6"; 3' of built-in support each side.
# South portion of east wall (Y=0–6'6") left open as loading/staging area.

CS_Y2 = Y_JUT_BOT                  # north end at bottom of jut = 12'6"
CS_Y1 = CS_Y2 - ft(6)              # south end = 6'6"
CS_DY = ft(6)
CS_DX = inch(24)                    # 24" deep from east wall
CS_X1 = X_SE - CS_DX

cs_bench = box("ChopSaw_Bench",
    CS_X1, CS_Y1, 0,
    CS_DX, CS_DY, inch(34),
    color=C_FRAME, transp=15)

cs_top = box("ChopSaw_BenchTop",
    CS_X1, CS_Y1, inch(34),
    CS_DX, CS_DY, inch(1.5),
    color=C_BENCH, transp=0)

# Saw centred N-S on bench, sitting on bench top
CS_SAW_W = inch(20)
CS_SAW_D = inch(15)
CS_SAW_Y = CS_Y1 + CS_DY / 2       # mid-bench Y
cs_saw = box("ChopSaw_Saw",
    CS_X1 + (CS_DX - CS_SAW_W) / 2,
    CS_SAW_Y - CS_SAW_D / 2,
    inch(35.5),
    CS_SAW_W, CS_SAW_D, inch(14),
    color=C_TOOL, transp=0)

chop_objs = [cs_bench, cs_top, cs_saw]

# =============================================================================
# TABLE SAW — floating in wider north zone (unchanged)
# =============================================================================
# Cabinet: 22" E-W × 27" N-S, blade at X≈47" (3'11" from west wall).
# 36" extension table east (fence side). South face at Y=13'.
# Infeed: 13' south; outfeed: 9' to north wall.

TS_Y1 = ft(13)
TS_DY = inch(27)
TS_X1 = inch(36)
TS_DX = inch(22)
TS_DZ = inch(34)

ts_cab = box("TableSaw_Cabinet",
    TS_X1, TS_Y1, 0,
    TS_DX, TS_DY, TS_DZ,
    color=C_TOOL, transp=0)

ts_top = box("TableSaw_Top",
    TS_X1, TS_Y1, TS_DZ,
    TS_DX, TS_DY, inch(1.5),
    color=C_TOPTBL, transp=0)

ts_ext = box("TableSaw_Extension",
    TS_X1 + TS_DX, TS_Y1, TS_DZ,
    inch(36), TS_DY, inch(1.5),
    color=C_TOPTBL, transp=15)

ts_roller = box("TableSaw_RollerStand",
    TS_X1 + inch(4), TS_Y1 + TS_DY + ft(4), TS_DZ - inch(2),
    inch(14), inch(14), inch(2),
    color=(0.6, 0.6, 0.6), transp=20)

tablesaw_objs = [ts_cab, ts_top, ts_ext, ts_roller]

# =============================================================================
# NORTH WALL — lumber rack only (storage cabinets moved to west wall)
# =============================================================================
LR_Z1  = inch(78)
LR_DZ  = inch(10)
LR_DY  = inch(8)

lr_rack = box("LumberRack",
    X_W, Y_N - LR_DY, LR_Z1,
    X_NE - ft(3), LR_DY, LR_DZ,
    color=C_LUMBER, transp=25)

storage_objs = storage_west_objs + [lr_rack]

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
grp("Grp_Tools_East", chop_objs + tablesaw_objs)
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
print(f"    Dust collector: Y={Y_S/25.4/12:.2f}' – {DC_DY/25.4/12:.2f}'  (SW corner, 16\"×26\" base)")
dc_bag2_top = (BAG_Z0 + BAG_H + SPACER_H + BAG_H) / 25.4
print(f"      Bags (×2, 15\"dia×24\"): stacked to {dc_bag2_top:.1f}\" AFF")
print(f"    Drill press   : Y={DP_Y1/25.4/12:.2f}' – {(DP_Y1+DP_DY)/25.4/12:.2f}'")
print(f"    Band saw      : Y={BS_Y/25.4/12:.2f}' – {(BS_Y+BS_DY)/25.4/12:.2f}'  (24\"×18\", on wheels)")
print(f"    Planer        : Y={PL_Y1/25.4/12:.2f}' – {(PL_Y1+PL_STAND_DY)/25.4/12:.2f}'  "
      f"(20\"×20\"×16\" machine on 24\"×24\"×36\" stand)")
print(f"    Storage cabs  : Y={ST_Y1/25.4/12:.2f}' – {ST_Y2/25.4/12:.2f}'  "
      f"({ST_DY/25.4/12:.1f}' long, 24\" deep, 7' tall)")
print(f"    Elec. panel   : Y={panel_bot_y/25.4/12:.2f}' – {panel_top_y/25.4/12:.2f}'")
print("─" * 60)
print("  EAST WALL (south → north)")
print(f"    Open staging  : Y=0 – {CS_Y1/25.4/12:.2f}'  (clear floor below chop saw)")
print(f"    Chop saw stn  : Y={CS_Y1/25.4/12:.2f}' – {CS_Y2/25.4/12:.2f}'  "
      f"(bench starts at jut, saw at Y≈{CS_SAW_Y/25.4/12:.1f}')")
print("─" * 60)
print("  TABLE SAW (floating, wider north zone)")
print(f"    Cabinet       : X={TS_X1/25.4/12:.2f}' – {(TS_X1+TS_DX)/25.4/12:.2f}', "
      f"Y={TS_Y1/25.4/12:.2f}' – {(TS_Y1+TS_DY)/25.4/12:.2f}'")
print(f"    Extension     : +36\" east (fence side)")
print(f"    Infeed        : {TS_Y1/25.4/12:.1f}' south  |  "
      f"Outfeed: {(Y_N-TS_Y1-TS_DY)/25.4/12:.1f}' north")
print("─" * 60)
print("  NORTH WALL")
print(f"    Lumber rack   : 8\" deep at 6'6\" AFF  (cabinets moved to west wall)")
print("=" * 60)
print("Groups: Grp_Walls / Grp_Joists / Grp_Electrical /")
print("        Grp_Tools_West / Grp_Tools_East / Grp_Storage")
print("Tip: hide Grp_Joists + Grp_Walls to see tool layout clearly.")
