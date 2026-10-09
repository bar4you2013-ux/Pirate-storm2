"""Cached, supersampled artwork. Rendering only; no gameplay state or RNG changes."""
from functools import lru_cache
import math
import random
import pygame


@lru_cache(maxsize=128)
def artwork(kind, width, height, variant=''):
    factor = 3
    s = pygame.Surface((width * factor, height * factor), pygame.SRCALPHA)
    def rect(c, box, edge=0, radius=0):
        pygame.draw.rect(s, c, tuple(round(v*factor) for v in box), edge*factor, border_radius=radius*factor)
    def line(c, a, b, thickness=1):
        pygame.draw.line(s,c,tuple(round(v*factor) for v in a),tuple(round(v*factor) for v in b),max(1,round(thickness*factor)))
    def ellipse(c, box, edge=0):
        pygame.draw.ellipse(s,c,tuple(round(v*factor) for v in box),edge*factor)
    def poly(c, points, edge=0):
        pygame.draw.polygon(s,c,[(round(x*factor),round(y*factor)) for x,y in points],edge*factor)
    rng = random.Random(f'{kind}:{variant}:{width}:{height}')
    w,h=width,height
    if kind == 'person':
        # Feet anchor at the bottom; coat, face and hat remain legible at game scale.
        coat = {'worker':(112,103,78),'Матрос':(71,91,104),'Рыбак':(111,105,79),
                'Торговка':(122,77,64),'Старый пират':(76,70,64)}.get(variant,(78,94,83))
        ellipse((20,24,22,65),(3,h-9,w-6,8))
        for x in (w*.34,w*.57):
            rect((53,49,43),(x,h*.68,w*.12,h*.23),radius=2)
            ellipse((35,31,28),(x-2,h*.87,w*.19,h*.09))
        poly((40,44,39),[(w*.22,h*.35),(w*.75,h*.35),(w*.81,h*.72),(w*.18,h*.72)])
        poly(coat,[(w*.27,h*.34),(w*.70,h*.34),(w*.76,h*.68),(w*.24,h*.68)])
        line(tuple(min(255,c+30) for c in coat),(w*.3,h*.4),(w*.3,h*.64),2)
        line((168,156,123),(w*.47,h*.36),(w*.52,h*.59),2)
        rect((65,43,29),(w*.24,h*.61,w*.51,3))
        rect((172,139,77),(w*.48,h*.61,4,4),1)
        for x in (w*.14,w*.73):
            line(coat,(x,h*.39),(x-1,h*.59),5)
            ellipse((182,140,103),(x-3,h*.58,6,7))
        ellipse((109,77,55),(w*.32,h*.14,w*.36,h*.24))
        ellipse((197,157,117),(w*.34,h*.15,w*.29,h*.22))
        line((58,48,39),(w*.39,h*.24),(w*.42,h*.24))
        line((58,48,39),(w*.56,h*.24),(w*.59,h*.24))
        line((132,92,66),(w*.49,h*.26),(w*.47,h*.29))
        poly((55,47,38),[(w*.13,h*.18),(w*.27,h*.07),(w*.50,h*.12),(w*.74,h*.07),(w*.86,h*.18),(w*.69,h*.22),(w*.29,h*.22)])
        line((142,116,72),(w*.29,h*.18),(w*.68,h*.18))
        if variant == 'worker':
            line((100,71,43),(w*.84,h*.4),(w*.9,h*.9),2)
            line((151,155,151),(w*.74,h*.42),(w*.98,h*.37),3)
    elif kind == 'building':
        market = variant in ('Рынок','market')
        fort = variant == 'fort'
        wall=(159,153,134) if fort or variant=='Банк' else (181,162,125)
        ellipse((24,28,24,70),(4,h*.78,w-4,h*.2))
        rect((71,64,52),(w*.09,h*.35,w*.84,h*.55),radius=2)
        rect(wall,(w*.07,h*.32,w*.82,h*.53))
        rect((123,109,86),(w*.07,h*.77,w*.82,h*.09))
        for yy in range(round(h*.35),round(h*.78),9):
            line(tuple(max(0,c-24) for c in wall),(w*.08,yy),(w*.88,yy))
            for xx in range(round(w*.1)+(yy//9%2)*12,round(w*.86),24):
                line((137,124,101),(xx,yy),(xx,yy+8))
        if fort:
            for xx in range(round(w*.07),round(w*.89),14):
                rect(wall,(xx,h*.22,9,h*.15))
        else:
            poly((62,54,46),[(2,h*.35),(w*.48,4),(w-3,h*.35),(w*.87,h*.4),(w*.46,h*.1),(w*.1,h*.4)])
            poly((115,75,53),[(4,h*.32),(w*.48,3),(w-7,h*.32)])
            for yy in range(12,round(h*.33),5):
                half=(yy-3)/(h*.32-3)*(w*.46)
                line((150,107,73),(w*.48-half,yy),(w*.48+half,yy))
                for xx in range(round(w*.48-half)+4,round(w*.48+half),10):
                    line((79,57,44),(xx,yy),(xx-2,yy+4))
        for xx in (w*.18,w*.67):
            rect((76,62,46),(xx-3,h*.45,w*.15+6,h*.22+5))
            rect((51,77,80),(xx,h*.45,w*.15,h*.20))
            rect((182,161,117),(xx,h*.45,w*.15,h*.20),1)
            line((182,161,117),(xx+w*.075,h*.45),(xx+w*.075,h*.65),2)
            line((182,161,117),(xx,h*.54),(xx+w*.15,h*.54))
        rect((54,43,32),(w*.43,h*.56,w*.16,h*.3),radius=3)
        for xx in range(round(w*.44),round(w*.58),4):
            line((104,79,49),(xx,h*.6),(xx,h*.84))
        ellipse((203,167,89),(w*.55,h*.73,3,3))
        rect((166,154,129),(w*.4,h*.85,w*.22,4))
        # Weathered plaster and roof flecks use a local RNG, never game randomness.
        for _ in range(max(20, w*h//100)):
            xx=rng.uniform(w*.08,w*.88); yy=rng.uniform(h*.35,h*.76)
            if w*.40 < xx < w*.61 or (w*.16 < xx < w*.35) or (w*.65 < xx < w*.85):
                continue
            line(tuple(max(0,c-rng.randrange(8,24)) for c in wall),(xx,yy),(xx+2,yy))
        if variant == 'Банк':
            for xx in (w*.08,w*.36,w*.61,w*.86):
                rect((194,187,166),(xx,h*.36,w*.045,h*.43))
                rect((130,124,110),(xx-2,h*.76,w*.075,5))
            ellipse((171,146,89),(w*.44,h*.39,w*.13,h*.12))
        if market or variant=='Лавка':
            for i in range(8):
                c=(137,62,46) if i%2 else (201,186,146)
                poly(c,[(w*.08+i*w*.1,h*.45),(w*.18+i*w*.1,h*.45),(w*.2+i*w*.1,h*.57),(w*.06+i*w*.1,h*.57)])
            rect((103,73,43),(w*.12,h*.7,w*.23,h*.16))
            for i in range(5): ellipse((162,124+i*5,54),(w*.14+i*5,h*.67,7,7))
        if variant=='Таверна':
            line((60,46,33),(w*.78,h*.36),(w*.98,h*.36),2)
            rect((84,58,36),(w*.87,h*.38,w*.12,h*.13),radius=2)
            ellipse((192,155,83),(w*.90,h*.40,w*.06,h*.07),1)
        if variant in ('Верфь','shipyard'):
            for i in range(3):
                line((126,88,51),(w*.75+i*4,h*.69),(w*.96,h*.91-i*4),3)
    elif kind == 'resource':
        ellipse((22,28,23,70),(1,h*.71,w-2,h*.24))
        if variant=='wood':
            for i in range(3):
                yy=h*.36+i*h*.16
                poly((87,57,34),[(w*.08,yy+h*.12),(w*.71,yy-h*.19),(w*.92,yy-h*.04),(w*.29,yy+h*.26)])
                line((153,110,62),(w*.14,yy+h*.1),(w*.73,yy-h*.16),2)
                ellipse((184,141,84),(w*.7,yy-h*.19,w*.23,h*.24))
                ellipse((111,73,41),(w*.74,yy-h*.15,w*.15,h*.16),1)
                for j in range(2): line((65,44,28),(w*.27,yy+h*.09+j*3),(w*.66,yy-h*.08+j*3))
        elif variant=='stone':
            for dx,dy,r in ((.25,.62,.23),(.65,.60,.29),(.45,.34,.24)):
                x,y=dx*w,dy*h; rw=r*w; rh=r*h
                pts=[(x-rw,y),(x-rw*.5,y-rh),(x+rw*.5,y-rh*.8),(x+rw,y),(x+rw*.5,y+rh*.7),(x-rw*.6,y+rh*.5)]
                poly((108,117,117),pts)
                poly((175,179,168),[pts[0],pts[1],pts[2],(x,y)])
                poly((68,78,80),[(x,y),pts[2],pts[3],pts[4]])
                line((201,199,181),pts[1],pts[2])
        else:
            ellipse((132,123,104),(w*.14,h*.14,w*.75,h*.68))
            ellipse((213,207,185),(w*.1,h*.1,w*.73,h*.65))
            for i in range(22):
                x=rng.uniform(w*.22,w*.67); y=rng.uniform(h*.22,h*.6)
                ellipse(rng.choice([(239,232,209),(179,170,145)]),(x,y,w*.15,h*.1),1)
            line((237,227,200),(w*.54,h*.73),(w*.88,h*.84),2)
    result = pygame.transform.smoothscale(s,(width,height))
    return result


def draw_person(surface, x, y, role='', scale=1):
    w,h=max(16,round(42*scale)),max(28,round(70*scale))
    surface.blit(artwork('person',w,h,role),(round(x-w/2),round(y-h+25*scale)))


def draw_building(surface, rect, name):
    w,h=rect.width+24,rect.height+32
    surface.blit(artwork('building',w,h,name),(rect.x-12,rect.y-28))


def draw_resource(surface, material, x, y, size):
    size=max(12,round(size))
    surface.blit(artwork('resource',size,size,material),(round(x-size/2),round(y-size/2)))


def decorate_room(surface, title):
    """Material grain and themed furnishings, baked into the existing room cache."""
    rng=random.Random(title)
    w,h=surface.get_size()
    for _ in range(900):
        x=rng.randrange(w); y=rng.randrange(410,h)
        pygame.draw.line(surface,(111,81,56),(x,y),(min(w-1,x+rng.randrange(3,18)),y))
    for x in (58,w-177):
        light=pygame.Surface((210,260),pygame.SRCALPHA)
        pygame.draw.polygon(light,(243,217,160,22),[(0,0),(95,0),(210,260),(20,260)])
        surface.blit(light,(x+12,285))
    for x in (235,660):
        pygame.draw.rect(surface,(47,35,26),(x,327,195,46),border_radius=4)
        for xx in range(x+5,x+190,18):
            pygame.draw.line(surface,(126,85,47),(xx,336),(xx,368),2)
        pygame.draw.rect(surface,(180,133,77),(x-3,318,201,14),border_radius=3)
        pygame.draw.line(surface,(218,175,111),(x,320),(x+193,320),2)
    if 'ТАВЕРНА' in title:
        for x in (270,315,710,755):
            pygame.draw.rect(surface,(42,70,52),(x,298,10,20),border_radius=2)
            pygame.draw.rect(surface,(190,167,119),(x+2,304,6,7))
        for x in (300,740):
            pygame.draw.ellipse(surface,(48,34,25),(x-45,493,100,23))
            pygame.draw.rect(surface,(72,46,29),(x-5,461,10,47))
            pygame.draw.ellipse(surface,(137,92,49),(x-48,447,96,37))
            pygame.draw.ellipse(surface,(187,138,76),(x-48,447,96,37),2)
    elif 'БАНК' in title:
        for x in (280,710):
            pygame.draw.rect(surface,(73,48,34),(x,310,35,7))
            pygame.draw.line(surface,(183,154,88),(x+17,308),(x+17,280),3)
            pygame.draw.line(surface,(183,154,88),(x,285),(x+35,285),2)
        pygame.draw.rect(surface,(118,44,39),(430,449,240,120),border_radius=3)
        pygame.draw.rect(surface,(190,149,81),(439,458,222,102),2)
    elif 'РЫНОК' in title or 'ЛАВКА' in title:
        for x in (35,w-170):
            for i,key in enumerate(('wood','stone','wool')):
                draw_resource(surface,key,x+32+i*42,395,36)
    elif 'ВЕРФЬ' in title:
        for x in (110,w-150):
            for r in (15,20,25,30):
                pygame.draw.circle(surface,(168,134,84),(x,520),r,2)


@lru_cache(maxsize=4)
def island_ground(width, height, hud_height):
    surface=pygame.Surface((width,height)).convert()
    surface.fill((65,118,133))
    land_bottom=height-112
    pygame.draw.rect(surface,(104,125,77),(0,hud_height,width,land_bottom-hud_height))
    rng=random.Random(2718)
    for _ in range(7000):
        x=rng.randrange(width); y=rng.randrange(hud_height,land_bottom)
        c=rng.choice(((112,131,83),(96,117,72),(118,133,86),(99,121,76)))
        pygame.draw.line(surface,c,(x,y),(x+rng.randrange(1,5),y))
    # A worn sand track connects the buildings without obscuring resource labels.
    pygame.draw.lines(surface,(150,142,105),False,[(0,488),(280,486),(560,477),(880,486),(width,487)],32)
    for _ in range(650):
        x=rng.randrange(width); y=rng.randrange(469,500)
        pygame.draw.circle(surface,rng.choice(((136,128,94),(163,153,115))),(x,y),1)
    for y in range(land_bottom-13,land_bottom+15):
        c=(174,161,120) if y<land_bottom else (147,150,116)
        pygame.draw.line(surface,c,(0,y),(width,y))
    for x in range(-20,width,42):
        pygame.draw.arc(surface,(158,188,176),(x,land_bottom+12,60,12),0,math.pi,1)
    return surface
