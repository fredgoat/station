# python Documents\GitHub\station\compo.py
""" So basically, you spawn a component, which spawns corridors,
which define equipment areas and spawn airlocks, which spawn more components.
Then you fill in the equipment, according to that component's flava.
"""

# time.time() @ decorates a function with another function, so the first one runs inside the second

# import doctest
# doctest.testmod() returns None if all fake Python sessions in comments in this module do what they say (like so)
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

decay           = 0.8     # component branches die off by a power of this
winwidth        = 40      # window dimensions
winheight       = 70
mincompheight   = 4       # component dimensions
mincompwidth    = 4
maxcompheight   = 10
maxcompwidth    = 10
bigcompfreq     = 0.15    # how often are comps bigger than max & by what factor?
comp_multiplier = 2

outer_space = {}
windex = (winwidth/-2,-3)
stations = []
"""Each station is a list of components
each component is a dict including index, dimensions, doors, flavor, and equipment
index is a tuple, dimensions are two numbers, doors is a list of tuples, flavor is a dict of numbers for each flavor,
equipment is a list of dicts including coordinate, dimensions, type, and inventory"""


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


class Grid(object):
    """The Grid is basically the screen or UI"""
    def __init__(self, width=winwidth, height=winheight, character=' '):
        self.grid = [[character for x in xrange(width)] for y in xrange(height)]

    def ischar(self, coordinate, character=' '):
        x, y = coordinate
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
            return False

    def placechar(self, coordinate, character):
        x, y = coordinate
        self.grid[y][x] = character

    def update(self, space, character=' '):
        "This wipes the screen, then fills in anything from that part of outer_space"
        self.grid = [[character for x in xrange(winwidth)] for y in xrange(winheight)] # blank slate
        window = filter(lambda x: windex[0]<=x[0]<winwidth+windex[0] and windex[1]<=x[1]<winheight+windex[1], space.keys())
        for point in window:            # then get all the relevant points from space
            m, n = point
            self.grid[n-windex[1]][m-windex[0]] = space[(m,n)]

    def border(self, border = 'X'):
        for a in range(winwidth):
            self.grid[0][a] = border
            self.grid[winheight-1][a] = border
        for b in range(winheight):
            self.grid[b][0] = border
            self.grid[b][winwidth-1] = border

    def __repr__(self):                 # print it!
        joined = ''
        for y in self.grid:
            line = ''
            for x in y:
                line += x
                line += ' '
            joined += line + '\n'
        return joined


def is_character(space, coordinate, character=' '):
    if not coordinate in space.keys():
        if ' ' == character:
            return True
        else:
            return False
    elif space[coordinate] == character:        # is it the thing?
        return True
    else:
        return False


def is_area(space, coordinate, width, height, character=' '):
    x, y = coordinate
    for ln in range(height):       # is the area blocked?
        for pt in range(width):
            if not is_character(space, (x+pt, y+ln), character):
                return False
    return True


@check_return_not_none
def flood(space, coordinate, target, replacement):
    q = [coordinate]
    if not is_character(space, coordinate, target):          # are we starting with the right character?
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


def entry(space, coordinate, cwidth, cheight, door):    # this function gives the entry of a door, given its component's size and coordinate
    x, y = coordinate
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


def corridors_linked(space, coordinate, cwidth, cheight, doors):
    x, y = coordinate
    linked = True
    d = doors[0]
    m, n = entry(space, coordinate, cwidth, cheight, d)
    others = list(doors)
    others.remove(d)
    flood(space, (m,n), 'C', 'Z')                         # flood the first door's corridors with Zs
    for o in others:
        h, k = entry(space, coordinate, cwidth, cheight, o)
        if is_character(space, (h,k), 'C'):
            linked = False                  # are there any Cs left?  Then something's unattached.
    flood(space, (m,n), 'Z', 'C')
    return linked


