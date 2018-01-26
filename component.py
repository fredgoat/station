""" So basically, you spawn a component, which spawns corridors,
which define equipment areas and spawn airlocks, which spawn more components.
Then you fill in the equipment, according to that component's flava.
"""


# time.time() tells you what time it is (seconds since 1970)
# @ decorates a function with another function, so the first one runs inside the second
# import doctest? doctest.testmod() returns None if all fake Python sessions in comments in this module do what they say (like so)
'''
>>> place_character(['  ', '  '], (0, 1), 'x')
['  ', 'x ']
'''

import pdb         # pdb.set_trace() stops everything and lets you do pdb commands
import traceback   # traceback.print_stack() just prints the stack at that point

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

stations = []
outerSpace = {}
cardinals = ['n', 's', 'w', 'e']

winWidth        = 120      # window dimensions measured in tiles
winHeight       = 60
wIndex = (float(winWidth) / -2, float(winHeight) / -2)        # this is the upper left corner of a screen centered on (0,0)
winZoom         = 10      # how many pixels per tile
maxZoom         = 20
minZoom         = 3

""" Each station is an object with a list of components
each component is an object with an index, dimensions, doors, flavor, and equipment
index is a tuple, dimensions are two numbers, doors is a list of tuples,
flavor is a dict of numbers for each flavor, i.e. {'med': 5, 'sci': 2}
equipment is a list of dicts including coordinate, dimensions, type, and inventory
"""

clock = pygame.time.Clock()
mouse = {'pos':(0,0), 1:0, 2:0, 3:0, 4:0, 5:0, 6:0} # {position, button 1, button 2, etc}
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])

gameDisplay = pygame.display.set_mode((winWidth * winZoom, winHeight * winZoom))      # the actual window will start at ten pixels per tile
pygame.display.set_caption('Space Station')
backgroundColor = (0, 0, 0)
defaultTile = pygame.image.load('default tile.bmp').convert()           # these are now Surfaces, and converted to a nice /pixel/ format
corridorTile = pygame.image.load('corridor tile.bmp').convert()         # later if I have sprites I can set_colorkey((255,255,255)) to make the white parts transparent
airlockTile = pygame.image.load('airlock tile.bmp').convert()


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
        gameDisplay.fill(backgroundColor)                                              # ...on both screens
        window = filter(lambda coords: intdex[0]-2 <= coords[0] < (winWidth+20)*zoom + intdex[0] and intdex[1]-2 <= coords[1] < (winHeight+10)*zoom + intdex[1], space.keys())
        for point in window:            # then get all the relevant points from space
            m, n = point
            #self.grid[n - intdex[1]][m - intdex[0]] = space[(m, n)]
            if space[(m, n)] == '#':            # draw the 10x10 tiles on the window, accounting for window index
                gameDisplay.blit(pygame.transform.scale(defaultTile,(zoom, zoom)), (round((m - index[0]) * zoom), round((n - index[1]) * zoom)))
            elif space[(m, n)] == 'C':
                gameDisplay.blit(pygame.transform.scale(corridorTile,(zoom, zoom)), (round((m - index[0]) * zoom), round((n - index[1]) * zoom)))
            elif space[(m, n)] == 'A':
                gameDisplay.blit(pygame.transform.scale(airlockTile,(zoom, zoom)), (round((m - index[0]) * zoom), round((n - index[1]) * zoom)))

#    def border(self, border = 'X'):
#        for a in range(winWidth):
#            self.grid[0][a] = border
#            self.grid[winHeight - 1][a] = border
#        for b in range(winHeight):
#            self.grid[b][0] = border
#            self.grid[b][winWidth - 1] = border

#    def __repr__(self):                 # print it!
#        joined = ''
#        for y in self.grid:
#            line = ''
#            for x in y:
#                line += x
#                line += ' '
#            joined += line + '\n'
#        return joined


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


def is_area(space, coords, width, height, character=' '): # is this area completely blank?
    x, y = coords
    for ln in range(height):                    # is the area blocked at all?
        for pt in range(width):
            if not is_character(space, (x+pt, y+ln), character):
                return False
    return True


@check_return_not_none
def flood(space, coords, target, replacement):
    q = [coords]
    if not is_character(space, coords, target):          # are we starting with the right character?
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


def entry(space, coords, cwidth, cheight, door):    # this function gives the entry of a door, given its component's size and coords
    x, y = coords
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


