""" So basically, you spawn a component, which spawns corridors,
which define equipment areas and spawn airlocks, which spawn more components.
Then you fill in the equipment, according to that component's flava.

Each station is an object with a list of components
each component is an object with a radix, dimensions, doors, flavor, and equipment
radix is a tuple, dimensions are two numbers, doors is a list of tuples,
flavor is a dict of numbers for each flavor, i.e. {'med': 5, 'sci': 2}
equipment is a list of dicts including index, dimensions, type, and inventory

Index = upper left point.  Extremity = lower right.  Coordinate = that point.  Radix = spawn root point.
"""

# __repr__(self) overrides what happens when you print a thing
# time.time() tells you what time it is (seconds since 1970)
# @ decorates a function with another function, so the first one runs inside the second

import pdb          # pdb.set_trace() stops everything and lets you do pdb commands
import traceback    # traceback.print_stack() just prints the stack at that point
import doctest      # doctest.testmod() returns None if all fake Python sessions in comments in this module return what they say, like so
'''
>>> function(*args)
returnvalue
'''

from random import random, randint, seed

super_seed = randint(1,1000)
print "This seed is", super_seed
seed(super_seed)    # this will let you go back to good randomnesses

import pygame
pygame.init()

branchPersistence = 0.8     # corridor branches persist (or die) by a power of this
compFreq         = 0.8     # probability that a door will actually spawn a component, rather than become exterior
minCompHeight   = 4       # component dimensions
minCompWidth    = 4
maxCompHeight   = 10
maxCompWidth    = 10
bigCompFreq     = 0.15    # how often are comps bigger than max & by what factor?
compMultiplier = 2

noFlavor = {'power':0, 'cargo':0, 'quarters':0, 'life support':0, 'medical':0, 'hydroponics':0, \
                 'command':0, 'reclamation':0, 'fabrication':0}
defaultFlavor = {'power':200, 'cargo':10, 'quarters':0, 'life support':10, 'medical':0, 'hydroponics':0, \
                 'command':0, 'reclamation':0, 'fabrication':0}
equipmentFlavors = {'power':{'converter':1}, 'cargo':{}, 'quarters':{}, 'life support':{}, 'medical':{}, 'hydroponics':{}, \
                 'command':{}, 'reclamation':{}, 'fabrication':{}}        # this is each flavor's equipment value per tile
equipmentLoot = {'converter': []}

stations = []
outerSpace = {}
cardinals = ['n', 'e', 's', 'w']

winWidth        = 120      # window dimensions measured in tiles
winHeight       = 60
wIndex = (float(winWidth) / -2, float(winHeight) / -2)        # this is the upper left corner of a screen centered on (0,0)
winZoom         = 10      # how many pixels per tile
maxZoom         = 20
minZoom         = 3

clock = pygame.time.Clock()
mouse = {'pos':(0,0), 1:0, 2:0, 3:0, 4:0, 5:0, 6:0} # {position, button 1, button 2, etc}
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])

gameDisplay = pygame.display.set_mode((winWidth * winZoom, winHeight * winZoom))      # the actual window will start at ten pixels per tile
pygame.display.set_caption('Space Station')
backgroundColor = (0, 0, 0)
background = pygame.image.load('background.bmp').convert()
defaultTile = pygame.image.load('default tile.bmp').convert()           # these are now Surfaces, and converted to a nice /pixel/ format
corridorTile = pygame.image.load('corridor tile.bmp').convert()         # later if I have sprites I can set_colorkey((255,255,255)) to make the white parts transparent
airlockTile = pygame.image.load('airlock tile.bmp').convert()
defaultPattern = pygame.Surface((winWidth * winZoom, winHeight * winZoom))
converterTile = pygame.image.load('converter tile.bmp').convert()


def patterner(background, tile, size):                      # this draws a repeating pattern out of tile images
    x = int(winWidth * winZoom / size[0] + 1)               # how many big ol' tiles fit side to side
    y = int(winHeight * winZoom / size[1] + 1)              # how many fit up and down
    for row in range(y):
        for spot in range(x):
            background.blit(tile, (spot * size[0], row * size[1]))      # blit that many in a pattern
    return background

class Tile(object):
    def __init__(self, tile, size):
        self.pattern = patterner(defaultPattern.copy(), pygame.transform.scale(tile, size), size)

converter = Tile(converterTile, (30,30))

drawnTiles = {'#': defaultTile, 'C': corridorTile, 'A': airlockTile, 'converter': converterTile}

def check_return_not_none(func):
    """A decorator for checking that a function is not returning None.
    If it is none, it will start a debugging session."""

    def decorated_function(*args):
        return_value = func(*args)
        if return_value is None:
            print 'Function "%s" returned None in' % func.__name__
            traceback.print_stack()
            pdb.set_trace()

        return return_value

    return decorated_function

def game_loop(mouse, grid, index, zoom, space):
    while True:
        for event in pygame.event.get():  # go as long as player doesn't hit the upper right x
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            elif pygame.mouse.get_focused():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse[event.button] = 1
                    mouse['pos'] = event.pos
                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse[event.button] = 0
                    mouse['pos'] = event.pos
                elif event.type == pygame.MOUSEMOTION:
                    mouse['pos'] = event.pos

                if mouse[1]:
                    x, y = pygame.mouse.get_rel()
                    index = (index[0] - min(max(float(x) / zoom, -10), 10), index[1] - min(max(float(y) / zoom, -10), 10))
                    grid.update(index, zoom, space)
                elif mouse[4] and zoom > minZoom:
                    index = (index[0]+winWidth*6/zoom, index[1]+winWidth*4/zoom)        # move the index toward the center
                    zoom -= zoom/5 + (zoom % 5 > 0)                                     # zoom out
                    index = (index[0]-winWidth*6/zoom, index[1]-winWidth*4/zoom)        # move the index back, net positive x and y change
                    grid.update(index, zoom, space)
                elif mouse[5] and zoom < maxZoom:
                    index = (index[0]+winHeight*10/zoom, index[1]+winHeight*10/zoom)
                    zoom = min(maxZoom, zoom + zoom/5 + (zoom % 5 > 0))
                    index = (index[0]-winHeight*10/zoom, index[1]-winHeight*10/zoom)
                    grid.update(index, zoom, space)

        pygame.display.update()  # redraw everything
        pygame.mouse.get_rel()
        clock.tick(60)  # allow 0.06 seconds to pass