@check_return_not_none
def link_corridors(space, coordinate, cwidth, cheight, doors, attempt=1):      # this fxn attempts to link the corridors in a component
    if attempt > 20 or len(doors) == 0:
        return space
    x, y = coordinate
    ndoors = filter(lambda coord: coord[1]==y-1,doors)              # north doors
    sdoors = filter(lambda coord: coord[1]==y+cheight,doors)        # south doors
    wdoors = filter(lambda coord: coord[0]==x-1,doors)              # west doors
    edoors = filter(lambda coord: coord[0]==x+cwidth,doors)         # east doors
    linked = True
    d = doors[0]
    m, n = entry(space, coordinate, cwidth, cheight, d)
    if corridors_linked(space, coordinate, cwidth, cheight, doors): # are they already linked?
        print 'linked before attempt', attempt ####
        return space
    else:                                                       # Or are they unlinked?  Let's fix that
        flood(space, (m,n), 'C', 'Z')                           # flood the first door's corridors with Zs
        unattached = filter(lambda door: is_character(space, entry(space, coordinate, cwidth, cheight, door), 'C'), doors)
        attached = filter(lambda door: is_character(space, entry(space, coordinate, cwidth, cheight, door), 'Z'), doors)
        un = entry(space, coordinate, cwidth, cheight, unattached[randint(0,len(unattached)-1)])
        at = entry(space, coordinate, cwidth, cheight, attached[randint(0,len(attached)-1)])
        print 'un:', un, 'at:', at ####
        xunish = min(max(randint(x,x+cwidth/4), un[0]), randint(x+cwidth*3/4,x+cwidth-1))
        xatish = min(max(randint(x,x+cwidth/4), at[0]), randint(x+cwidth*3/4,x+cwidth-1))
        yunish = min(max(randint(y,y+cheight/4), un[1]), randint(y+cheight*3/4,y+cheight-1))
        yatish = min(max(randint(y,y+cheight/4), at[1]), randint(y+cheight*3/4,y+cheight-1))
        point = (randint(min(xunish,xatish), max(xunish,xatish)), randint(min(yunish, yatish), max(yunish, yatish)))
        point = (un[0] + int(round(float(point[0]-un[0])*(0.9**attempt))),
                 at[1] + int(round(float(point[1]-at[1])*(0.9**attempt)))) # the more attempts, the closer to x = C entry, y = Z entry
        print "point:", point ####
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
            if corridors_linked(space, coordinate, cwidth, cheight, doors):
                print 'linked on first try of attempt', attempt ####
                return space
            else:               # that didn't work?!?
                print "something's still not linked"
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
            if corridors_linked(space, coordinate, cwidth, cheight, doors):   # did it work?
                print 'linked after overshooting a Z on attempt', attempt ####
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
            if corridors_linked(space, coordinate, cwidth, cheight, doors):     # did THAT work?
                print 'linked after overshooting a C on attempt', attempt ####
                return space
        flood(space, (m,n), 'Z', 'C')  # fine!  Let's try closer to "un" and "at".
        link_corridors(space, coordinate, cwidth, cheight, doors, attempt+1)
        return space

class Station(object):

    def spawn_nscomponent(self, cindex, flavor, doors, nsprob, ewprob):
        crashcount = 0
        while crashcount * (1+len(self.components)) < 100:    # try this until you get it, but don't die.
            half_width  = randint(mincompwidth + 3, maxcompwidth) / 2
            half_height = randint(mincompheight, maxcompheight - 6) / 2
            crashcount += 1
            if random() < bigcompfreq:          # maybe this is a super big component?
                half_width  *= comp_multiplier
                half_height *= comp_multiplier
            cwidth = 2 * half_width + 1
            cheight = 2 * half_height + 1
            x = cindex[0] - half_width
            if cindex[2] == 'n':
                y = cindex[1]
            elif cindex[2] == 's':
                y = cindex[1] - 2 * half_height
            else:
                print "How can the orientation of a nscomponent be", cindex[2]
            coordinate = (x, y)                 # coordinate is the upper left corner; cindex is the origin & orientation
            print "Doors were whittled down from", doors
            doors = filter(lambda d: (d[0] == coordinate[0] - 1 or d[0] == coordinate[0] + cwidth) and \
                                     (coordinate[1] <= d[1] <= coordinate[1] + cheight - 1) or \
                                     (d[1] == coordinate[1] - 1 or d[1] == coordinate[1] + cheight) and \
                                     (coordinate[0] <= d[0] <= coordinate[0] + cwidth - 1), doors)
            print "to", doors
            if len(self.components) > 0 and not doors:
                break
            if is_area(self.space, coordinate, cwidth, cheight) and (len(self.components) == 0 or doors): # not blocked? good doors?
                self.components.append(NSComponent(self.space, self, cindex, half_width, half_height, self.flavor, doors, nsprob, ewprob))
                break
