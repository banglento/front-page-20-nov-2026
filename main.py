#!/usr/bin/env python3
"""Draw a deterministic broadsheet front page using only the Python standard library."""
import os
import struct
import zlib

W = H = 1024
PAPER = (245, 238, 218)
INK = (24, 39, 55)
RED = (174, 45, 39)
GREY = (102, 105, 104)
WHITE = (255, 251, 238)

# Five-by-seven bitmap glyphs. A text call uppercases before looking up glyphs.
_FONT_ROWS = {
'A':('01110','10001','10001','11111','10001','10001','10001'), 'B':('11110','10001','10001','11110','10001','10001','11110'),
'C':('01111','10000','10000','10000','10000','10000','01111'), 'D':('11110','10001','10001','10001','10001','10001','11110'),
'E':('11111','10000','10000','11110','10000','10000','11111'), 'F':('11111','10000','10000','11110','10000','10000','10000'),
'G':('01111','10000','10000','10111','10001','10001','01111'), 'H':('10001','10001','10001','11111','10001','10001','10001'),
'I':('11111','00100','00100','00100','00100','00100','11111'), 'J':('00111','00010','00010','00010','10010','10010','01100'),
'K':('10001','10010','10100','11000','10100','10010','10001'), 'L':('10000','10000','10000','10000','10000','10000','11111'),
'M':('10001','11011','10101','10101','10001','10001','10001'), 'N':('10001','11001','10101','10011','10001','10001','10001'),
'O':('01110','10001','10001','10001','10001','10001','01110'), 'P':('11110','10001','10001','11110','10000','10000','10000'),
'Q':('01110','10001','10001','10001','10101','10010','01101'), 'R':('11110','10001','10001','11110','10100','10010','10001'),
'S':('01111','10000','10000','01110','00001','00001','11110'), 'T':('11111','00100','00100','00100','00100','00100','00100'),
'U':('10001','10001','10001','10001','10001','10001','01110'), 'V':('10001','10001','10001','10001','10001','01010','00100'),
'W':('10001','10001','10001','10101','10101','10101','01010'), 'X':('10001','10001','01010','00100','01010','10001','10001'),
'Y':('10001','10001','01010','00100','00100','00100','00100'), 'Z':('11111','00001','00010','00100','01000','10000','11111'),
'0':('01110','10001','10011','10101','11001','10001','01110'), '1':('00100','01100','00100','00100','00100','00100','01110'),
'2':('01110','10001','00001','00010','00100','01000','11111'), '3':('11110','00001','00001','01110','00001','00001','11110'),
'4':('00010','00110','01010','10010','11111','00010','00010'), '5':('11111','10000','10000','11110','00001','00001','11110'),
'6':('01110','10000','10000','11110','10001','10001','01110'), '7':('11111','00001','00010','00100','01000','01000','01000'),
'8':('01110','10001','10001','01110','10001','10001','01110'), '9':('01110','10001','10001','01111','00001','00001','01110'),
'.':('00000','00000','00000','00000','00000','00110','00110'), ',':('00000','00000','00000','00000','00110','00110','00100'),
':':('00000','00110','00110','00000','00110','00110','00000'), ';':('00000','00110','00110','00000','00110','00110','00100'),
'!':('00100','00100','00100','00100','00100','00000','00100'), '?':('01110','10001','00001','00010','00100','00000','00100'),
"'":('00100','00100','00000','00000','00000','00000','00000'), '"':('01010','01010','00000','00000','00000','00000','00000'),
'-':('00000','00000','00000','11111','00000','00000','00000'), '(':('00010','00100','01000','01000','01000','00100','00010'),
')':('01000','00100','00010','00010','00010','00100','01000'), '/':('00001','00010','00010','00100','01000','01000','10000'),
'&':('01100','10010','10100','01000','10101','10010','01101'), '%':('11001','11010','00100','01000','10110','00110','00000'),
'+':('00000','00100','00100','11111','00100','00100','00000'), '=':('00000','11111','00000','11111','00000','00000','00000'),
'*':('00000','10101','01110','11111','01110','10101','00000'), '$':('00100','01111','10100','01110','00101','11110','00100'),
'#':('01010','11111','01010','01010','11111','01010','00000'), '@':('01110','10001','10111','10101','10111','10000','01111'),
'_':('00000','00000','00000','00000','00000','00000','11111'), ' ':('00000',)*7,
}

pixels = bytearray(W * H * 3)

def rect(x, y, w, h, color):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        start = (yy * W + x0) * 3
        pixels[start:start + len(row)] = row