class Grid(object):
    """The Grid is basically the screen or UI"""
    def __init__(self, width=winWidth, height=winHeight, character=' '):
        pass
        #self.grid = [[character for x in xrange(width)] for y in xrange(height)]

    """
    def ischar(self, coords, character=' '):
        x, y = coords
        line = self.grid[y]
        if y < 0:                       # is this in the grid?
            return False
        if x < 0:
            return False
        if y >= len(self.grid):
            return False
        if x >= len(line):
            return False
        if line[x] == character:        # is it the thing?
            return True
        else:
            return False """

    """
    def placechar(self, coords, character):
        x, y = coords
        self.grid[y][x] = character """

    def update(self, index, zoom, space, character=' '):
        "This wipes the screen, then fills in anything from that part of outerSpace"
        intdex = (int(round(index[0])), int(round(index[1])))
        #self.grid = [[character for x in xrange(winWidth*zoom)] for y in xrange(winHeight*zoom)] # blank slate
        gameDisplay.blit(background, (0, 0))
        window = filter(lambda coords: intdex[0]-2 <= coords[0] < (winWidth+20)*zoom + intdex[0] and intdex[1]-2 <= coords[1] < (winHeight+10)*zoom + intdex[1], space.keys())
        for point in window:            # then get all the relevant points from space
            m, n = point
            #self.grid[n - intdex[1]][m - intdex[0]] = space[(m, n)]
            # if space[(m, n)] == '#':            # draw the 10x10 tiles on the window, accounting for window index ... turn this into a function dict?
            #     gameDisplay.blit(pygame.transform.scale(defaultTile,(zoom, zoom)), (round((m - index[0]) * zoom), round((n - index[1]) * zoom)))
            # elif space[(m, n)] == 'C':
            #     gameDisplay.blit(pygame.transform.scale(corridorTile,(zoom, zoom)), (round((m - index[0]) * zoom), round((n - index[1]) * zoom)))
            # elif space[(m, n)] == 'A':
            #     gameDisplay.blit(pygame.transform.scale(airlockTile,(zoom, zoom)), (round((m - index[0]) * zoom), round((n - index[1]) * zoom)))
            gameDisplay.blit(pygame.transform.scale(drawnTiles[space[m,n]],(zoom, zoom)), (round((m - index[0]) * zoom), round((n - index[1]) * zoom)))
        nearby = filter(lambda x: x.space == space and intdex[0]-50 < x.stradix[0] < intdex[0]+(winWidth+100)*zoom \
                        and intdex[1]-50 < x.stradix[1] < intdex[1]+(winHeight+100)*zoom, stations)
        for station in nearby:
            for comp in station.components:
                for equip in comp.equipment:
                    gameDisplay.blit(pygame.transform.scale(converter.pattern, (winWidth * zoom, winHeight * zoom)), (round((equip['eindex'][0] - index[0]) * zoom), \
                                                        round((equip['eindex'][1] - index[1]) * zoom)), \
                                     pygame.Rect(0, 0, equip['width'] * zoom, equip['height'] * zoom))
                    # gameDisplay.blit(pygame.transform.scale(drawnTiles[equip['type']], (equip['width']*zoom, equip['height']*zoom)), \
                    #                                         (round((equip['eindex'][0] - index[0]) * zoom), \
                    #                                          round((equip['eindex'][1] - index[1]) * zoom)))


"""
   def border(self, border = 'X'):
       for a in range(winWidth):
           self.grid[0][a] = border
           self.grid[winHeight - 1][a] = border
       for b in range(winHeight):
           self.grid[b][0] = border
           self.grid[b][winWidth - 1] = border

   def __repr__(self):                 # print it!
       joined = ''
       for y in self.grid:
           line = ''
           for x in y:
               line += x
               line += ' '
           joined += line + '\n'
       return joined
"""


def go(coords, direction):
    if direction == 'n':
        return (coords[0], coords[1] - 1)
    elif direction == 'e':
        return (coords[0] + 1, coords[1])
    elif direction == 's':
        return (coords[0], coords[1] + 1)
    elif direction == 'w':
        return (coords[0] - 1, coords[1])
    else:
        print "invalid direction"


def replace(space, index, extremity, target, replacement):
    x = index[0]
    y = index[1]
    width = abs(extremity[0] - x) + 1
    height = abs(extremity[1] - y) + 1
    for n in range(height):
        for m in range(width):
            if is_character(space, (x+m, y+n), target):
                space[(x+m, y+n)] = replacement
    return space


def is_character(space, coords, character=' '): # epaulet?
    if not coords in space.keys():
        if ' ' == character:
            return True
        else:
            return False
    elif space[coords] == character:        # is it the thing?
        return True
    else:
        return False


def is_area(space, index, width, height, character=' '): # is this area completely blank?
    x, y = index
    for ln in range(height):                    # is the area blocked at all?
        for pt in range(width):
            if not is_character(space, (x+pt, y+ln), character):
                return False
    return True


def is_any(space, index, width, height, character):  # are there any of this thing in this area?
    x = index[0]
    y = index[1]
    for ln in range(height):
        for pt in range(width):
            if is_character(space, (x+pt, y+ln), character):
                return True
    return False


def block_off(space, index, half_width, half_height):
    width = 2 * half_width + 1
    height = 2 * half_height + 1
    blocks = []                     # these will be tuples of (index, width, height) in which equipment can be placed
    attempts = 0
    while attempts < 100 and is_any(space, index, width, height, '#'):      # while there's any '#' left
        attempts += 1
        spot = (index[0] + randint(0,width-1), index[1] + randint(0,height-1))      # pick a random spot
        if is_character(space, spot, '#'):                                              # and if it's got a '#'
            x, y = spot
            way = randint(0,3)
            direction = cardinals[way]                                      # pick a direction
            extremity = (0, 0)
            for a in xrange(2):         # try to circle twice
                for b in xrange(2):     # each circle is two L-turns
                    for c in xrange(2):                                         # go till you're blocked and turn counter-clockwise, twice
                        while is_character(space, go((x,y), direction), '#'):   # is the space you're about to go to still '#'?
                            x, y = go((x,y), direction)                         # go there
                        way -= 1                                                # dead end?  turn counter-clockwise
                        direction = cardinals[way]
                    if not b:
                        extremity = (x, y)                                          # you went and turned twice?  mark that spot, then continue
                if (x, y) == spot:                                              # if you wind up where you started, that's a block
                    h = min(extremity[0], x)
                    k = min(extremity[1], y)
                    m = max(extremity[0], x)
                    n = max(extremity[1], y)
                    blocks.append(((h,k), m - h + 1, n - k + 1))
                    replace(space, (h,k), (m,n), '#', '+')
                    break
                else:                                                           # if not, this is your new spot, try one more time
                    spot = (x, y)
                    way += 4
    replace(space, index, (index[0]+width-1, index[1]+height-1), '+', '#')
    print "Blocks are", blocks                                                                                        ####
    return blocks


