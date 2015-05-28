# python Documents\GitHub\station\compo.py
''' So basically, you spawn a component, which spawns corridors,
which define equipment areas and spawn airlocks, which spawn more components.
Then you fill in the equipment, according to that component's flava.
'''

from random import random, randint

decay           = 0.8     # component branches die off by a power of this
winwidth        = 30      # window dimensions
winheight       = 30
mincompheight   = 4       # component dimensions
mincompwidth    = 4
maxcompheight   = 15
maxcompwidth    = 15
bigcompfreq     = 0.15    # how often are comps bigger than max & by what factor?
comp_multiplier = 2

components = []
space = {}

#blank_map_rows = [' '*gridwidth for x in xrange(gridheight)]

window = {'tl':(0,0),'br':(winwidth,winheight)}

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
        '''Place character in the grid

        >>> place_character(['  ', '  '], (0, 1), 'x')
        ['  ', 'x ']
        '''
    def update(self, space, character=' '):            
        self.grid = [[character for x in xrange(winwidth)] for y in xrange(winheight)] # blank slate
        window = filter(lambda x: 0<=x[0]<winwidth and 0<=x[1]<winheight, space)
        for point in window:            # then get all the relevant points from space
            m, n = point
            self.grid[n][m] = space[(m,n)]
    def __repr__(self):                 # print it!
        joined = ''
        for y in self.grid:
            line = ''
            for x in y:
                line += x
            joined += line + '\n'
        return joined

def is_character(space, coordinate, character=' '):
    if not coordinate in space:
        if ' ' == character:
            return True
        else:
            return False
    elif space[coordinate] == character:        # is it the thing?
        return True
    else:
        return False

def flood(space, coordinate, target, replacement):
    x, y = coordinate
    Q = []
    if space[coordinate] != target:          # are we starting with the right character?
        return space
    Q.append(coordinate)
    for co in Q:
        w = co
        e = co
        while space[(w[0],w[1])] == target and w[0] > 0:
            w = (w[0]-1, w[1])
        while space[(e[0],e[1])] == target and e[0] < len(grid)-1:      # mark off a line
            e = (e[0]+1, e[1])
        for n in range(e[0]-w[0]+1):
            space[(w[0]+n,co[1])] = replacement                         # fill it in
            if co[1] > 0:
                if space[(w[0]+n,co[1]-1)] == target:
                    Q.append((w[0]+n, co[1]-1))
            if co[1] < len(grid)-1:
                if space[(w[0]+n,co[1]+1)] == target:
                    Q.append((w[0]+n,co[1]+1))
        return space

def place_nscomponent(space, coordinate, flavor, doors, nsprob, ewprob):
    x, y = coordinate
    crashcount = 0
    while len(components) == 0 and crashcount < 100:    # try this until you get it, but don't die.
        cwidth  = randint(mincompwidth + 1, maxcompwidth)
        cheight = randint(mincompheight, maxcompheight - 2)
        crashcount = crashcount + 1
        if random() < bigcompfreq:          # maybe this is a super big component?
            cwidth  *= comp_multiplier
            cheight *= comp_multiplier
        for ln in range(cheight):       # is the area blocked?
            for pt in range(cwidth):
                if not is_character(space, (x+pt, y+ln)):
                    return space
        for ln in range(cheight):       # if not, place component
            for pt in range(cwidth):
                space[(x+pt,y+ln)] = '#'
        space = place_nscorridors(space, coordinate, cwidth, cheight, doors, nsprob, ewprob)
#       space = place_equipment(space, coordinate, cwidth, cheight, flavor)
        components.append(dict(coordinate=coordinate, flavor=flavor, doors=doors)) # store the comp
    return space

def place_ewcomponent(space, coordinate, flavor, doors, ewprob, nsprob):
    x, y = coordinate
    crashcount = 0
    while len(components) == 0 and crashcount < 100:
        cwidth  = randint(mincompwidth, maxcompwidth - 2)
        cheight = randint(mincompheight + 1, maxcompheight)
        crashcount = crashcount + 1
        if random() < bigcompfreq:
            cwidth  *= comp_multiplier
            cheight *= comp_multiplier
        for ln in range(cheight):       # is the area blocked?
            for pt in range(cwidth):
                if not is_character(space, (x+pt, y+ln)):
                    return space
        for ln in range(cheight):           # if not, place component
            for pt in range(cwidth):
                space[(x+pt,y+ln)] = '#'
        space = place_ewcorridors(space, coordinate, cwidth, cheight, doors, ewprob, nsprob)