#            return space

    def __init__(self, space, stindex, flavor):
        self.space = space
        self.stindex = stindex
        self.flavor = flavor
        self.components = []
        self.spawn_nscomponent(self.stindex, self.flavor, [], 1.0, 0.3)


class NSComponent(object):

    def spawn_ewbranches(self, deadends):
        x = self.cindex[0] - self.half_width
        y = self.cindex[1]
        coordinate = (x, y)
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
        for end in deadends[:]:                            # now let's connect some dead-ends
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
#        for d in newdoors:
#            doors.append(d)
        if newdoors:
            self.doors += newdoors
#            place_ewcomponent(space, (coordinate[0]+cwidth+1, cindex[1]+half_height, 'e' or 'w' but filter newdoors to decide?), flavor, doors, nsprob*decay, ewprob)
        print 'doors:', self.doors ####
        for end in deadends:
            print 'deadends abandoned:', end ####
            self.space[end] = 'C'
#        return space

    def spawn_nscorridors(self, space, station, cindex, half_width, half_height, flavor, nsprob, ewprob):
        x = cindex[0] - half_width
        y = cindex[1]
        coordinate = (x, y)                               # top left coordinate of the component
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        doors = self.doors
        ndoors = filter(lambda coord: coord[1]==y-1,doors)          # north doors (each is an (x,y) just outside the comp)
        sdoors = filter(lambda coord: coord[1]==y+cheight,doors)      # south doors
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
        if random() < nsprob:
            while maincorridors > 0:        # place any other main corridors at random
                spot = randint(0,cwidth-1)
                if cindex[2] == 's':       # do they start at the north?
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
                elif cindex[2] == 'n':                       # or south?
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
                    print "How did an nscorridor's cindex[2] become", cindex[2]
        if newdoors:
            self.doors += newdoors
            station.spawn_nscomponent((cindex[0], cindex[1]+cheight+1, cindex[2]), self.flavor, self.doors, nsprob*decay, ewprob)
        self.spawn_ewbranches(deadends)
#        return space

    def __init__(self, space, station, cindex, half_width, half_height, flavor, doors, nsprob, ewprob):
        self.space = space
        self.cindex = cindex
        self.flavor = flavor
        self.doors = doors
        self.nsprob = nsprob
        self.ewprob = ewprob
        self.station = len(stations)
        self.equipment = []
        self.half_width = half_width
        self.half_height = half_height
        self.width = 2 * half_width + 1
        self.height = 2 * half_height + 1
        x = cindex[0] - half_width
        if cindex[2] == 'n':
            y = cindex[1]
        elif cindex[2] == 's':
            y = cindex[1] - 2 * half_height
        print 'coordinate:', (x, y), 'extremity:', (x+self.width-1,y+self.height-1), 'width:', self.width, 'height:', self.height ####
        for ln in range(self.height):       # then place component
            for pt in range(self.width):
                space[(x+pt,y+ln)] = '#'
        self.spawn_nscorridors(space, station, cindex, half_width, half_height, flavor, nsprob, ewprob)
        link_corridors(space, (x, y), self.width, self.height, self.doors)
#       space = place_equipment(space, cindex, half_width, half_height, flavor)
#    return space


def generate_station(space, stindex, flavor):
    stations.append([])
    place_nscomponent(space, stindex, flavor, [], 1.0, 0.3)
    return space