def season(flavor):                                         # this boosts all existing flavors, adds some, and subtracts relative to total
    seasonings = 0
    for spice in flavor.keys():
        seasonings += max(0, flavor[spice])
    for spice in flavor.keys():
        flavor[spice] *= 2
        flavor[spice] += randint(0,30) - flavor[spice]/4
    return flavor


def flavor_add(base, addition):
    for spice in base.keys():
        base[spice] += addition[spice]
    return base


def flavor_subtract(base, subtraction):
    for spice in base.keys():
        base[spice] -= subtraction[spice]
    return base


@check_return_not_none
def flood(space, coords, target, replacement):          # this floods contiguous target characters with a replacement character
    q = [coords]                                        # turn our coords into a list of one set of coords, so we can do list stuff
    if not is_character(space, coords, target):         # are we starting with the right character?
        return space
    while q:
        co = q.pop(0)
        w = co
        e = co
        while is_character(space, (w[0]-1,w[1]), target):
            w = (w[0]-1, w[1])
        while is_character(space, (e[0]+1,e[1]), target):      # mark off a line
            e = (e[0]+1, e[1])
        for pt in range(e[0]-w[0]+1):
            space[(w[0]+pt,co[1])] = replacement                     # fill it in
            if is_character(space, (w[0]+pt,co[1]-1), target):
                q.append((w[0]+pt, co[1]-1))                         # add any "targets" to q if they're north of the filled point
            if is_character(space, (w[0]+pt,co[1]+1), target):
                q.append((w[0]+pt,co[1]+1))                          # ...or south
    return space


def entry(space, index, cwidth, cheight, door):    # this function gives the entry of a door, given its component's size and index
    x, y = index
    m, n = door
    if m == x-1:
        return (x,n)
    elif m == x+cwidth:
        return (x+cwidth-1,n)
    elif n == y-1:
        return (m,y)
    elif n == y+cheight:
        return (m,y+cheight-1)
    else:
        return False


def corridors_linked(space, index, cwidth, cheight, doors):
    x, y = index
    linked = True
    d = doors[0]
    m, n = entry(space, index, cwidth, cheight, d)
    others = list(doors)
    others.remove(d)
    flood(space, (m,n), 'C', 'Z')                         # flood the first door's corridors with Zs
    for o in others:
        h, k = entry(space, index, cwidth, cheight, o)
        if is_character(space, (h,k), 'C'):
            linked = False                  # are there any Cs left?  Then something's unattached.
    flood(space, (m,n), 'Z', 'C')
    return linked