#       space = place_equipment(space, coordinate, cwidth, cheight, flavor)
        components.append(dict(coordinate=coordinate, flavor=flavor, doors=doors)) # store the comp
    return space

def place_nscorridors(space, coordinate, cwidth, cheight, doors, nsprob, ewprob):
    x, y = coordinate                               # top left coordinate of the component
    ndoors = filter(lambda coord: coord[0]==y,doors)                # north doors (each is an (x,y))
    sdoors = filter(lambda coord: coord[0]==y+cheight-1,doors)      # south doors
    maincorridors = max(1,randint(cwidth/5, int(cwidth/3.5)), len(ndoors) + len(sdoors))     # how many n/s corridors left?
    deadends = []
    newdoors = []
    for nd in ndoors:               # place corridors spawned by north doors
        m, n = nd
        if is_character(space, (m,n), '#'):
            cl = min(randint(cheight/3, cheight*2), cheight)
            for c in range(cl):
                space[(m,n+c)] = 'C'
            maincorridors -= 1
            if cl != cheight:
                space[(m,n+cl-1)] = 'c'            # dead-ends get lowercase c
                deadends.append((m,n+cl-1))
            else:
                newdoors.append((m,n+cl-1))
    for sd in sdoors:               # place corridors spawned by south doors
        m, n = sd
        if is_character(space, (m,n), '#'):
            cl = min(randint(cheight/3, cheight*2), cheight)
            for c in range(cl):
                space[(m,n-c)] = 'C'
            maincorridors -= 1
            if cl != cheight:
                space[(m,n-cl+1)] = 'c'
                deadends.append((m,n-cl+1))
            else:
                newdoors.append((m,n-cl+1))
    if random() < nsprob:
        while maincorridors > 0:        # place any other main corridors at random
            spot = randint(0,cwidth)
            if randint(0,1) == 1:       # do they start at the north?
                if is_character(space, (x+spot,y), '#') and not is_character(space, (x+spot+1,y), 'C') \
                   and not is_character(space, (x+spot-1,y), 'C') and not is_character(space, (x+spot-1,y+cheight-1), 'C') \
                   and not is_character(space, (x+spot+1,y+cheight-1), 'C'):
                    cl = min(randint(cheight/3, cheight*2), cheight)
                    for c in range(cl):
                        space[(x+spot,y+c)] = 'C'
                    maincorridors -= 1
                    newdoors.append((x+spot,y))
                    if cl != cheight:
                        space[(x+spot,y+cl-1)] = 'c'
                        deadends.append((x+spot,y+cl-1))
                    else:
                        newdoors.append((x+spot,y+cl-1))
            else:                       # or south?
                if is_character(space, (x+spot,y+cheight-1), '#') and not is_character(space, (x+spot+1,y), 'C') \
                   and not is_character(space, (x+spot-1,y), 'C') and not is_character(space, (x+spot-1,y+cheight-1), 'C') \
                   and not is_character(space, (x+spot+1,y+cheight-1), 'C'):
                    cl = min(randint(cheight/3, cheight*2), cheight)
                    for c in range(cl):
                        space[(x+spot,y+cheight-c-1)] = 'C'
                    maincorridors -= 1
                    newdoors.append((x+spot,y+cheight-1))
                    if cl != cheight:
                        space[(x+spot,y+cheight-cl)] = 'c'
                        deadends.append((x+spot,y+cheight-cl))
                    else:
                        newdoors.append((x+spot,y+cheight-cl))
    for d in newdoors:
        doors.append(d)
    place_ewbranches(space, coordinate, cwidth, cheight, doors, deadends, nsprob, ewprob)
    return space

