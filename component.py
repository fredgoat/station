# python Documents\GitHub\station\compo.py
''' So basically, you spawn a component, which spawns corridors,
which define equipment areas and spawn airlocks, which spawn more components.
Then you fill in the equipment, according to that component's flava.
'''

from random import random, randint

decay           = 0.8     # component branches die off by a power of this
winwidth        = 40      # window dimensions
winheight       = 40
mincompheight   = 4       # component dimensions
mincompwidth    = 4
maxcompheight   = 12
maxcompwidth    = 12
bigcompfreq     = 0.15    # how often are comps bigger than max & by what factor?
comp_multiplier = 2

components = []
space = {}
windex = (0,0)

#blank_map_rows = [' '*gridwidth for x in xrange(gridheight)]

class Grid(object):
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
        self.grid = [[character for x in xrange(winwidth)] for y in xrange(winheight)] # blank slate
        window = filter(lambda x: windex[0]<=x[0]<winwidth+windex[0] and windex[1]<=x[1]<winheight+windex[1], space.keys())
        for point in window:            # then get all the relevant points from space
            m, n = point
            self.grid[n][m] = space[(m-windex[0],n-windex[1])]
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

def flood(space, coordinate, target, replacement):
    x, y = coordinate
    Q = []
    if not is_character(space, coordinate, target):          # are we starting with the right character?
        return space
    Q.append(coordinate)
    for co in Q:
        w = co
        e = co
        while is_character(space, (w[0],w[1]), target):
            w = (w[0]-1, w[1])
        while is_character(space, (e[0],e[1]), target):      # mark off a line
            e = (e[0]+1, e[1])
        for n in range(e[0]-w[0]+1):
            space[(w[0]+n,co[1])] = replacement                         # fill it in
#            if co[1] > 0:
            if is_character(space, (w[0]+n,co[1]-1), target):
                Q.append((w[0]+n, co[1]-1))                         # add any "targets" to the list if they're north of the filled point