@check_return_not_none
def link_corridors(space, index, cwidth, cheight, doors, attempt=1):      # this fxn attempts to link the corridors in a component
    if attempt > 20 or len(doors) == 0:
        return space
    x, y = index
    ndoors = filter(lambda coords: coords[1]==y-1,doors)              # north doors
    sdoors = filter(lambda coords: coords[1]==y+cheight,doors)        # south doors
    wdoors = filter(lambda coords: coords[0]==x-1,doors)              # west doors
    edoors = filter(lambda coords: coords[0]==x+cwidth,doors)         # east doors
    linked = True
    d = doors[0]
    m, n = entry(space, index, cwidth, cheight, d)
    if corridors_linked(space, index, cwidth, cheight, doors): # are they already linked?
        return space
    else:                                                       # Or are they unlinked?  Let's fix that
        flood(space, (m,n), 'C', 'Z')                           # flood the first door's corridors with Zs
        unattached = filter(lambda door: is_character(space, entry(space, index, cwidth, cheight, door), 'C'), doors)
        attached = filter(lambda door: is_character(space, entry(space, index, cwidth, cheight, door), 'Z'), doors)
        un = entry(space, index, cwidth, cheight, unattached[randint(0, len(unattached) - 1)])
        at = entry(space, index, cwidth, cheight, attached[randint(0, len(attached) - 1)])
        xunish = min(max(randint(x,x+cwidth/4), un[0]), randint(x+cwidth*3/4,x+cwidth-1))
        xatish = min(max(randint(x,x+cwidth/4), at[0]), randint(x+cwidth*3/4,x+cwidth-1))
        yunish = min(max(randint(y,y+cheight/4), un[1]), randint(y+cheight*3/4,y+cheight-1))
        yatish = min(max(randint(y,y+cheight/4), at[1]), randint(y+cheight*3/4,y+cheight-1))
        point = (randint(min(xunish,xatish), max(xunish,xatish)), randint(min(yunish, yatish), max(yunish, yatish)))
        point = (un[0] + int(round(float(point[0]-un[0])*(0.9**attempt))),
                 at[1] + int(round(float(point[1]-at[1])*(0.9**attempt)))) # the more attempts, the closer to x = C entry, y = Z entry
        p, q = point
        go = ['n','s','e','w']
        ways = {'n':'?', 's':'?', 'e':'?', 'w':'?'}
        for g in go:
            r = p
            s = q
            if g == 'n':                                # can we find a 'Z' and a 'C' from our point?  Try going North
                while s > y and not is_character(space, (p,s), 'Z') and not is_character(space, (p,s), 'C'):
                    s -= 1
                if is_character(space, (p,s), 'Z'):
                    ways[g] = 'Z'
                elif is_character(space, (p,s), 'C'):
                    ways[g] = 'C'
                elif s == y:
                    ways[g] = 'W'
            elif g == 's':                              # or South
                while s < y+cheight-1 and not is_character(space, (p,s), 'Z') and not is_character(space, (p,s), 'C'):
                    s += 1
                if is_character(space, (p,s), 'Z'):
                    ways[g] = 'Z'
                elif is_character(space, (p,s), 'C'):
                    ways[g] = 'C'
                elif s == y+cheight-1:
                    ways[g] = 'W'
            elif g == 'e':                              # or East
                while r < x+cwidth-1 and not is_character(space, (r,q), 'Z') and not is_character(space, (r,q), 'C'):
                    r += 1
                if is_character(space, (r,q), 'Z'):
                    ways[g] = 'Z'
                elif is_character(space, (r,q), 'C'):
                    ways[g] = 'C'
                elif r == x+cwidth-1:
                    ways[g] = 'W'
            elif g == 'w':                              # or West
                while r > x and not is_character(space, (r,q), 'Z') and not is_character(space, (r,q), 'C'):
                    r -= 1
                if is_character(space, (r,q), 'Z'):
                    ways[g] = 'Z'
                elif is_character(space, (r,q), 'C'):
                    ways[g] = 'C'
                elif r == x:
                    ways[g] = 'W'
        cways = filter(lambda dir: ways[dir]=='C', ways.keys())
        zways = filter(lambda dir: ways[dir]=='Z', ways.keys())
        if len(cways) != 0 and len(zways) != 0:                 # it worked?  So easy!  Let's connect them.
            linkways = [cways[randint(0,len(cways)-1)]] + [zways[randint(0,len(zways)-1)]]
            for way in linkways:
                r = p
                s = q
                if way == 'n':                           # go the way to the C or Z, and then connect "point" to the C or Z
                    s -= 1
                    while not is_character(space, (r,s), 'C') and not is_character(space, (r,s), 'Z'):
                        s -= 1
                    for k in range(q-s):
                        space[(p,q-k)] = 'Z'
                elif way == 's':
                    s += 1
                    while not is_character(space, (r,s), 'C') and not is_character(space, (r,s), 'Z'):
                        s += 1
                    for k in range(s-q):
                        space[(p,q+k)] = 'Z'
                elif way == 'e':
                    r += 1
                    while not is_character(space, (r,s), 'C') and not is_character(space, (r,s), 'Z'):
                        r += 1
                    for k in range(r-p):
                        space[(p+k,q)] = 'Z'
                else:
                    r -= 1
                    while not is_character(space, (r,s), 'C') and not is_character(space, (r,s), 'Z'):
                        r -= 1
                    for k in range(p-r):
                        space[(p-k,q)] = 'Z'
            flood(space, (m,n), 'Z', 'C')
            if corridors_linked(space, index, cwidth, cheight, doors):
                return space
            else:               # that didn't work?!?
                print "Oops!  Having trouble linking the corridors in the component at", index                     ####
        elif len(zways) != 0:
            for zw in zways:    # we can only see Zs from here?  Go past them and maybe we'll connect to Cs.
                r = p
                s = q
                if zw == 'n':
                    while not is_character(space, (r,s), 'C') and not s == y:
                        s -= 1
                    if is_character(space, (r,s), 'C'):
                        s += 1
                        while not is_character(space, (r,s), 'Z'):
                            space[(r,s)] = 'C'
                            s += 1
                elif zw == 's':
                    while not is_character(space, (r,s), 'C') and not s == y+cheight-1:
                        s += 1
                    if is_character(space, (r,s), 'C'):
                        s -= 1
                        while not is_character(space, (r,s), 'Z'):
                            space[(r,s)] = 'C'
                            s -= 1
                elif zw == 'e':
                    while not is_character(space, (r,s), 'C') and not r == x+cwidth-1:
                        r += 1
                    if is_character(space, (r,s), 'C'):
                        r -= 1
                        while not is_character(space, (r,s), 'Z'):
                            space[(r,s)] = 'C'
                            r -= 1
                else:
                    while not is_character(space, (r,s), 'C') and not r == x:
                        r -= 1
                    if is_character(space, (r,s), 'C'):
                        r += 1
                        while not is_character(space, (r,s), 'Z'):
                            space[(r,s)] = 'C'
                            r += 1
            flood(space, (m,n), 'Z', 'C')
            if corridors_linked(space, index, cwidth, cheight, doors):   # did it work?
                return space
        elif len(cways) != 0:
            for cw in cways:    # or maybe we can only see Cs?  Go past them and maybe we'll connect to Zs???
                r = p
                s = q
                if cw == 'n':
                    while not is_character(space, (r,s), 'Z') and not s == y:
                        s -= 1
                    if is_character(space, (r,s), 'Z'):
                        s += 1
                        while not is_character(space, (r,s), 'C'):
                            space[(r,s)] = 'Z'
                            s += 1
                elif cw == 's':
                    while not is_character(space, (r,s), 'Z') and not s == y+cheight-1:
                        s += 1
                    if is_character(space, (r,s), 'Z'):
                        s -= 1
                        while not is_character(space, (r,s), 'C'):
                            space[(r,s)] = 'Z'
                            s -= 1
                elif cw == 'e':
                    while not is_character(space, (r,s), 'Z') and not r == x+cwidth-1:
                        r += 1
                    if is_character(space, (r,s), 'Z'):
                        r -= 1
                        while not is_character(space, (r,s), 'C'):
                            space[(r,s)] = 'Z'
                            r -= 1
                else:
                    while not is_character(space, (r,s), 'Z') and not r == x:
                        r -= 1
                    if is_character(space, (r,s), 'Z'):
                        r += 1
                        while not is_character(space, (r,s), 'C'):
                            space[(r,s)] = 'Z'
                            r += 1
            flood(space, (m,n), 'Z', 'C')
            if corridors_linked(space, index, cwidth, cheight, doors):     # did THAT work?
                return space
        flood(space, (m,n), 'Z', 'C')  # fine!  Let's try closer to "un" and "at".
        link_corridors(space, index, cwidth, cheight, doors, attempt + 1)
        return space


class Station(object):
    """Stations spawn initial components"""
    def spawn_component(self, cradix, flavor, doors, nsprob, ewprob):
        crashcount = 0
        while crashcount * (1+self.component_count) < 100:    # try this until you get it, but don't die.
            half_width  = randint(minCompWidth, maxCompWidth) / 2
            half_height = randint(minCompHeight, maxCompHeight) / 2
            crashcount += 1
            if random() < bigCompFreq:          # maybe this is a super big component?
                half_width  *= compMultiplier
                half_height *= compMultiplier
            cwidth = 2 * half_width + 1         # component width
            cheight = 2 * half_height + 1       # component height
            index = (cradix[0] - 2 * half_width if cradix[2] == 'e' else cradix[0] if cradix[2] == 'w' \
            else cradix[0] - half_width, cradix[1] if cradix[2] == 'n' else cradix[1] - 2 * half_height \
            if cradix[2] == 's' else cradix[1] - half_height)
            x, y = index             # index = upper left corner; cradix = centerpoint spawned /from/ & direction spawned /from/
            if self.component_count > 0 and not doors:
                print "No doors!  Time to stop."
                break
            realdoors = filter(lambda d: (d[0] == index[0] - 1 or d[0] == index[0] + cwidth) and \
                                         (index[1] <= d[1] <= index[1] + cheight - 1) or \
                                         (d[1] == index[1] - 1 or d[1] == index[1] + cheight) and \
                                         (index[0] <= d[0] <= index[0] + cwidth - 1), doors)
            print "Should this component form?  So far we have", self.component_count                               ####
            if is_area(self.space, (index[0] - 1, index[1] - 1), cwidth + 2, cheight + 2) and not (self.component_count > 0 and not realdoors): # not blocked? still doors left?
                if random() < compFreq or self.component_count == 0:
                    self.component_count += 1
                    #for door in doors:
                    #    self.space[door] = 'A'
                    doors = realdoors
                    if cradix[2] == 'n' or cradix[2] == 's':
                        self.components.append(NSComponent(self.space, self, cradix, half_width, half_height, flavor, doors, nsprob, ewprob))
                    else:
                        self.components.append(WEComponent(self.space, self, cradix, half_width, half_height, flavor, doors, nsprob, ewprob))
                break

    def __init__(self, space, stradix, flavor):
        self.space = space
        self.stradix = stradix
        self.flavor = season(flavor)
        self.components = []
        self.component_count = 0
        self.spawn_component(self.stradix, self.flavor, [], random() * 0.4 + 0.4, random() * 0.4 + 0.4)     # ns and we probs are random between .4 and .8
        pygame.display.update()


