from PIL import Image, ImageDraw, ImageFont
import os

FONT_DIR = "/home/scott/.claude/skills/canvas-design/canvas-fonts/"

W, H = 1400, 420

NAVY       = (14,  40,  74)
NAVY_MID   = (22,  54,  96)
STEEL      = (96, 112, 130)
STEEL_LIGHT= (160, 175, 190)
WHITE      = (255, 255, 255)
CREAM      = (248, 249, 250)
GOLD       = (185, 148,  72)

def load(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)

def spaced_text(draw, x, y, text, font, fill, spacing=5):
    cx = x
    for ch in text:
        draw.text((cx, y), ch, fill=fill, font=font)
        bb = draw.textbbox((0, 0), ch, font=font)
        cx += (bb[2] - bb[0]) + spacing
    return cx

def make_logo(bg, mark_bg, mark_fg, name_col, sub_col, rule_col, filename):
    img = Image.new('RGB', (W, H), bg)
    draw = ImageDraw.Draw(img)

    f_name = load("BigShoulders-Bold.ttf",    128)
    f_mark = load("BigShoulders-Bold.ttf",    170)
    f_sub  = load("InstrumentSans-Regular.ttf", 30)

    PAD      = 64
    MARK_W   = 230
    MARK_H   = 230
    mark_x   = PAD
    mark_y   = (H - MARK_H) // 2

    # --- MARK: chamfered rectangle (cut top-right corner) ---
    CUT = 30
    pts = [
        (mark_x,              mark_y + CUT),
        (mark_x + CUT,        mark_y),
        (mark_x + MARK_W,     mark_y),
        (mark_x + MARK_W,     mark_y + MARK_H),
        (mark_x,              mark_y + MARK_H),
    ]
    draw.polygon(pts, fill=mark_bg)

    # --- "B" centred inside mark, reversed out ---
    bb_b = draw.textbbox((0, 0), "B", font=f_mark)
    bw   = bb_b[2] - bb_b[0]
    bh   = bb_b[3] - bb_b[1]
    bx   = mark_x + (MARK_W - bw) // 2 - bb_b[0]
    by   = mark_y + (MARK_H - bh) // 2 - bb_b[1] - 4
    draw.text((bx, by), "B", fill=mark_fg, font=f_mark)

    # --- thin gold accent bar at base of mark ---
    bar_y = mark_y + MARK_H + 10
    draw.rectangle([mark_x, bar_y, mark_x + MARK_W, bar_y + 4], fill=GOLD)

    # --- TEXT block ---
    text_x = mark_x + MARK_W + PAD + 20

    bb_name = draw.textbbox((0, 0), "BRISAR", font=f_name)
    name_h  = bb_name[3] - bb_name[1]

    bb_sub  = draw.textbbox((0, 0), "I", font=f_sub)   # height ref
    sub_h   = bb_sub[3] - bb_sub[1]

    gap       = 14
    total_h   = name_h + gap + sub_h
    name_y    = (H - total_h) // 2 - bb_name[1]
    rule_y    = name_y + name_h + gap // 2 - 1
    sub_y     = rule_y + 8

    # Company name
    draw.text((text_x, name_y), "BRISAR", fill=name_col, font=f_name)

    # Horizontal rule under name
    name_w = bb_name[2] - bb_name[0]
    draw.rectangle([text_x, rule_y, text_x + name_w + 60, rule_y + 2], fill=rule_col)

    # Spaced sub-text
    spaced_text(draw, text_x + 2, sub_y, "INVESTMENTS  LLC", f_sub, sub_col, spacing=4)

    # --- Thin vertical divider between mark and text ---
    div_x  = text_x - PAD // 2 - 4
    div_t  = mark_y + 10
    div_b  = mark_y + MARK_H - 10
    draw.rectangle([div_x, div_t, div_x + 2, div_b], fill=rule_col)

    img.save(filename, 'PNG', dpi=(300, 300))
    print(f"Saved {filename}")


# ── Version 1: White background (main) ──────────────────────────────
make_logo(
    bg       = CREAM,
    mark_bg  = NAVY,
    mark_fg  = CREAM,
    name_col = NAVY,
    sub_col  = STEEL,
    rule_col = STEEL_LIGHT,
    filename = "/home/scott/projects/govt-contracts/brisar-logo.png",
)

# ── Version 2: Navy background (reversed / white) ───────────────────
make_logo(
    bg       = NAVY,
    mark_bg  = WHITE,
    mark_fg  = NAVY,
    name_col = WHITE,
    sub_col  = STEEL_LIGHT,
    rule_col = (60, 85, 115),
    filename = "/home/scott/projects/govt-contracts/brisar-logo-white.png",
)