def corridors_linked(space, coords, cwidth, cheight, doors):
    x, y = coords
    linked = True
    d = doors[0]
    m, n = entry(space, coords, cwidth, cheight, d)
    others = list(doors)
    others.remove(d)
    flood(space, (m,n), 'C', 'Z')                         # flood the first door's corridors with Zs
    for o in others:
        h, k = entry(space, coords, cwidth, cheight, o)
        if is_character(space, (h,k), 'C'):
            linked = False                  # are there any Cs left?  Then something's unattached.
    flood(space, (m,n), 'Z', 'C')
    return linked


@check_return_not_none
def link_corridors(space, coords, cwidth, cheight, doors, attempt=1):      # this fxn attempts to link the corridors in a component
    if attempt > 20 or len(doors) == 0:
        return space
    x, y = coords
    ndoors = filter(lambda coord: coord[1]==y-1,doors)              # north doors
    sdoors = filter(lambda coord: coord[1]==y+cheight,doors)        # south doors
    wdoors = filter(lambda coord: coord[0]==x-1,doors)              # west doors
    edoors = filter(lambda coord: coord[0]==x+cwidth,doors)         # east doors
    linked = True
    d = doors[0]
    m, n = entry(space, coords, cwidth, cheight, d)
    if corridors_linked(space, coords, cwidth, cheight, doors): # are they already linked?
        return space
    else:                                                       # Or are they unlinked?  Let's fix that
        flood(space, (m,n), 'C', 'Z')                           # flood the first door's corridors with Zs
        unattached = filter(lambda door: is_character(space, entry(space, coords, cwidth, cheight, door), 'C'), doors)
        attached = filter(lambda door: is_character(space, entry(space, coords, cwidth, cheight, door), 'Z'), doors)
        un = entry(space, coords, cwidth, cheight, unattached[randint(0, len(unattached) - 1)])
        at = entry(space, coords, cwidth, cheight, attached[randint(0, len(attached) - 1)])
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
            if corridors_linked(space, coords, cwidth, cheight, doors):
                return space
            else:               # that didn't work?!?
                print "Oops!  Having trouble linking the corridors in the component at", coords                     ####
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
            if corridors_linked(space, coords, cwidth, cheight, doors):   # did it work?
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
            if corridors_linked(space, coords, cwidth, cheight, doors):     # did THAT work?
                return space
        flood(space, (m,n), 'Z', 'C')  # fine!  Let's try closer to "un" and "at".
        link_corridors(space, coords, cwidth, cheight, doors, attempt + 1)
        return space


class Station(object):

    def spawn_component(self, cindex, flavor, doors, nsprob, ewprob):
        crashcount = 0
        while crashcount * (1+self.component_count) < 100:    # try this until you get it, but don't die.
            half_width  = randint(minCompWidth, maxCompWidth) / 2
            half_height = randint(minCompHeight, maxCompHeight) / 2
            crashcount += 1
            print "Component placement attempt", crashcount                                                         ####
            if random() < bigCompFreq:          # maybe this is a super big component?
                half_width  *= compMultiplier
                half_height *= compMultiplier
            cwidth = 2 * half_width + 1         # component width
            cheight = 2 * half_height + 1       # component height
            self.coordinates = (cindex[0] - 2 * half_width if cindex[2] == 'e' else cindex[0] if cindex[2] == 'w' \
            else cindex[0] - half_width, cindex[1] if cindex[2] == 'n' else cindex[1] - 2 * half_height \
            if cindex[2] == 's' else cindex[1] - half_height)
            x, y = self.coordinates             # coordinates = upper left corner; cindex = centerpoint spawned /from/ & direction spawned /from/
            if self.component_count > 0 and not doors:
                print "No doors!  Time to stop."
                break
            print "Doors were whittled down from", doors                                                            ####
            realdoors = filter(lambda d: (d[0] == self.coordinates[0] - 1 or d[0] == self.coordinates[0] + cwidth) and \
                                         (self.coordinates[1] <= d[1] <= self.coordinates[1] + cheight - 1) or \
                                         (d[1] == self.coordinates[1] - 1 or d[1] == self.coordinates[1] + cheight) and \
                                         (self.coordinates[0] <= d[0] <= self.coordinates[0] + cwidth - 1), doors)
            print "to", realdoors
            print "Should this component form?  So far we have", self.component_count                               ####
            if is_area(self.space, (self.coordinates[0]-1, self.coordinates[1]-1), cwidth+2, cheight+2) and not (self.component_count > 0 and not realdoors): # not blocked? still doors left?
                if random() < compFreq or self.component_count == 0:
                    self.component_count += 1
                    #for door in doors:
                    #    self.space[door] = 'A'
                    doors = realdoors
                    if cindex[2] == 'n' or cindex[2] == 's':
                        self.components.append(NSComponent(self.space, self, cindex, half_width, half_height, self.flavor, doors, nsprob, ewprob))
                    else:
                        self.components.append(WEComponent(self.space, self, cindex, half_width, half_height, self.flavor, doors, nsprob, ewprob))
                break
