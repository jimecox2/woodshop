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

tool_objs = [bs_body, bs_table]

# =============================================================================
# GROUPS
# =============================================================================
def grp(name, objs):
    g = doc.addObject("App::DocumentObjectGroup", name)
    g.addObjects([o for o in objs if o is not None])
    return g

grp("Grp_Floor",    [floor_obj])
grp("Grp_Walls",    [south_wall, west_wall,
                     nw_west, nw_east, nw_header,
                     east_lower, east_upper, east_jut])
grp("Grp_Door",     [door_obj])
grp("Grp_Joists",   lower_joist_objs + main_joist_objs)
grp("Grp_Electrical", [panel_obj])
grp("Grp_Tools",     tool_objs)

# =============================================================================
# FINALISE
# =============================================================================
doc.recompute()
Gui.activeDocument().activeView().viewIsometric()
Gui.SendMsgToActiveView("ViewFit")

print("=" * 60)
print("Woodshop Layout — Room Shell")
print("=" * 60)
print(f"  Room extents  : {X_NE/25.4/12:.2f}' E  x  {Y_N/25.4/12:.2f}' N")
print(f"  South wall    : {X_SE/25.4/12:.2f}' wide (concrete)")
print(f"  North wall    : {X_NE/25.4/12:.2f}' wide (2x4 + drywall)")
print(f"  Joist underside: {H_LOWER_BOT/25.4:.0f}\" AFF")
print(f"  Joist depth   : {H_JOIST/25.4:.0f}\"  |  top at {(H_LOWER_BOT+H_JOIST)/25.4:.0f}\" AFF")
print(f"  Lower joists  : {len(lower_joist_objs)} @ 16\" OC  (Y = 6\" to 7')")
print(f"  Main joists   : {len(main_joist_objs)} shown  (incl 2 south of room)")
print(f"  Door          : 36\" x 80\",  east-north wall, 6\" from east end")
print("=" * 60)
print(f"  Band saw base : 24\" deep x 18\" wide, against west wall")
print(f"  Band saw Y    : {BS_Y/25.4/12:.2f}' from south (south face of base)")
print(f"  Band saw gap  : 6\" south of electrical panel")
print("Groups: Grp_Floor / Grp_Walls / Grp_Door / Grp_Joists / Grp_Electrical / Grp_Tools")
print("Toggle visibility in Model panel to isolate layers.")