@check_return_not_none
def place_nscomponent(space, cindex, flavor, doors, nsprob, ewprob):
    crashcount = 0
    while crashcount * (1+len(stations[-1])) < 100:    # try this until you get it, but don't die.
        half_width  = randint(mincompwidth + 3, maxcompwidth) / 2
        half_height = randint(mincompheight, maxcompheight - 6) / 2
        crashcount += 1
        if random() < bigcompfreq:          # maybe this is a super big component?
            half_width  *= comp_multiplier
            half_height *= comp_multiplier
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        x = cindex[0] - half_width
        if cindex[2] == 'n':
            y = cindex[1]
        elif cindex[2] == 's':
            y = cindex[1] - 2 * half_height
        else:
            print "How can the orientation of a nscomponent be", cindex[2]
        coordinate = (x, y)                 # coordinate is the upper left corner; cindex is the origin & orientation
        print "Doors were whittled down from", doors
        doors = filter(lambda d: (d[0] == coordinate[0] - 1 or d[0] == coordinate[0] + cwidth) and \
                                  (coordinate[1] <= d[1] <= coordinate[1] + cheight - 1) or \
                                 (d[1] == coordinate[1] - 1 or d[1] == coordinate[1] + cheight) and \
                                 (coordinate[0] <= d[0] <= coordinate[0] + cwidth - 1), doors)
        print "to", doors
        if len(stations[-1]) > 0 and not doors:
            break
        if is_area(space, coordinate, cwidth, cheight) and (len(stations[-1]) == 0 or doors): # not blocked? good doors?
            stations[-1].append(dict(cindex=cindex, half_width=half_width, half_height=half_height, flavor=flavor, doors=doors, equipment=[])) # store the comp
            print 'coordinate:', coordinate, 'extremity:', (x+cwidth-1,y+cheight-1), 'width:', cwidth, 'height:', cheight ####
            for ln in range(cheight):       # then place component
                for pt in range(cwidth):
                    space[(x+pt,y+ln)] = '#'
            space = place_nscorridors(space, cindex, half_width, half_height, flavor, nsprob, ewprob)
            space = link_corridors(space, coordinate, cwidth, cheight, doors)
#           space = place_equipment(space, cindex, half_width, half_height, flavor)
            break
    return space


@check_return_not_none
def place_ewcomponent(space, cindex, flavor, doors, ewprob, nsprob):
    crashcount = 0
    while crashcount * (1+len(stations[-1])) < 100:
        half_width  = randint(mincompwidth, maxcompwidth - 6) / 2
        half_height = randint(mincompheight + 3, maxcompheight) / 2
        crashcount += 1
        if random() < bigcompfreq:
            half_width  *= comp_multiplier
            half_height *= comp_multiplier
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        y = cindex[1] - half_height
        if cindex[2] == 'e':
            x = cindex[0] - 2 * half_width
        elif cindex[2] == 'w':
            x = cindex[0]
        else:
            print "How can the orientation of an ewcomponent be", cindex[2]
        coordinate = (x, y)
        doors = filter(lambda d: (d[0] == coordinate[0] - 1 or d[0] == coordinate[0] + cwidth) and \
                                 (coordinate[1] <= d[1] <= coordinate[1] + cheight - 1) or \
                                 (d[1] == coordinate[1] - 1 or d[1] == coordinate[1] + cheight) and \
                                 (coordinate[0] <= d[0] <= coordinate[0] + cwidth - 1), doors)
        if len(stations[-1]) > 0 and not doors:
            break
        if is_area(space, coordinate, cwidth, cheight):
            stations[-1].append(dict(cindex=cindex, half_width=half_width, half_height=half_height, flavor=flavor, doors=doors, equipment=[])) # store the comp
            print 'coordinate:', coordinate, 'extremity:', (x+cwidth-1,y+cheight-1), 'width:', cwidth, 'height:', cheight ####
            for ln in range(cheight):           # if not blocked, place component
                for pt in range(cwidth):
                    space[(x+pt,y+ln)] = '#'
            space = place_ewcorridors(space, cindex, half_width, half_height, flavor, ewprob, nsprob)
            space = link_corridors(space, coordinate, cwidth, cheight, doors)
#           space = place_equipment(space, coordinate, cwidth, cheight, flavor)
            break
    return space