class Component(object):

    def place(self):
        x, y = self.index
        print 'Component forming!  index:', self.index, 'extremity:', (x + self.width - 1, y + self.height - 1), 'width:', self.width, 'height:', self.height ####
        for ln in range(self.height):       # then place component
            for pt in range(self.width):
                self.space[(x+pt,y+ln)] = '#'

    def connect_deadends(self, deadends):           # corridors that end in a dead-end go to branches, and if branches don't link them we try here
        x, y = self.index
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        ndoors = filter(lambda coords: coords[1]==y-1,self.doors)              # north doors
        sdoors = filter(lambda coords: coords[1]==y+cheight,self.doors)        # south doors
        wdoors = filter(lambda coords: coords[0]==x-1,self.doors)              # west doors
        edoors = filter(lambda coords: coords[0]==x+cwidth,self.doors)         # east doors
        for end in deadends[:]:
            m,n = end
            if not is_character(self.space, end, 'c'):
                deadends.remove(end)
            else:
                go = ['n', 's', 'e', 'w']               # which directions will we look?
                if is_character(self.space, (m,n-1), 'C') or is_character(self.space, (m,n-1), 'c') or end in ndoors:
                    go.remove('n')
                if is_character(self.space, (m,n+1), 'C') or is_character(self.space, (m,n+1), 'c') or end in sdoors:
                    go.remove('s')
                if is_character(self.space, (m+1,n), 'C') or is_character(self.space, (m+1,n), 'c') or end in edoors:
                    go.remove('e')
                if is_character(self.space, (m-1,n), 'C') or is_character(self.space, (m-1,n), 'c') or end in wdoors:
                    go.remove('w')
                if len(go) < 3:
                    self.space[end] = 'C'
                    deadends.remove(end)
                else:
                    while len(go) > 0 and end in deadends:
                        g = go[randint(0,len(go)-1)]
                        go.remove(g)
                        if g == 'n':
                            k = n
                            while k >= y:
                                k -= 1
                                if is_character(self.space, (m,k), 'C') or is_character(self.space, (m,k), 'c'):
                                    deadends.remove(end)
                                    while k <= n:
                                        self.space[(m,k)] = 'C'
                                        k += 1
                                    break
                        elif g == 's':
                            k = n
                            while k <= y+cheight-1:
                                k += 1
                                if is_character(self.space, (m,k), 'C') or is_character(self.space, (m,k), 'c'):
                                    deadends.remove(end)
                                    while k >= n:
                                        self.space[(m,k)] = 'C'
                                        k -= 1
                                    break
                        elif g == 'e':
                            h = m
                            while h <= x+cwidth-1:
                                h += 1
                                if is_character(self.space, (h,n), 'C') or is_character(self.space, (h,n), 'c'):
                                    deadends.remove(end)
                                    while h >= m:
                                        self.space[(h,n)] = 'C'
                                        h -= 1
                                    break
                        else:
                            h = m
                            while h >= x:
                                h -= 1
                                if is_character(self.space, (h,n), 'C') or is_character(self.space, (h,n), 'c'):
                                    deadends.remove(end)
                                    while h <= m:
                                        self.space[(h,n)] = 'C'
                                        h += 1
                                    break
                        if len(deadends) == 0:
                            break

    def place_equipment(self):                              # this picks equipment based on the flavor, keeping track of what's already there
        seasonings = 0
        for spice in self.flavor.keys():
            seasonings += max(0, self.flavor[spice])                        # add up all the flavor in this component
        if not seasonings:
            print "no flavor for equipment!"    ####
        else:
            for block in block_off(self.space, self.index, self.half_width, self.half_height):  # divide it into blocks, this returns a list of blocks, each one (index, width, height)
                seas = randint(1,seasonings)
                flav = False
                attempts = 0
                flavs = self.flavor.keys()
                while seas > 0 and attempts < 100:                                 # pick a piece of equipment to place in each block
                    flav = flavs.pop()
                    seas -= max(0, self.flavor[flav])                   # pick a flavor from self.flavor
                    attempts += 1
                print "Tried", attempts, "different flavors, and have", seas, "seasoning left."            ####
                if equipmentFlavors[flav].keys():               # if this flavor even has any equipment to its name (remove this later?)
                    equip = equipmentFlavors[flav].keys()[randint(0,len(equipmentFlavors[flav].keys())-1)]
                    self.equipment.append({'eindex': block[0], 'width': block[1], 'height': block[2], 'type': equip, 'flavor': flav, 'inv': equipmentLoot[equip]})
                    print "Added new equipment", self.equipment[-1]
                    self.flavored[flav] += equipmentFlavors[flav][equip] * block[1] * block[2]        # add tile flavor * area to self.flavored


    def __init__(self, space, station, cradix, half_width, half_height, flavor, doors, nsprob, ewprob):
        self.space = space
        self.cradix = cradix
        self.flavor = season(flavor)        # the flavor the component wants to have (mutate it from that provided by the spawn source)
        self.doors = doors
        self.nsprob = nsprob
        self.ewprob = ewprob
        self.station = station
        self.equipment = []                 # equipment is a list of dicts including 'eindex', 'width', 'height', 'type', 'flavor', and 'inv': []
        self.half_width = half_width
        self.half_height = half_height
        self.width = 2 * half_width + 1
        self.height = 2 * half_height + 1
        self.index = (cradix[0] - 2 * half_width if cradix[2] == 'e' else cradix[0] if cradix[2] == 'w' \
        else cradix[0] - half_width, cradix[1] if cradix[2] == 'n' else cradix[1] - 2 * half_height \
        if cradix[2] == 's' else cradix[1] - half_height)       # index are at the top left, cradix is at the center on the spawning side, cradix[2] is direction spawning happens /from/
        self.place()
        self.flavored = noFlavor            # the flavor from the equipment placed