#            if co[1] < len(grid)-1:
            if is_character(space, (w[0]+n,co[1]+1), target):
                Q.append((w[0]+n,co[1]+1))                          # ...or south
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
    others = doors
    others.remove(d)
    flood(space, (m,n), 'C', 'Z')                         # flood the first door's corridors with Zs
    for o in others:
        h, k = entry(space, coordinate, cwidth, cheight, o)
        if is_character(space, (h,k), 'C'):
            linked = False                  # are there any Cs left?  Then something's unattached.
    flood(space, (m,n), 'Z', 'C')
    return linked

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
    print 'flood entry:', (m, n) ####
    if corridors_linked(space, coordinate, cwidth, cheight, doors): # are they already linked?
        print 'linked before attempt', attempt ####
        return space
    else:                                                       # Or are they unlinked?  Let's fix that
        flood(space, (m,n), 'C', 'Z')                           # flood the first door's corridors with Zs
        print 'flood entry confirmation:', space[(m,n)]
        unattached = filter(lambda door: is_character(space, entry(space, coordinate, cwidth, cheight, door), 'C'), doors)
        attached = filter(lambda door: is_character(space, entry(space, coordinate, cwidth, cheight, door), 'Z'), doors)  ##### somehow there are no attached!  Did flooding work?
        print 'on attempt', attempt, 'the attached doors were', attached, 'and the unattached doors were', unattached
        un = entry(space, coordinate, cwidth, cheight, unattached[randint(0,len(unattached)-1)])
        at = entry(space, coordinate, cwidth, cheight, attached[randint(0,len(attached)-1)])
        print 'un:', un, 'at:', at ####
        print 'x:', x, 'x+cwidth/4:', x+cwidth/4, 'x+cwidth*3/4:', x+cwidth*3/4, 'x+cwidth-1:', x+cwidth-1 ####
        print 'y:', y, 'y+cheight/4:', y+cheight/4, 'y+cheight*3/4:', y+cheight*3/4, 'y+cheight-1:', y+cheight-1 ####
        xunish = min(max(randint(x,x+cwidth/4), un[0]), randint(x+cwidth*3/4,x+cwidth-1))
        xatish = min(max(randint(x,x+cwidth/4), at[0]), randint(x+cwidth*3/4,x+cwidth-1))
        yunish = min(max(randint(y,y+cheight/4), un[1]), randint(y+cheight*3/4,y+cheight-1))
        yatish = min(max(randint(y,y+cheight/4), at[1]), randint(y+cheight*3/4,y+cheight-1))
        point = (randint(min(xunish,xatish), max(xunish,xatish)), randint(min(yunish, yatish), max(yunish, yatish))
        point = (un[0] + (point[0]-un[0])/attempt, at[1] + (point[1]-at[1])/attempt) # the more attempts, the closer to x = C entry, y = Z entry
        p, q = point
        go = ['n','s','e','w']
        ways = {'n':'?', 's':'?', 'e':'?', 'w':'?'}
        for g in go:
            go.remove(g)
            if g == 'n':                                # can we find a 'Z' and a 'C' from our point?  Try going North
                while q > y and not is_character(space, (p,q), 'Z') and not is_character(space, (p,q), 'C'):
                    q -= 1
                if space[(p,q)] == 'Z':
                    ways[g] = 'Z'
                elif space[(p,q)] == 'C':
                    ways[g] = 'C'
                elif q == y:
                    ways[g] = 'W'
            elif g == 's':                              # or South
                while q < y+cheight-1 and not is_character(space, (p,q), 'Z') and not is_character(space, (p,q), 'C'):
                    q += 1
                if space[(p,q)] == 'Z':
                    ways[g] = 'Z'
                elif space[(p,q)] == 'C':
                    ways[g] = 'C'
                elif q == y+cheight-1:
                    ways[g] = 'W'
            elif g == 'e':                              # or East
                while p < x+cwidth-1 and not is_character(space, (p,q), 'Z') and not is_character(space, (p,q), 'C'):
                    p += 1
                if space[(p,q)] == 'Z':
                    ways[g] = 'Z'
                elif space[(p,q)] == 'C':
                    ways[g] = 'C'
                elif q == x+cwidth-1:
                    ways[g] = 'W'
            elif g == 'w':                              # or West
                while q < x and not is_character(space, (p,q), 'Z') and not is_character(space, (p,q), 'C'):
                    q -= 1
                if space[(p,q)] == 'Z':
                    ways[g] = 'Z'
                elif space[(p,q)] == 'C':
                    ways[g] = 'C'
                elif q == x:
                    ways[g] = 'W'
        cways = filter(lambda dir: ways[dir]=='C', ways.keys())
        zways = filter(lambda dir: ways[dir]=='Z', ways.keys())
        if len(cways) != 0 and len(zways) != 0:                 # it worked?  So easy!  Let's connect them.
            linkways = cways[randint(0,len(cways)-1)] + zways[randint(0,len(zways)-1)]
            for way in linkways:
                linkways.remove(way)
                r = p
                s = q
                if way == 'n':                           # go the way to the C or Z, and then connect "point" to the C or Z
                    while not is_character(space, (r,s), 'C') and not is_character(space, (r,s), 'Z'):
                        s -= 1
                    for k in range(q-s):
                        space[(p,q-k)] = 'Z'
                elif way == 's':
                    while not is_character(space, (r,s), 'C') and not is_character(space, (r,s), 'Z'):
                        s += 1
                    for k in range(s-q):
                        space[(p,q+k)] = 'Z'
                elif way == 'e':
                    while not is_character(space, (r,s), 'C') and not is_character(space, (r,s), 'Z'):
                        r += 1
                    for k in range(r-p):
                        space[(p+k,q)] = 'Z'
                else:
                    while not is_character(space, (r,s), 'C') and not is_character(space, (r,s), 'Z'):
                        r -= 1
                    for k in range(p-r):
                        space[(p-k,q)] = 'Z'
            flood(space, (m,n), 'Z', 'C')
            if corridors_linked(space, coordinate, cwidth, cheight, doors):
                print 'linked on first try of attempt', attempt ####
                return space
            else:               # that didn't work?!?
                print "link_corridors must have found a way to connect, but couldn't.  Whyever not?"
        elif zways != 0:
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
        elif cways != 0:
            for cw in cways:    # or maybe we can only see Cs?  Go past them and maybe we'll connect to Zs???
                r = p
                s = q
                if cw == 'n':
                    while not is_character(space, (r,s), 'C') and not s == y:
                        s -= 1
                    if is_character(space, (r,s), 'C'):
                        s += 1
                        while not is_character(space, (r,s), 'Z'):
                            space[(r,s)] = 'C'
                            s += 1
                elif cw == 's':
                    while not is_character(space, (r,s), 'C') and not s == y+cheight-1:
                        s += 1
                    if is_character(space, (r,s), 'C'):
                        s -= 1
                        while not is_character(space, (r,s), 'Z'):
                            space[(r,s)] = 'C'
                            s -= 1
                elif cw == 'e':
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
            if corridors_linked(space, coordinate, cwidth, cheight, doors):     # did THAT work?
                print 'linked after overshooting a C on attempt', attempt ####
                return space
        else:                       # fine!  Let's try closer to "un" and "at".
            flood(space, (m,n), 'Z', 'C')
            link_corridors(space, coordinate, cwidth, cheight, doors, attempt+1)
            return space

def place_nscomponent(space, coordinate, flavor, doors, nsprob, ewprob):
    x, y = coordinate
    crashcount = 0
    while len(components) == 0 and crashcount < 100:    # try this until you get it, but don't die.
        cwidth  = randint(mincompwidth + 3, maxcompwidth)
        cheight = randint(mincompheight, maxcompheight - 6)
        crashcount = crashcount + 1
        if random() < bigcompfreq:          # maybe this is a super big component?
            cwidth  *= comp_multiplier
            cheight *= comp_multiplier
        if is_area(space, coordinate, cwidth, cheight): # blocked?
            print 'coordinate:', coordinate, 'extremity:', (x+cwidth-1,y+cheight-1), 'width:', cwidth, 'height:', cheight ####
            for ln in range(cheight):       # if not, place component
                for pt in range(cwidth):
                    space[(x+pt,y+ln)] = '#'
            space = place_nscorridors(space, coordinate, cwidth, cheight, doors, nsprob, ewprob)
            space = link_corridors(space, coordinate, cwidth, cheight, doors)
#           space = place_equipment(space, coordinate, cwidth, cheight, flavor)
            components.append(dict(coordinate=coordinate, cwidth=cwidth, cheight=cheight, flavor=flavor, doors=doors)) # store the comp
    return space

def place_ewcomponent(space, coordinate, flavor, doors, ewprob, nsprob):
    x, y = coordinate
    crashcount = 0
    while len(components) == 0 and crashcount < 100:
        cwidth  = randint(mincompwidth, maxcompwidth - 6)
        cheight = randint(mincompheight + 3, maxcompheight)
        crashcount = crashcount + 1
        if random() < bigcompfreq:
            cwidth  *= comp_multiplier
            cheight *= comp_multiplier
        if is_area(space, coordinate, cwidth, cheight): # blocked?
            for ln in range(cheight):           # if not, place component
                for pt in range(cwidth):
                    space[(x+pt,y+ln)] = '#'
            space = place_ewcorridors(space, coordinate, cwidth, cheight, doors, ewprob, nsprob)
#           space = place_equipment(space, coordinate, cwidth, cheight, flavor)
            components.append(dict(coordinate=coordinate, cwidth=cwidth, cheight=cheight, flavor=flavor, doors=doors)) # store the comp
    return space

def place_nscorridors(space, coordinate, cwidth, cheight, doors, nsprob, ewprob):
    x, y = coordinate                               # top left coordinate of the component
    ndoors = filter(lambda coord: coord[0]==y-1,doors)          # north doors (each is an (x,y) just outside the comp)
    sdoors = filter(lambda coord: coord[0]==y+cheight,doors)      # south doors
    maincorridors = max(1,randint(cwidth/5, int(cwidth/3.5)), len(ndoors) + len(sdoors))     # how many n/s corridors left?
    deadends = []
    newdoors = []
    for nd in ndoors:               # place corridors spawned by north doors
        m, n = nd
        if is_character(space, (m,n+1), '#'):
            cl = min(randint(cheight/3, cheight*2), cheight)
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
            cl = min(randint(cheight/3, cheight*2), cheight)
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
            if randint(0,1) == 1:       # do they start at the north?
                if is_character(space, (x+spot,y), '#') and not is_character(space, (x+spot+1,y), 'C') \
                   and not is_character(space, (x+spot-1,y), 'C') and not is_character(space, (x+spot-1,y+cheight-1), 'C') \
                   and not is_character(space, (x+spot+1,y+cheight-1), 'C'):
                    cl = min(randint(cheight/3, cheight*2), cheight)
                    for c in range(cl):
                        space[(x+spot,y+c)] = 'C'
                    maincorridors -= 1
                    newdoors.append((x+spot,y-1))
                    if cl != cheight:
                        space[(x+spot,y+cl-1)] = 'c'
                        deadends.append((x+spot,y+cl-1))
                        print deadends, 'north deadend' ####
                    else:
                        newdoors.append((x+spot,y+cl))
            else:                       # or south?
                if is_character(space, (x+spot,y+cheight-1), '#') and not is_character(space, (x+spot+1,y), 'C') \
                   and not is_character(space, (x+spot-1,y), 'C') and not is_character(space, (x+spot-1,y+cheight-1), 'C') \
                   and not is_character(space, (x+spot+1,y+cheight-1), 'C'):
                    cl = min(randint(cheight/3, cheight*2), cheight)
                    for c in range(cl):
                        space[(x+spot,y+cheight-c-1)] = 'C'
                    maincorridors -= 1
                    newdoors.append((x+spot,y+cheight))
                    if cl != cheight:
                        space[(x+spot,y+cheight-cl)] = 'c'
                        deadends.append((x+spot,y+cheight-cl))
                        print deadends, 'south deadend' ####
                    else:
                        newdoors.append((x+spot,y+cheight-cl-1))
    for d in newdoors:
        doors.append(d)
    place_ewbranches(space, coordinate, cwidth, cheight, doors, deadends, nsprob, ewprob)
    return space

def place_ewbranches(space, coordinate, cwidth, cheight, doors, deadends, nsprob, ewprob):
    x, y = coordinate
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
            if eokay == True and randint(0,1) == 1:       # do those start at the east?
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
                            print deadends, 'east deadend' ####
                        else:
                            space[(m,n)] = 'C'
                        m -= 1
                    branches -= 1
            elif wokay == True:                       # or west?
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
                            print deadends, 'west deadend' ####
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
                print 'deadend connection options:', go ####
                while len(go) > 0 and end in deadends:
                    g = go[randint(0,len(go)-1)]
                    go.remove(g)
                    print g ####
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
                        print 'deadends fixed!' ####
                        break
    for d in newdoors:
        doors.append(d)
    print 'doors:', doors ####
    for end in deadends:
        print 'deadends abandoned:', end ####
        space[end] = 'C'
    return space

'''
>>> place_character(['  ', '  '], (0, 1), 'x')
['  ', 'x ']
'''
#import doctest
#doctest.testmod()

grid = Grid(winwidth, winheight)
space = place_nscomponent(space, (winwidth/2,winheight/2), {}, [], 1.0, 0.3)

grid.update(space)
grid.border()
print grid