#            return space

    def __init__(self, space, stindex, flavor):
        self.space = space
        self.stindex = stindex
        self.flavor = flavor
        self.components = []
        self.component_count = 0
        self.spawn_component(self.stindex, self.flavor, [], random()*0.4+0.4, random()*0.4+0.4)
        pygame.display.update()


class Component(object):

    def place(self):
        x, y = self.coordinates
        print 'coordinates:', self.coordinates, 'extremity:', (x+self.width-1,y+self.height-1), 'width:', self.width, 'height:', self.height ####
        for ln in range(self.height):       # then place component
            for pt in range(self.width):
                self.space[(x+pt,y+ln)] = '#'

    def connect_deadends(self, deadends):           # corridors that end in a dead-end go to branches, and if branches don't link them we try here
        x, y = self.coordinates
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        ndoors = filter(lambda coord: coord[1]==y-1,self.doors)              # north doors
        sdoors = filter(lambda coord: coord[1]==y+cheight,self.doors)        # south doors
        wdoors = filter(lambda coord: coord[0]==x-1,self.doors)              # west doors
        edoors = filter(lambda coord: coord[0]==x+cwidth,self.doors)         # east doors
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

    def __init__(self, space, station, cindex, half_width, half_height, flavor, doors, nsprob, ewprob):
        self.space = space
        self.cindex = cindex
        self.flavor = flavor
        self.doors = doors
        self.nsprob = nsprob
        self.ewprob = ewprob
        self.station = station
        self.equipment = []
        self.half_width = half_width
        self.half_height = half_height
        self.width = 2 * half_width + 1
        self.height = 2 * half_height + 1
        self.coordinates = (cindex[0] - 2 * half_width if cindex[2] == 'e' else cindex[0] if cindex[2] == 'w' \
        else cindex[0] - half_width, cindex[1] if cindex[2] == 'n' else cindex[1] - 2 * half_height \
        if cindex[2] == 's' else cindex[1] - half_height)       # coordinates are at the top left, cindex is at the center on the spawning side, cindex[2] is direction spawning happens /from/
        self.place()

class NSComponent(Component):

    def spawn_webranches(self, deadends):
        x, y = self.coordinates
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        ndoors = filter(lambda coord: coord[1]==y-1,self.doors)              # north doors
        sdoors = filter(lambda coord: coord[1]==y+cheight,self.doors)        # south doors
        wdoors = filter(lambda coord: coord[0]==x-1,self.doors)              # west doors
        edoors = filter(lambda coord: coord[0]==x+cwidth,self.doors)         # east doors
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
            if not filter(lambda coord: coord[0]==x-1,self.doors):          # any west doors?
                direc.remove('w')
            if not filter(lambda coord: coord[0]==x+cwidth,self.doors):     # or east doors?
                direc.remove('e')
            while direc:
                tion = direc.pop(randint(0,len(direc)-1))                    # pick a direction and spawn some components!
                spawnx = self.coordinates[0]-2 if tion == 'e' else self.coordinates[0]+cwidth+1
                self.station.spawn_component((spawnx, self.coordinates[1]+self.half_height, tion), self.flavor, self.doors, self.nsprob, branchPersistence * self.ewprob)
        for door in self.doors:
            self.space[door] = 'A'
        print 'doors:', self.doors ####
        for end in deadends:
            print 'deadends abandoned:', end ####
            self.space[end] = 'C'
#        return space

    def spawn_nscorridors(self, space, cindex, half_width, half_height, flavor, nsprob, ewprob):
        x, y = self.coordinates                           # top left coordinates of the component
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        ndoors = filter(lambda coord: coord[1]==y-1,self.doors)          # north doors (each is an (x,y) just outside the comp)
        sdoors = filter(lambda coord: coord[1]==y+cheight,self.doors)      # south doors
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
                if cindex[2] == 's':       # do they start at the north, to mirror the door-spawned southern corridors?
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
                elif cindex[2] == 'n':                       # or at the south, to mirror the door-spawned norther corridors?
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
                    print "How did an nscorridor's cindex[2] become", cindex[2]                                     ####
        if newdoors:
            self.doors += newdoors
            self.station.spawn_component((cindex[0], cindex[1] + cheight + 1 if cindex[2] == 'n' else cindex[1] - cheight - 1, cindex[2]), \
                                         self.flavor, self.doors, nsprob * branchPersistence, ewprob)
        self.spawn_webranches(deadends)