class NSComponent(Component):

    def spawn_webranches(self, deadends):
        x, y = self.index
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        ndoors = filter(lambda coords: coords[1]==y-1,self.doors)              # north doors
        sdoors = filter(lambda coords: coords[1]==y+cheight,self.doors)        # south doors
        wdoors = filter(lambda coords: coords[0]==x-1,self.doors)              # west doors
        edoors = filter(lambda coords: coords[0]==x+cwidth,self.doors)         # east doors
        branches = max(1,randint(cheight/5, int(cheight/3.5)), len(edoors) + len(wdoors))     # how many e/w corridors left?
        eokay = wokay = False
        if len(edoors) > 0:
            eokay = True
        if len(wdoors) > 0:
            wokay = True
        if random() < self.ewprob:
            tricoin = random()
            if tricoin > 0.3:
                eokay = True
            if tricoin < 0.7:
                wokay = True
        for ed in edoors:
            m, n = ed
            m -= 1
            cl = randint(cwidth/3, cwidth*2/3)
            while m >= x+cwidth-cl and not is_character(self.space, (m,n), 'C'):
                if m == x+cwidth-cl and is_character(self.space, (m,n+1), '#') \
                   and is_character(self.space, (m,n-1), '#') and is_character(self.space, (m-1,n), '#'):
                    self.space[(m,n)] = 'c'
                    deadends.append((m,n))
                else:
                    self.space[(m,n)] = 'C'
                m -= 1
            branches -= 1
        for wd in wdoors:
            m, n = wd
            m += 1
            cl = randint(cwidth/3, cwidth*2/3)
            while m <= x+cl-1 and not is_character(self.space, (m,n), 'C'):
                if m == x+cl-1 and is_character(self.space, (m,n+1), '#') \
                   and is_character(space, (m,n-1), '#') and is_character(self.space, (m+1,n), '#'):
                    self.space[(m,n)] = 'c'
                    deadends.append((m,n))
                else:
                    self.space[(m,n)] = 'C'
                m += 1
            branches -= 1
        newdoors = []
        if wokay == True or eokay == True:
            crashcount = 0
            while branches > 0 and crashcount < 100:        # place any other branches at random
                crashcount += 1
                spot = randint(0,cheight-1)
                if eokay and randint(0,1) == 1:       # do those start at the east?
                    if is_character(self.space, (x+cwidth-1,y+spot), '#') and not is_character(self.space, (x,y+spot+1), 'C') \
                       and not is_character(self.space, (x,y+spot-1), 'C') and not is_character(self.space, (x+cwidth-1,y+spot-1), 'C') \
                       and not is_character(self.space, (x+cwidth-1,y+spot+1), 'C'):
                        cl = randint(cwidth/3, cwidth*2/3)
                        m = x+cwidth-1
                        n = y+spot
                        newdoors.append((m+1,n))
                        while m >= x+cwidth-cl and not is_character(self.space, (m,n), 'C'):
                            if m == x+cwidth-cl and not (is_character(self.space, (m,n+1), 'C') or is_character(self.space, (m,n-1), 'C')):
                                self.space[(m,n)] = 'c'
                                deadends.append((m,n))
                            else:
                                self.space[(m,n)] = 'C'
                            m -= 1
                        branches -= 1
                elif wokay:                       # or west?
                    if is_character(self.space, (x,y+spot), '#') and not is_character(self.space, (x,y+spot+1), 'C') \
                       and not is_character(self.space, (x,y+spot-1), 'C') and not is_character(self.space, (x+cwidth-1,y+spot-1), 'C') \
                       and not is_character(self.space, (x+cwidth-1,y+spot+1), 'C'):
                        cl = randint(cwidth/3, cwidth*2/3)
                        m = x
                        n = y+spot
                        newdoors.append((m-1,n))
                        while m <= x+cl-1 and not is_character(self.space, (m,n), 'C'):
                            if m == x+cl-1 and not (is_character(self.space, (m,n+1), 'C') or is_character(self.space, (m,n-1), 'C')):
                                self.space[(m,n)] = 'c'
                                deadends.append((m,n))
                            else:
                                self.space[(m,n)] = 'C'
                            m += 1
                        branches -= 1
            if crashcount == 100: print 'couldn\'t place any more e/w branches'  ####
        print 'deadends', deadends ####
        self.connect_deadends(deadends)                 # now let's connect some dead-ends
        if newdoors:
            self.doors += newdoors
            direc = ['w', 'e']
            if not filter(lambda coords: coords[0]==x-1,self.doors):          # any west doors?
                direc.remove('w')
            if not filter(lambda coords: coords[0]==x+cwidth,self.doors):     # or east doors?
                direc.remove('e')
            while direc:
                tion = direc.pop(randint(0,len(direc)-1))                    # pick a direction and spawn some components!
                spawnx = self.index[0] - 2 if tion == 'e' else self.index[0] + cwidth + 1
                self.station.spawn_component((spawnx, self.index[1] + self.half_height, tion), \
                                             flavor_subtract(self.flavor, self.flavored), self.doors, \
                                             self.nsprob, branchPersistence * self.ewprob)
        for door in self.doors:
            self.space[door] = 'A'
        print 'doors:', self.doors ####
        for end in deadends:
            print 'deadends abandoned:', end ####
            self.space[end] = 'C'

    def spawn_nscorridors(self, space, cradix, half_width, half_height, flavor, nsprob, ewprob):
        x, y = self.index                           # top left index of the component
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        ndoors = filter(lambda coords: coords[1]==y-1,self.doors)          # north doors (each is an (x,y) just outside the comp)
        sdoors = filter(lambda coords: coords[1]==y+cheight,self.doors)      # south doors
        maincorridors = max(1,randint(cwidth/10, int(cwidth/3.5)), len(ndoors) + len(sdoors))     # how many n/s corridors left?
        deadends = []
        newdoors = []
        for nd in ndoors:               # place corridors spawned by north doors
            m, n = nd
            if is_character(space, (m,n+1), '#'):
                cl = min(randint(cheight/5, cheight*9/5), cheight)
                for c in range(cl):
                    space[(m,n+c+1)] = 'C'
                maincorridors -= 1
                if cl != cheight:
                    space[(m,n+cl)] = 'c'            # dead-ends get lowercase c
                    deadends.append((m,n+cl))
                else:
                    newdoors.append((m,n+cl+1))
        for sd in sdoors:               # place corridors spawned by south doors
            m, n = sd
            if is_character(space, (m,n-1), '#'):
                cl = min(randint(cheight/5, cheight*9/5), cheight)
                for c in range(cl):
                    space[(m,n-c-1)] = 'C'
                maincorridors -= 1
                if cl != cheight:
                    space[(m,n-cl)] = 'c'
                    deadends.append((m,n-cl))
                else:
                    newdoors.append((m,n-cl-1))
        if random() < nsprob or self.station.component_count == 1:
            while maincorridors > 0:        # place any other main corridors at random
                spot = randint(0,cwidth-1)
                if cradix[2] == 's':       # do they start at the north, to mirror the door-spawned southern corridors?
                    if is_character(space, (x+spot,y), '#') and not is_character(space, (x+spot+1,y), 'C') \
                       and not is_character(space, (x+spot-1,y), 'C') and not is_character(space, (x+spot-1,y+cheight-1), 'C') \
                       and not is_character(space, (x+spot+1,y+cheight-1), 'C'):
                        cl = min(randint(cheight/5, cheight*9/5), cheight)
                        for c in range(cl):
                            space[(x+spot,y+c)] = 'C'
                        maincorridors -= 1
                        newdoors.append((x+spot,y-1))
                        if cl != cheight:
                            space[(x+spot,y+cl-1)] = 'c'
                            deadends.append((x+spot,y+cl-1))
                        else:
                            newdoors.append((x+spot,y+cl))
                elif cradix[2] == 'n':                       # or at the south, to mirror the door-spawned norther corridors?
                    if is_character(space, (x+spot,y+cheight-1), '#') and not is_character(space, (x+spot+1,y), 'C') \
                       and not is_character(space, (x+spot-1,y), 'C') and not is_character(space, (x+spot-1,y+cheight-1), 'C') \
                       and not is_character(space, (x+spot+1,y+cheight-1), 'C'):
                        cl = min(randint(cheight/5, cheight*9/5), cheight)
                        for c in range(cl):
                            space[(x+spot,y+cheight-c-1)] = 'C'
                        maincorridors -= 1
                        newdoors.append((x+spot,y+cheight))
                        if cl != cheight:
                            space[(x+spot,y+cheight-cl)] = 'c'
                            deadends.append((x+spot,y+cheight-cl))
                        else:
                            newdoors.append((x+spot,y+cheight-cl-1))
                else:
                    print "How did an nscorridor's cradix[2] become", cradix[2]                                     ####
        if newdoors:
            self.doors += newdoors
            self.station.spawn_component((cradix[0], cradix[1] + cheight + 1 if cradix[2] == 'n' else cradix[1] - cheight - 1, cradix[2]), \
                                         flavor_subtract(self.flavor, self.flavored), self.doors, nsprob * branchPersistence, ewprob)
        self.spawn_webranches(deadends)

    def __init__(self, space, station, cradix, half_width, half_height, flavor, doors, nsprob, ewprob):
        Component.__init__(self, space, station, cradix, half_width, half_height, flavor, doors, nsprob, ewprob)
        self.spawn_nscorridors(space, cradix, half_width, half_height, flavor, nsprob, ewprob)
        link_corridors(space, self.index, self.width, self.height, self.doors)
        space = self.place_equipment()