@check_return_not_none
def place_nscorridors(space, cindex, half_width, half_height, flavor, nsprob, ewprob):
    x = cindex[0] - half_width
    y = cindex[1]
    coordinate = (x, y)                               # top left coordinate of the component
    cwidth = 2 * half_width + 1
    cheight = 2 * half_height + 1
    doors = stations[-1][-1]['doors']
    ndoors = filter(lambda coord: coord[1]==y-1,doors)          # north doors (each is an (x,y) just outside the comp)
    sdoors = filter(lambda coord: coord[1]==y+cheight,doors)      # south doors
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
    if random() < nsprob:
        while maincorridors > 0:        # place any other main corridors at random
            spot = randint(0,cwidth-1)
            if cindex[2] == 's':       # do they start at the north?
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
            elif cindex[2] == 'n':                       # or south?
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
                print "How did an nscorridor's cindex[2] become", cindex[2]
    if newdoors:
        stations[-1][-1]['doors'] += newdoors
        place_nscomponent(space, (cindex[0], cindex[1]+cheight+1, cindex[2]), flavor, doors, nsprob*decay, ewprob)
    place_ewbranches(space, cindex, half_width, half_height, flavor, doors, deadends, nsprob, ewprob)
    return space


@check_return_not_none
def place_ewbranches(space, cindex, half_width, half_height, flavor, doors, deadends, nsprob, ewprob):
    x = cindex[0] - half_width
    y = cindex[1]
    coordinate = (x, y)
    cwidth = 2 * half_width + 1
    cheight = 2 * half_height + 1
    ndoors = filter(lambda coord: coord[1]==y-1,doors)              # north doors
    sdoors = filter(lambda coord: coord[1]==y+cheight,doors)        # south doors
    wdoors = filter(lambda coord: coord[0]==x-1,doors)              # west doors
    edoors = filter(lambda coord: coord[0]==x+cwidth,doors)         # east doors
    branches = max(1,randint(cheight/5, int(cheight/3.5)), len(edoors) + len(wdoors))     # how many e/w corridors left?
    eokay = wokay = False
    if len(edoors) > 0:
        eokay = True
    if len(wdoors) > 0:
        wokay = True
    if random() < ewprob:
        tricoin = random()
        if tricoin > 0.3:
            eokay = True
        if tricoin < 0.7:
            wokay = True
    for ed in edoors:
        m, n = ed
        m -= 1
        cl = randint(cwidth/3, cwidth*2/3)
        while m >= x+cwidth-cl and not is_character(space, (m,n), 'C'):
            if m == x+cwidth-cl and is_character(space, (m,n+1), '#') \
               and is_character(space, (m,n-1), '#') and is_character(space, (m-1,n), '#'):
                space[(m,n)] = 'c'
                deadends.append((m,n))
            else:
                space[(m,n)] = 'C'
            m -= 1
        branches -= 1
    for wd in wdoors:
        m, n = wd
        m += 1
        cl = randint(cwidth/3, cwidth*2/3)
        while m <= x+cl-1 and not is_character(space, (m,n), 'C'):
            if m == x+cl-1 and is_character(space, (m,n+1), '#') \
               and is_character(space, (m,n-1), '#') and is_character(space, (m+1,n), '#'):
                space[(m,n)] = 'c'
                deadends.append((m,n))
            else:
                space[(m,n)] = 'C'
            m += 1
        branches -= 1
    newdoors = []
    if wokay == True or eokay == True:
        crashcount = 0
        while branches > 0 and crashcount < 100:        # place any other branches at random
            crashcount += 1
            spot = randint(0,cheight-1)
            if eokay and randint(0,1) == 1:       # do those start at the east?
                if is_character(space, (x+cwidth-1,y+spot), '#') and not is_character(space, (x,y+spot+1), 'C') \
                   and not is_character(space, (x,y+spot-1), 'C') and not is_character(space, (x+cwidth-1,y+spot-1), 'C') \
                   and not is_character(space, (x+cwidth-1,y+spot+1), 'C'):
                    cl = randint(cwidth/3, cwidth*2/3)
                    m = x+cwidth-1
                    n = y+spot
                    newdoors.append((m+1,n))
                    while m >= x+cwidth-cl and not is_character(space, (m,n), 'C'):
                        if m == x+cwidth-cl and not (is_character(space, (m,n+1), 'C') or is_character(space, (m,n-1), 'C')):
                            space[(m,n)] = 'c'
                            deadends.append((m,n))
                        else:
                            space[(m,n)] = 'C'
                        m -= 1
                    branches -= 1
            elif wokay:                       # or west?
                if is_character(space, (x,y+spot), '#') and not is_character(space, (x,y+spot+1), 'C') \
                   and not is_character(space, (x,y+spot-1), 'C') and not is_character(space, (x+cwidth-1,y+spot-1), 'C') \
                   and not is_character(space, (x+cwidth-1,y+spot+1), 'C'):
                    cl = randint(cwidth/3, cwidth*2/3)
                    m = x
                    n = y+spot
                    newdoors.append((m-1,n))
                    while m <= x+cl-1 and not is_character(space, (m,n), 'C'):
                        if m == x+cl-1 and not (is_character(space, (m,n+1), 'C') or is_character(space, (m,n-1), 'C')):
                            space[(m,n)] = 'c'
                            deadends.append((m,n))
                        else:
                            space[(m,n)] = 'C'
                        m += 1
                    branches -= 1
        if crashcount == 100: print 'couldn\'t place any more e/w branches'  ####
    print 'deadends', deadends ####
    for end in deadends[:]:                            # now let's connect some dead-ends
        m,n = end
        if not is_character(space, end, 'c'):
            deadends.remove(end)
        else:
            go = ['n', 's', 'e', 'w']               # which directions will we look?
            if is_character(space, (m,n-1), 'C') or is_character(space, (m,n-1), 'c') or end in ndoors:
                go.remove('n')
            if is_character(space, (m,n+1), 'C') or is_character(space, (m,n+1), 'c') or end in sdoors:
                go.remove('s')
            if is_character(space, (m+1,n), 'C') or is_character(space, (m+1,n), 'c') or end in edoors:
                go.remove('e')
            if is_character(space, (m-1,n), 'C') or is_character(space, (m-1,n), 'c') or end in wdoors:
                go.remove('w')
            if len(go) < 3:
                space[end] = 'C'
                deadends.remove(end)
            else:
                while len(go) > 0 and end in deadends:
                    g = go[randint(0,len(go)-1)]
                    go.remove(g)
                    if g == 'n':
                        k = n
                        while k >= y:
                            k -= 1
                            if is_character(space, (m,k), 'C') or is_character(space, (m,k), 'c'):
                                deadends.remove(end)
                                while k <= n:
                                    space[(m,k)] = 'C'
                                    k += 1
                                break
                    elif g == 's':
                        k = n
                        while k <= y+cheight-1:
                            k += 1
                            if is_character(space, (m,k), 'C') or is_character(space, (m,k), 'c'):
                                deadends.remove(end)
                                while k >= n:
                                    space[(m,k)] = 'C'
                                    k -= 1
                                break
                    elif g == 'e':
                        h = m
                        while h <= x+cwidth-1:
                            h += 1
                            if is_character(space, (h,n), 'C') or is_character(space, (h,n), 'c'):
                                deadends.remove(end)
                                while h >= m:
                                    space[(h,n)] = 'C'
                                    h -= 1
                                break
                    else:
                        h = m
                        while h >= x:
                            h -= 1
                            if is_character(space, (h,n), 'C') or is_character(space, (h,n), 'c'):
                                deadends.remove(end)
                                while h <= m:
                                    space[(h,n)] = 'C'
                                    h += 1
                                break
                    if len(deadends) == 0:
                        break
#    for d in newdoors:
#        doors.append(d)
    if newdoors:
        doors += newdoors
#        place_ewcomponent(space, (coordinate[0]+cwidth+1, cindex[1]+half_height, 'e' or 'w' but filter newdoors to decide?), flavor, doors, nsprob*decay, ewprob)
    print 'doors:', doors ####
    for end in deadends:
        print 'deadends abandoned:', end ####
        space[end] = 'C'
    return space


grid = Grid(winwidth, winheight)      # okay, make a blank screen
#outer_space = generate_station(outer_space, (0,0,'n'), {})  # put station in space

stations.append(Station(outer_space, (0,0,'n'), {}))

grid.update(outer_space)              # put that space on the screen
grid.border()                         # make it look nice
print grid

# Do:  Write spawn_ewcorridors, spawn_nwbranches, spawn_equipment
# Update and introduce spawn_ewcomponent, or look for "game library python" with active development - not "pygame"