def pixel(x, y, color):
    x, y = int(x), int(y)
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        pixels[i:i+3] = bytes(color)

def line(x0, y0, x1, y1, color, width=1):
    x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
    dx, sx = abs(x1-x0), 1 if x0 < x1 else -1
    dy, sy = -abs(y1-y0), 1 if y0 < y1 else -1
    err = dx + dy
    r = max(0, int(width)//2)
    while True:
        if r:
            circle(x0, y0, r, color)
        else:
            pixel(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy

def circle(cx, cy, radius, color):
    cx, cy, radius = int(cx), int(cy), int(radius)
    rr = radius * radius
    for yy in range(max(0, cy-radius), min(H, cy+radius+1)):
        dy = yy - cy
        extent = int((rr - dy*dy) ** 0.5) if rr >= dy*dy else -1
        if extent >= 0:
            rect(cx-extent, yy, 2*extent+1, 1, color)

def polygon(points, color):
    if len(points) < 3:
        return
    ymin = max(0, min(int(p[1]) for p in points)); ymax = min(H-1, max(int(p[1]) for p in points))
    for y in range(ymin, ymax+1):
        xs = []
        for i, (x1, y1) in enumerate(points):
            x2, y2 = points[(i+1) % len(points)]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(int(x1 + (y-y1) * (x2-x1) / (y2-y1)))
        xs.sort()
        for i in range(0, len(xs)-1, 2):
            rect(xs[i], y, xs[i+1]-xs[i]+1, 1, color)

def starburst(cx, cy, outer, inner, points, color):
    verts = []
    for i in range(points * 2):
        angle = -1.5707963267948966 + i * 3.141592653589793 / points
        radius = outer if i % 2 == 0 else inner
        verts.append((int(cx + radius * __import__('math').cos(angle)), int(cy + radius * __import__('math').sin(angle))))
    polygon(verts, color)

def text_width(s, scale):
    s = str(s).upper().replace('–', '-').replace('—', '-')
    return max(0, len(s) * 6 * scale - scale)

def draw_text(x, y, s, color=INK, scale=2):
    s = str(s).upper().replace('–', '-').replace('—', '-')
    x, y = int(x), int(y)
    start = x
    for ch in s:
        rows = _FONT_ROWS.get(ch, _FONT_ROWS['?'])
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == '1':
                    rect(x + rx*scale, y + ry*scale, scale, scale, color)
        x += 6 * scale
    return x - start - (scale if s else 0)

def wrap_words(text, max_width, scale):
    text = str(text).replace('–', '-').replace('—', '-')
    words = text.split()
    lines, current = [], ''
    for word in words:
        candidate = word if not current else current + ' ' + word
        if current and text_width(candidate, scale) > max_width:
            lines.append(current); current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines

def draw_wrapped(x, y, text, max_width, color=INK, scale=2, leading=None):
    lines = wrap_words(text, max_width, scale)
    step = leading if leading is not None else 8 * scale
    for i, item in enumerate(lines):
        draw_text(x, y + i*step, item, color, scale)
    return y + len(lines)*step, lines

def panel(x, y, w, h, fill=PAPER):
    rect(x, y, w, h, fill)
    rect(x, y, w, 2, INK); rect(x, y+h-2, w, 2, INK)
    rect(x, y, 2, h, INK); rect(x+w-2, y, 2, h, INK)

def flag_stripes(x, y, w, h, colors):
    for i, col in enumerate(colors):
        y0 = y + h*i//len(colors); y1 = y + h*(i+1)//len(colors)
        rect(x, y0, w, y1-y0, col)

def draw_masthead():
    title = 'THE WORLD IN ONE DAY'
    draw_text((W-text_width(title, 7))//2, 25, title, INK, 7)
    rect(32, 91, 960, 54, RED)
    date = 'FRIDAY, 20 NOVEMBER 2026'
    draw_text((W-text_width(date, 5))//2, 99, date, WHITE, 5)

def draw_lead_illustration(x, y, w, h):
    rect(x, y, w, h, (20, 34, 58))
    # Night sky and two incoming missile trails.
    for sx, sy in [(x+32,y+24),(x+142,y+18),(x+235,y+35),(x+355,y+16),(x+390,y+72),(x+90,y+81)]:
        circle(sx, sy, 2, (220, 224, 214))
    line(x+101, y+1, x+240, y+108, (242, 171, 81), 4)
    line(x+246, y-1, x+326, y+91, (255, 197, 104), 3)
    line(x+101, y+1, x+240, y+108, (255, 231, 174), 1)
    line(x+246, y-1, x+326, y+91, (255, 236, 179), 1)
    # Kyiv skyline and embassy blocks.
    rect(x, y+145, w, h-145, (39, 52, 67))
    buildings = [(x+12, y+112,48,115),(x+61,y+95,54,132),(x+119,y+126,38,101),
                 (x+160,y+82,58,145),(x+222,y+109,43,118),(x+267,y+70,70,157),
                 (x+340,y+103,47,124),(x+390,y+120,35,107)]
    for bx, by, bw, bh in buildings:
        rect(bx, by, bw, bh, (57, 68, 80))
        for wy in range(by+12, y+205, 18):
            for wx in range(bx+8, bx+bw-5, 15):
                rect(wx, wy, 5, 7, (230, 186, 105) if (wx+wy)%3 else (110, 139, 156))
    # Embassy facades and their flags (Austria, Netherlands).
    rect(x+119, y+125, 58, 93, (133, 132, 119))
    rect(x+267, y+114, 70, 113, (145, 138, 121))
    line(x+148, y+72, x+148, y+101, WHITE, 2)
    flag_stripes(x+150, y+73, 26, 16, [RED, WHITE, RED])
    line(x+301, y+80, x+301, y+101, WHITE, 2)
    flag_stripes(x+303, y+81, 28, 18, [RED, WHITE, (32, 76, 151)])
    for cx, cy, r in [(x+210,y+142,17),(x+231,y+135,21),(x+247,y+146,16),(x+329,y+145,19),(x+349,y+135,16)]:
        circle(cx, cy, r, (91, 99, 107))
    # Searchlights sweep the smoky skyline.
    line(x+41, y+218, x+162, y+87, (156, 190, 205), 2)
    line(x+365, y+221, x+275, y+58, (156, 190, 205), 2)
    rect(x+6, y+h-21, w-12, 1, (180, 183, 177))

def draw_lead():
    x, y, w, h = 32, 156, 960, 244
    panel(x, y, w, h, (250, 246, 233))
    draw_text(x+15, y+12, 'LEAD STORY - UKRAINE', RED, 2)
    draw_text(x+15, y+37, 'KYIV HIT BY', INK, 5)
    draw_text(x+15, y+75, 'FOUR MISSILES', INK, 5)
    deck = 'Four ballistic missiles hit the capital overnight; Russian strikes damage the Austrian and Dutch embassies.'
    draw_wrapped(x+15, y+123, deck, 470, INK, 2, 16)
    draw_text(x+15, y+207, 'EMBASSIES DAMAGED', RED, 2)
    draw_lead_illustration(x+528, y+10, 417, 224)

def draw_china_illustration(x, y, w, h):
    rect(x, y, w, h, (179, 207, 210))
    rect(x, y+int(h*.55), w, int(h*.45), (65, 126, 153))
    rect(x, y+int(h*.55), w, 3, (235, 225, 193))
    # Distant Shenzhen skyline.
    for bx, bw, bh in [(x+12,35,40),(x+54,31,55),(x+91,44,68),(x+143,37,48),(x+190,43,61),(x+242,37,49),(x+294,39,70),(x+343,38,51),(x+390,32,64)]:
        rect(bx, y+int(h*.55)-bh, bw, bh, (82, 111, 123))
        for wy in range(y+int(h*.55)-bh+8, y+int(h*.55)-5, 12):
            rect(bx+7, wy, max(4,bw-14), 2, (208, 190, 144))
    # Three flags: United States, China, Russia.
    bases = [x+72, x+208, x+342]
    for bx in bases:
        line(bx, y+8, bx, y+74, INK, 2)
    fx, fy = bases[0]+2, y+12
    flag_stripes(fx, fy, 48, 27, [(181,45,49), WHITE, (181,45,49), WHITE, (181,45,49), WHITE, (181,45,49)])
    rect(fx, fy, 21, 15, (37,61,112))
    for sy in (fy+4, fy+10):
        for sx in (fx+5, fx+12, fx+17): circle(sx, sy, 1, WHITE)
    fx, fy = bases[1]+2, y+12
    rect(fx, fy, 48, 27, (193,48,45))
    starburst(fx+13, fy+11, 6, 2, 5, (255,220,75))
    for sx, sy in [(fx+25,fy+5),(fx+31,fy+10),(fx+30,fy+18),(fx+23,fy+21)]: starburst(sx,sy,2,1,5,(255,220,75))
    flag_stripes(bases[2]+2, y+12, 48, 27, [WHITE, (42,71,146), (185,49,48)])
    # Low reflected light on the lake.
    for i in range(7):
        yy = y+int(h*.64)+i*5
        rect(x+35+i*18, yy, 45+(i%3)*20, 1, (196, 194, 164))

def draw_tanker_illustration(x, y, w, h):
    rect(x, y, w, h, (37, 91, 125))
    for yy in range(y+15, y+h, 18):
        line(x+8, yy, x+w-8, yy+2, (79, 133, 157), 1)
    # Ship hull and deck structures.
    polygon([(x+28,y+55),(x+w-28,y+55),(x+w-46,y+78),(x+53,y+78)], (31,42,49))
    rect(x+58, y+34, w-122, 21, (178, 74, 47))
    for bx in range(x+68, x+w-70, 34):
        rect(bx, y+39, 25, 11, (204, 123, 70))
    rect(x+w-94, y+23, 42, 32, (218, 208, 177))
    rect(x+w-84, y+28, 8, 9, (62, 93, 115)); rect(x+w-68, y+28, 8, 9, (62, 93, 115))
    draw_text(x+96, y+61, 'TANKER', WHITE, 1)
    # Flames and smoke above the deck.
    polygon([(x+99,y+35),(x+107,y+7),(x+116,y+28),(x+125,y+1),(x+133,y+35)], (240,112,40))
    polygon([(x+108,y+35),(x+116,y+17),(x+121,y+34)], (255,214,75))
    for cx, cy, r in [(x+125,y+12,12),(x+138,y+8,15),(x+151,y+14,12)]: circle(cx,cy,r,(105,108,106))
    # Mine silhouette below the waterline.
    circle(x+w//2, y+h-10, 11, (29,42,48))
    for i in range(8):
        import math
        a = i * math.pi / 4
        line(x+w//2+int(10*math.cos(a)), y+h-10+int(10*math.sin(a)), x+w//2+int(18*math.cos(a)), y+h-10+int(18*math.sin(a)), (29,42,48), 3)

def draw_half_panels():
    y, h, gap = 410, 239, 12
    x1, w = 32, 472
    x2 = x1+w+gap
    panel(x1,y,w,h,(250,246,233)); panel(x2,y,w,h,(250,246,233))
    draw_text(x1+13,y+11,'CHINA - TRILATERAL SUMMIT',RED,2)
    draw_text(x1+13,y+34,'A PEACE DECLARATION',INK,3)
    deck1 = 'Trump, Xi and Putin issue a four-point declaration after their first-ever three-way summit in Shenzhen; the statement backs nuclear non-proliferation. Talks covered Ukraine, Iran and trade.'
    draw_wrapped(x1+13,y+61,deck1,w-26,INK,2,15)
    draw_china_illustration(x1+8,y+172,w-16,58)
    draw_text(x2+13,y+11,'GULF - HORMUZ',RED,2)
    draw_text(x2+13,y+34,'TANKER HITS MINE',INK,3)
    deck2 = 'A tanker catches fire after hitting a mine east of the Strait of Hormuz; Iran says it is the third such strike in 24 hours.'
    draw_wrapped(x2+13,y+61,deck2,w-26,INK,2,15)
    draw_tanker_illustration(x2+8,y+153,w-16,77)

def draw_airport_illustration(x,y,w,h):
    rect(x,y,w,h,(24,39,59))
    # Distant airport lights and runway perspective.
    for i in range(13):
        circle(x+8+i*22,y+31+(i%3)*4,2,(250,193,83))
    polygon([(x+42,y+25),(x+w-42,y+25),(x+w-5,y+h),(x+5,y+h)], (54,62,68))
    line(x+w//2,y+35,x+w//2,y+h-2,(230,224,198),2)
    for yy in range(y+44,y+h,15): rect(x+w//2-2,yy,4,7,(238,224,177))
    for bx in range(x+18,x+w-10,25): circle(bx,y+h-8,2,(233,91,53))
    # Grounded passenger plane.
    polygon([(x+70,y+64),(x+145,y+64),(x+164,y+70),(x+145,y+74),(x+70,y+74),(x+54,y+70)],(215,218,211))
    polygon([(x+103,y+64),(x+117,y+47),(x+126,y+47),(x+121,y+65)],(215,218,211))
    polygon([(x+106,y+73),(x+120,y+87),(x+128,y+87),(x+119,y+72)],(215,218,211))
    # Three drone silhouettes above runway.
    for dx,dy in [(x+57,y+22),(x+180,y+17),(x+225,y+35)]:
        line(dx-10,dy,dx+10,dy,(220,220,204),2); circle(dx,dy,3,(220,220,204))
        line(dx-7,dy-4,dx-7,dy+4,(220,220,204),1); line(dx+7,dy-4,dx+7,dy+4,(220,220,204),1)

def draw_market_illustration(x,y,w,h):
    rect(x,y,w,h,(24,43,64))
    for gx in range(x+12,x+w,35): line(gx,y+7,gx,y+h-7,(53,71,85),1)
    for gy in range(y+8,y+h,18): line(x+8,gy,x+w-8,gy,(53,71,85),1)
    draw_text(x+13,y+8,'NASDAQ',WHITE,1)
    draw_text(x+13,y+26,'ANT', (250,206,92), 2)
    draw_text(x+w-65,y+8,'$83',WHITE,2)
    pts=[(x+22,y+h-17),(x+62,y+h-27),(x+102,y+h-25),(x+144,y+h-48),(x+190,y+h-46),(x+w-17,y+22)]
    for a,b in zip(pts,pts[1:]): line(a[0],a[1],b[0],b[1],(105,208,139),3)
    starburst(x+w-17,y+22,6,3,5,(255,220,91))

def draw_brief(x,y,w,h):
    draw_text(x+11,y+11,'IN BRIEF',RED,2)
    draw_text(x+11,y+34,'AROUND THE WORLD',INK,3)
    items = [
        'HOUTHIS: claim drone and missile strikes on four Saudi targets.',
        'COP31: UN climate talks close in Antalya; fossil-fuel reference dropped from the draft.',
        'SOUTH KOREA: annual exports top $1 trillion for the first time.',
        'INDIA: more than 80,000 evacuated as tropical storm Dana nears the coast.',
        'US: Trump posthumously pardons baseball legend Pete Rose.',
    ]
    yy = y+64
    maxw = w-38
    for item in items:
        lines = wrap_words(item,maxw,2)
        circle(x+15,yy+5,3,RED)
        for j, segment in enumerate(lines):
            draw_text(x+25, yy+j*14, segment, INK, 2)
        yy += len(lines)*14 + 3

def draw_bottom_panels():
    y,h=661,329
    xs=[32,352,672]; w=312
    for x in xs: panel(x,y,w,h,(250,246,233))
    x=xs[0]
    draw_text(x+11,y+10,'EUROPE - ITALY',RED,2)
    draw_wrapped(x+11,y+31,'DRONES SHUT GENOA AIRPORT',w-22,INK,3,23)
    draw_wrapped(x+11,y+82,'Unidentified drones force Genoa airport to suspend all flights for four hours overnight.',w-22,INK,2,15)
    draw_airport_illustration(x+7,y+174,w-14,146)
    x=xs[1]
    draw_text(x+11,y+10,'MARKETS - IPO',RED,2)
    draw_wrapped(x+11,y+31,'ANTHROPIC DEBUTS',w-22,INK,3,23)
    draw_wrapped(x+11,y+82,"Anthropic's shares begin trading on the Nasdaq in the largest IPO on record - an $81.3 billion raise, priced at $83 a share.",w-22,INK,2,15)
    draw_market_illustration(x+7,y+174,w-14,146)
    draw_brief(xs[2],y,w,h)

def png_chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)

def write_png(path):
    raw = bytearray()
    stride=W*3
    for y in range(H):
        raw.append(0)
        raw.extend(pixels[y*stride:(y+1)*stride])
    data=(b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('>2I5B',W,H,8,2,0,0,0))+
          png_chunk(b'IDAT',zlib.compress(bytes(raw),9))+png_chunk(b'IEND',b''))
    with open(path,'wb') as f: f.write(data)

def draw():
    rect(0,0,W,H,PAPER)
    # Thin double broadsheet frame.
    rect(15,15,994,2,INK); rect(15,15,2,994,INK)
    rect(1007,15,2,994,INK); rect(15,1007,994,2,INK)
    rect(21,21,982,1,RED); rect(21,21,1,982,RED)
    rect(1002,21,1,982,RED); rect(21,1002,982,1,RED)
    draw_masthead()
    draw_lead()
    draw_half_panels()
    draw_bottom_panels()
    footer='ALL EVENTS OF FRIDAY, 20 NOVEMBER 2026'
    draw_text((W-text_width(footer,1))//2,992,footer,GREY,1)

def main():
    draw()
    output_dir=os.environ.get('MAKEFUN_OUTPUT_DIR','/output')
    os.makedirs(output_dir,exist_ok=True)
    write_png(os.path.join(output_dir,'entry.png'))

if __name__=='__main__':
    main()