class WEComponent(Component):

    def spawn_nsbranches(self, deadends):
        x, y = self.index
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        ndoors = filter(lambda coords: coords[1]==y-1,self.doors)              # north doors
        sdoors = filter(lambda coords: coords[1]==y+cheight,self.doors)        # south doors
        wdoors = filter(lambda coords: coords[0]==x-1,self.doors)              # west doors
        edoors = filter(lambda coords: coords[0]==x+cwidth,self.doors)         # east doors
        branches = max(1,randint(cwidth/5, int(cwidth/3.5)), len(ndoors) + len(sdoors))     # how many n/s corridors left?
        nokay = sokay = False
        if len(ndoors) > 0:
            nokay = True
        if len(sdoors) > 0:
            sokay = True
        if random() < self.nsprob:
            tricoin = random()
            if tricoin > 0.3:
                nokay = True
            if tricoin < 0.7:
                sokay = True
        for sd in sdoors:
            m, n = sd
            n -= 1
            cl = randint(cheight/3, cheight*2/3)
            while n >= y+cheight-cl and not is_character(self.space, (m,n), 'C'):
                if n == y+cheight-cl and is_character(self.space, (m+1,n), '#') \
                   and is_character(self.space, (m-1,n), '#') and is_character(self.space, (m,n-1), '#'):
                    self.space[(m,n)] = 'c'
                    deadends.append((m,n))
                else:
                    self.space[(m,n)] = 'C'
                n -= 1
            branches -= 1
        for nd in ndoors:
            m, n = nd
            n += 1
            cl = randint(cheight/3, cheight*2/3)
            while n <= y+cl-1 and not is_character(self.space, (m,n), 'C'):
                if n == y+cl-1 and is_character(self.space, (m+1,n), '#') \
                   and is_character(space, (m-1,n), '#') and is_character(self.space, (m,n+1), '#'):
                    self.space[(m,n)] = 'c'
                    deadends.append((m,n))
                else:
                    self.space[(m,n)] = 'C'
                n += 1
            branches -= 1
        newdoors = []
        if nokay == True or sokay == True:
            crashcount = 0
            while branches > 0 and crashcount < 100:        # place any other branches at random
                crashcount += 1
                spot = randint(0,cwidth-1)
                if sokay and randint(0,1) == 1:       # do those start at the south?
                    if is_character(self.space, (x+spot,y+cheight-1), '#') and not is_character(self.space, (x+spot+1,y), 'C') \
                       and not is_character(self.space, (x+spot-1,y), 'C') and not is_character(self.space, (x+spot-1,y+cheight-1), 'C') \
                       and not is_character(self.space, (x+spot+1,y+cheight-1), 'C'):
                        cl = randint(cheight/3, cheight*2/3)
                        m = x+spot
                        n = y+cheight-1
                        newdoors.append((m,n+1))
                        while n >= y+cheight-cl and not is_character(self.space, (m,n), 'C'):
                            if n == y+cheight-cl and not (is_character(self.space, (m+1,n), 'C') or is_character(self.space, (m-1,n), 'C')):
                                self.space[(m,n)] = 'c'
                                deadends.append((m,n))
                            else:
                                self.space[(m,n)] = 'C'
                            n -= 1
                        branches -= 1
                elif nokay:                       # or north?
                    if is_character(self.space, (x+spot,y), '#') and not is_character(self.space, (x+spot+1,y), 'C') \
                       and not is_character(self.space, (x+spot-1,y), 'C') and not is_character(self.space, (x+spot-1,y+cheight-1), 'C') \
                       and not is_character(self.space, (x+spot+1,y+cheight-1), 'C'):
                        cl = randint(cheight/3, cheight*2/3)
                        n = y
                        m = x+spot
                        newdoors.append((m,n-1))
                        while n <= y+cl-1 and not is_character(self.space, (m,n), 'C'):
                            if n == y+cl-1 and not (is_character(self.space, (m+1,n), 'C') or is_character(self.space, (m-1,n), 'C')):
                                self.space[(m,n)] = 'c'
                                deadends.append((m,n))
                            else:
                                self.space[(m,n)] = 'C'
                            n += 1
                        branches -= 1
            if crashcount == 100: print 'couldn\'t place any more e/w branches'  ####
        print 'deadends', deadends ####
        self.connect_deadends(deadends)                 # now let's connect some dead-ends
        if newdoors:
            self.doors += newdoors
            direc = ['n', 's']
            if not filter(lambda coords: coords[1]==y-1,self.doors):          # any north doors?
                direc.remove('n')
            if not filter(lambda coords: coords[1]==y+cheight,self.doors):    # or south doors?
                direc.remove('s')
            while direc:
                tion = direc.pop(randint(0,len(direc)-1))                    # pick a direction and spawn some components!
                spawny = self.index[1] - 2 if tion == 's' else self.index[1] + cheight + 1
                self.station.spawn_component((self.index[0] + self.half_width, spawny, tion), \
                                             flavor_subtract(self.flavor, self.flavored), self.doors, \
                                             self.nsprob * branchPersistence, self.ewprob)
        for door in self.doors:
            self.space[door] = 'A'
        print 'doors:', self.doors ####
        for end in deadends:
            print 'deadends abandoned:', end ####
            self.space[end] = 'C'

    def spawn_wecorridors(self, space, cradix, half_width, half_height, flavor, nsprob, ewprob):
        x, y = self.index                               # top left index of the component
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        wdoors = filter(lambda coords: coords[0]==x-1,self.doors)          # west doors (each is an (x,y) just outside the comp)
        edoors = filter(lambda coords: coords[0]==x+cwidth,self.doors)      # east doors
        maincorridors = max(1,randint(cheight/10, int(cheight/3.5)), len(wdoors) + len(edoors))     # how many w/e corridors left?
        deadends = []
        newdoors = []
        for wd in wdoors:               # place corridors spawned by west doors
            m, n = wd
            if is_character(space, (m+1,n), '#'):
                cl = min(randint(cwidth/5, cwidth*9/5), cwidth)
                for c in range(cl):
                    space[(m+c+1,n)] = 'C'
                maincorridors -= 1
                if cl != cwidth:
                    space[(m+cl,n)] = 'c'            # dead-ends get lowercase c
                    deadends.append((m+cl,n))
                else:
                    newdoors.append((m+cl+1,n))
        for ed in edoors:               # place corridors spawned by east doors
            m, n = ed
            if is_character(space, (m-1,n), '#'):
                cl = min(randint(cwidth/5, cwidth*9/5), cwidth)
                for c in range(cl):
                    space[(m-c-1,n)] = 'C'
                maincorridors -= 1
                if cl != cwidth:
                    space[(m-cl,n)] = 'c'
                    deadends.append((m-cl,n))
                else:
                    newdoors.append((m-cl-1,n))
        if random() < ewprob or self.station.component_count == 1:
            while maincorridors > 0:        # place any other main corridors at random
                spot = randint(0,cheight-1)
                if cradix[2] == 'e':       # do they start at the west, to mirror the door-spawned eastern corridors?
                    if is_character(space, (x,y+spot), '#') and not is_character(space, (x,y+spot+1), 'C') \
                       and not is_character(space, (x,y+spot-1), 'C') and not is_character(space, (x+cwidth-1,y+spot-1), 'C') \
                       and not is_character(space, (x+cwidth-1,y+spot+1), 'C'):
                        cl = min(randint(cwidth/5, cwidth*9/5), cwidth)
                        for c in range(cl):
                            space[(x+c,y+spot)] = 'C'
                        maincorridors -= 1
                        newdoors.append((x-1,y+spot))
                        if cl != cwidth:
                            space[(x+cl-1,y+spot)] = 'c'
                            deadends.append((x+cl-1,y+spot))
                        else:
                            newdoors.append((x+cl,y+spot))
                elif cradix[2] == 'w':                       # or at the east, to mirror the door-spawned western corridors?
                    if is_character(space, (x+cwidth-1,y+spot), '#') and not is_character(space, (x,y+spot+1), 'C') \
                       and not is_character(space, (x,y+spot-1), 'C') and not is_character(space, (x+cwidth-1,y+spot-1), 'C') \
                       and not is_character(space, (x+cwidth-1,y+spot+1), 'C'):
                        cl = min(randint(cwidth/5, cwidth*9/5), cwidth)
                        for c in range(cl):
                            space[(x+cwidth-c-1,y+spot)] = 'C'
                        maincorridors -= 1
                        newdoors.append((x+cwidth,y+spot))
                        if cl != cwidth:
                            space[(x+cwidth-cl,y+spot)] = 'c'
                            deadends.append((x+cwidth-cl,y+spot))
                        else:
                            newdoors.append((x+cwidth-cl-1,y+spot))
                else:
                    print "How did an ewcorridor's cradix[2] become", cradix[2]                                     ####
        if newdoors:
            self.doors += newdoors
            self.station.spawn_component((cradix[0] + cwidth + 1 if cradix[2] == 'w' else cradix[0] - cwidth - 1, cradix[1], cradix[2]), \
                                         flavor_subtract(self.flavor, self.flavored), self.doors, nsprob, ewprob * branchPersistence)
        self.spawn_nsbranches(deadends)


    def __init__(self, space, station, cradix, half_width, half_height, flavor, doors, nsprob, ewprob):
        Component.__init__(self, space, station, cradix, half_width, half_height, flavor, doors, nsprob, ewprob)
        self.spawn_wecorridors(space, cradix, half_width, half_height, flavor, nsprob, ewprob)
        link_corridors(space, self.index, self.width, self.height, self.doors)
        space = self.place_equipment()

grid = Grid(winWidth, winHeight)      # okay, make a blank ASCII matrix
gameDisplay.fill(backgroundColor)     # and a blank image window

stations.append(Station(outerSpace, (0, 0, cardinals[randint(0, 3)]), defaultFlavor))  # (what region?, (origin x,origin y,from what direction?), what flavors?)

grid.update(wIndex, winZoom, outerSpace)              # put that space on the screen

game_loop(mouse, grid, wIndex, winZoom, outerSpace)  # run the game until the user hits the x
pygame.quit()  # if by some miracle you get here without that happening, quit immediately omg
quit()

#Do:  Add more equipment! (equipmentFlavors, Loot, what else?)  Photoshop some actual equipment?  Make UI/controls!

# What other flavors?  Armory?  Science?  Propulsion?