def place_ewbranches(space, coordinate, cwidth, cheight, doors, deadends, nsprob, ewprob):
    x, y = coordinate
    ndoors = filter(lambda coord: coord[0]==y,doors)                # north doors
    sdoors = filter(lambda coord: coord[0]==y+cheight-1,doors)      # south doors
    wdoors = filter(lambda coord: coord[1]==x,doors)                # west doors
    edoors = filter(lambda coord: coord[1]==x+cwidth-1,doors)       # east doors
    maincorridors = max(1,randint(cheight/5, int(cheight/3.5)), len(edoors) + len(wdoors))     # how many e/w corridors left?
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
        cl = randint(cwidth/3, cwidth*2/3)
        while m >= x+cwidth-cl and not is_character(space, (m,n), 'C'):
            if m == x+cwidth-cl and is_character(space, (m,n+1), '#') \
               and is_character(space, (m,n-1), '#') and is_character(space, (m-1,n), '#'):
                space[(m,n)] = 'c'
                deadends.append((m,n))
            else:
                space[(m,n)] = 'C'
            m -= 1
        maincorridors -= 1
    for wd in wdoors:
        m, n = wd
        cl = randint(cwidth/3, cwidth*2/3)
        while m <= x+cl-1 and not is_character(space, (m,n), 'C'):
            if m == x+cl-1 and is_character(space, (m,n+1), '#') \
               and is_character(space, (m,n-1), '#') and is_character(space, (m+1,n), '#'):
                space[(m,n)] = 'c'
                deadends.append((m,n))
            else:
                space[(m,n)] = 'C'
            m += 1
        maincorridors -= 1
    if wokay == True or eokay == True:
        crashcount = 0
        while maincorridors > 0 and crashcount < 100:        # place any other main corridors at random
            crashcount += 1
            spot = randint(0,cheight)
            if eokay == True and randint(0,1) == 1:       # do those start at the east?
                if is_character(space, (x+cwidth-1,y+spot), '#') and not is_character(space, (x,y+spot+1), 'C') \
                   and not is_character(space, (x,y+spot-1), 'C') and not is_character(space, (x+cwidth-1,y+spot-1), 'C') \
                   and not is_character(space, (x+cwidth-1,y+spot+1), 'C'):
                    cl = randint(cwidth/3, cwidth*2/3)
                    m = x+cwidth-1
                    n = y+spot
                    while m >= x+cwidth-cl and not is_character(space, (m,n), 'C'):
                        if m == x+cwidth-cl and not (is_character(space, (m,n+1), 'C') or is_character(space, (m,n-1), 'C')):
                            space[(m,n)] = 'c'
                            deadends.append((m,n))
                        else:
                            space[(m,n)] = 'C'
                        m -= 1
                    maincorridors -= 1
            elif wokay == True:                       # or west?
                if is_character(space, (x,y+spot), '#') and not is_character(space, (x,y+spot+1), 'C') \
                   and not is_character(space, (x,y+spot-1), 'C') and not is_character(space, (x+cwidth-1,y+spot-1), 'C') \
                   and not is_character(space, (x+cwidth-1,y+spot+1), 'C'):
                    cl = randint(cwidth/3, cwidth*2/3)
                    m = x
                    n = y+spot
                    while m <= x+cl-1 and not is_character(space, (m,n), 'C'):
                        if m == x+cl-1 and not (is_character(space, (m,n+1), 'C') or is_character(space, (m,n-1), 'C')):
                            space[(m,n)] = 'c'
                            deadends.append((m,n))
                        else:
                            space[(m,n)] = 'C'
                        m += 1
                    maincorridors -= 1
    for end in deadends:                            # now let's connect some dead-ends
        m,n = end
        if not is_character(space, end, 'c'):
            deadends.remove(end)
        else:
            go = ['n', 's', 'e', 'w']               # which directions will we look?
            if is_character(space, (m,n-1), 'C') or is_character(space, (m,n-1), 'c'):
                go.remove('n')
            if is_character(space, (m,n+1), 'C') or is_character(space, (m,n+1), 'c'):
                go.remove('s')
            if is_character(space, (m+1,n), 'C') or is_character(space, (m+1,n), 'c'):
                go.remove('e')
            if is_character(space, (m-1,n), 'C') or is_character(space, (m-1,n), 'c'):
                go.remove('w')
            if len(go) < 3:
                space[end] = 'C'
                deadends.remove(end)
            else:
                for g in go:
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
                    if not end in deadends:
                        break
    return space

#import doctest
#doctest.testmod()

grid = Grid(winwidth, winheight)
space = place_nscomponent(space, (winwidth/2,winheight/2), {}, [], 1.0, 0.3)

grid.update(space)
print grid