#        return space

    def __init__(self, space, station, cindex, half_width, half_height, flavor, doors, nsprob, ewprob):
        Component.__init__(self, space, station, cindex, half_width, half_height, flavor, doors, nsprob, ewprob)
        self.spawn_nscorridors(space, cindex, half_width, half_height, flavor, nsprob, ewprob)
        link_corridors(space, self.coordinates, self.width, self.height, self.doors)
#       space = place_equipment(space, cindex, half_width, half_height, flavor)
#    return space

class WEComponent(Component):

    def spawn_nsbranches(self, deadends):
        x, y = self.coordinates
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        ndoors = filter(lambda coord: coord[1]==y-1,self.doors)              # north doors
        sdoors = filter(lambda coord: coord[1]==y+cheight,self.doors)        # south doors
        wdoors = filter(lambda coord: coord[0]==x-1,self.doors)              # west doors
        edoors = filter(lambda coord: coord[0]==x+cwidth,self.doors)         # east doors
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
            if not filter(lambda coord: coord[1]==y-1,self.doors):          # any north doors?
                direc.remove('n')
            if not filter(lambda coord: coord[1]==y+cheight,self.doors):    # or south doors?
                direc.remove('s')
            while direc:
                tion = direc.pop(randint(0,len(direc)-1))                    # pick a direction and spawn some components!
                spawny = self.coordinates[1]-2 if tion == 's' else self.coordinates[1]+cheight+1
                self.station.spawn_component((self.coordinates[0]+self.half_width, spawny, tion), self.flavor, self.doors, self.nsprob * branchPersistence, self.ewprob)
        for door in self.doors:
            self.space[door] = 'A'
        print 'doors:', self.doors ####
        for end in deadends:
            print 'deadends abandoned:', end ####
            self.space[end] = 'C'
#        return space

    def spawn_wecorridors(self, space, cindex, half_width, half_height, flavor, nsprob, ewprob):
        x, y = self.coordinates                               # top left coordinates of the component
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        wdoors = filter(lambda coord: coord[0]==x-1,self.doors)          # west doors (each is an (x,y) just outside the comp)
        edoors = filter(lambda coord: coord[0]==x+cwidth,self.doors)      # east doors
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
                if cindex[2] == 'e':       # do they start at the west, to mirror the door-spawned eastern corridors?
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
                elif cindex[2] == 'w':                       # or at the east, to mirror the door-spawned western corridors?
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
                    print "How did an ewcorridor's cindex[2] become", cindex[2]                                     ####
        if newdoors:
            self.doors += newdoors
            self.station.spawn_component((cindex[0]+cwidth+1 if cindex[2] == 'w' else cindex[0]-cwidth-1, cindex[1], cindex[2]), \
                                         self.flavor, self.doors, nsprob, ewprob * branchPersistence)
        self.spawn_nsbranches(deadends)
#        return space


    def __init__(self, space, station, cindex, half_width, half_height, flavor, doors, nsprob, ewprob):
        Component.__init__(self, space, station, cindex, half_width, half_height, flavor, doors, nsprob, ewprob)
        self.place()
        self.spawn_wecorridors(space, cindex, half_width, half_height, flavor, nsprob, ewprob)
        link_corridors(space, self.coordinates, self.width, self.height, self.doors)
#        space = place_equipment(space, cindex, half_width, half_height, flavor)
#    return space


grid = Grid(winWidth, winHeight)      # okay, make a blank ASCII matrix
gameDisplay.fill(backgroundColor)     # and a blank image window

stations.append(Station(outerSpace, (0, 0, cardinals[randint(0, 3)]), {}))  # (what region?, (origin x,origin y,from what direction?), what flavors?)

grid.update(wIndex, winZoom, outerSpace)              # put that space on the screen
#grid.border()                         # make it look nice
#print grid
game_loop(mouse, grid, wIndex, winZoom, outerSpace)  # run the game until the user hits the x
pygame.quit()  # if by some miracle you get here without that happening, quit immediately omg
quit()

#Do:  Make flavorful equipment!  Make controls!

# What flavors?  Cargo, Life Support, Propulsion, Power, Sensors, Comms, Fabrication, Reclamation, Quarters
# Medical?  Armory?  Science?  Weapons?
