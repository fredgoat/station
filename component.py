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
    def update(self, space, character=' '):            
        self.grid = [[character for x in xrange(winwidth)] for y in xrange(winheight)] # blank slate
        window = filter(lambda x: 0<=x[0]<winwidth and 0<=x[1]<winheight, space)
        for point in window:            # then get all the relevant points from space
            m, n = point
            self.grid[n][m] = space[(m,n)]
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
    if not coordinate in space:
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
                    Q.append((w[0]+n, co[1]-1))                         # add any "targets" to the list if they're north of the filled point
            if co[1] < len(grid)-1:
                if space[(w[0]+n,co[1]+1)] == target:
                    Q.append((w[0]+n,co[1]+1))                          # ...or south
        return space

def link_corridors(space, coordinate, cwidth, cheight, doors):      # this function attempts to link all the corridors in a component
    x, y = coordinate
    ndoors = filter(lambda coord: coord[1]==y-1,doors)              # north doors
    sdoors = filter(lambda coord: coord[1]==y+cheight,doors)        # south doors
    wdoors = filter(lambda coord: coord[0]==x-1,doors)              # west doors
    edoors = filter(lambda coord: coord[0]==x+cwidth,doors)         # east doors
    linked = True
    d = doors[0]
    m, n = doors[0]
    others = doors
    others.remove(d)
    if d in ndoors:                         # wherever the first door is, start flooding the corridor connected to it with Zs
        flood(space, (m,n+1), 'C', 'Z')
    elif d in sdoors:
        flood(space, (m,n-1), 'C', 'Z')
    elif d in edoors:
        flood(space, (m-1,n), 'C', 'Z')
    else:
        flood(space, (m+1,n), 'C', 'Z')
    for o in others:
        h, k = o
        if o in ndoors and is_character(space, (h,k+1), 'C')\
           or o in sdoors and is_character(space, (h,k-1), 'C')\
           or o in edoors and is_character(space, (h-1,k), 'C')\
           or o in wdoors and is_character(space, (h+1,k), 'C'):
            linked = False                  # are there any Cs left?  Then something's unattached.
        else:
            return space
    unattached = filter(lambda door: is_character(space, (door[0],door[1]+1, 'C'), ndoors))\
                 + filter(lambda door: is_character(space, (door[0],door[1]-1, 'C'), sdoors))\
                 + filter(lambda door: is_character(space, (door[0]-1,door[1], 'C'), edoors))\
                 + filter(lambda door: is_character(space, (door[0]+1,door[1], 'C'), wdoors))
    attached = filter(lambda door: is_character(space, (door[0],door[1]+1, 'Z'), ndoors))\
                 + filter(lambda door: is_character(space, (door[0],door[1]-1, 'Z'), sdoors))\
                 + filter(lambda door: is_character(space, (door[0]-1,door[1], 'Z'), edoors))\
                 + filter(lambda door: is_character(space, (door[0]+1,door[1], 'Z'), wdoors))
    un = unattached[randint(0,len(unattached)-1)]
    at = attached[randint(0,len(attached)-1)]
    point = (randint(min(max(randint(x+cwidth/4,x+cwidth/3),un[0]),randint(x+cwidth*3/4,x+cwidth*2/3)),\
                     min(max(randint(x+cwidth/4,x+cwidth/3),at[0]),randint(x+cwidth*3/4,x+cwidth*2/3))),\
             randint(min(max(randint(y+cheight/4,y+cheight/3),un[1]),randint(y+cheight*3/4,y+cheight*2/3)),\
                     min(max(randint(y+cheight/4,y+cheight/3),at[1]),randint(y+cheight*3/4,y+cheight*2/3))))
    p, q = point
    c = False
    z = False
    go = ['n','s','e','w']
    g = go[randint(0,len(go)-1)]
    ways = {'north':'?', 'south':'?', 'east':'?', 'west':'?'}
    if g == 'n':                                # can we find a 'Z' and a 'C' from our point?  Try going North
        go.remove('n')
        while q > y and space[(p,q)] != 'Z' and space[(p,q)] != 'C':
            q -= 1
        if space[(p,q)] == 'Z':
            z = True
            ways['north'] = 'Z'
        elif space[(p,q)] == 'C':
            c = True
            ways['north'] = 'C'
        elif q == y:
            ways['north'] = 'W'
    elif g == 's':                              # or South
        go.remove('s')
        while q < y+cheight-1 and space[(p,q)] != 'Z' and space[(p,q)] != 'C':
            q += 1
        if space[(p,q)] == 'Z':
            z = True
            ways['south'] = 'Z'
        elif space[(p,q)] == 'C':
            c = True
            ways['south'] = 'C'
        elif q == y+cheight-1:
            ways['south'] = 'W'
    elif g == 'e':                              # or East
        go.remove('e')
        while p < x+cwidth-1 and space[(p,q)] != 'Z' and space[(p,q)] != 'C':
            p += 1
        if space[(p,q)] == 'Z':
            z = True
            ways['east'] = 'Z'
        elif space[(p,q)] == 'C':
            c = True
            ways['east'] = 'C'
        elif q == x+cwidth-1:
            ways['east'] = 'W'
    elif g == 'w':                              # or West
        go.remove('w')
        while q < x and space[(p,q)] != 'Z' and space[(p,q)] != 'C':
            q -= 1
        if space[(p,q)] == 'Z':
            z = True
            ways['west'] = 'Z'
        elif space[(p,q)] == 'C':
            c = True
            ways['west'] = 'C'
        elif q == x:
            ways['west'] = 'W'
    if c == True and z == True:
        cways = filter(lambda dir: ways[dir]=='C', ways.keys())
        zways = filter(lambda dir: ways[dir]=='Z', ways.keys())
        
    # now I just tell it to link the different corridor systems somehow
'''
Go a direction
until you see Zs or Cs or a wall.  If you see Zs, go the other way.
If you see more Zs, keep going.  If you see a C, connect it to the last Z.
If not, go past the other Z till you see a C and connect THAT.
If none of that works, do it again, closer to the doors.  If nothing works,
'''
    

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
            print 'width', cwidth ####
            for ln in range(cheight):       # if not, place component
                for pt in range(cwidth):
                    space[(x+pt,y+ln)] = '#'
            space = place_nscorridors(space, coordinate, cwidth, cheight, doors, nsprob, ewprob)
            space = link_corridors(space, coordinate, cwidth, cheight, doors)
#           space = place_equipment(space, coordinate, cwidth, cheight, flavor)
            components.append(dict(coordinate=coordinate, flavor=flavor, doors=doors)) # store the comp
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
            components.append(dict(coordinate=coordinate, flavor=flavor, doors=doors)) # store the comp
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
            print 'ns', spot ####
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
                        print deadends, 'north' ####
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
                        print deadends, 'south' ####
                    else:
                        newdoors.append((x+spot,y+cheight-cl-1))
    for d in newdoors:
        doors.append(d)
    print 'doors', doors ####
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
            print 'ew', spot ####
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
                            print deadends, 'east' ####
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
                            print deadends, 'west' ####
                        else:
                            space[(m,n)] = 'C'
                        m += 1
                    branches -= 1
    print deadends ####
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
                print go ####
                while len(go) > 0 and end in deadends:
                    g = go[randint(0,len(go)-1)]
                    if g == 'n':
                        go.remove('n')
                        k = n
                        while k >= y:
                            k -= 1
                            if is_character(space, (m,k), 'C') or is_character(space, (m,k), 'c'):
                                deadends.remove(end)
                                while k <= n:
                                    space[(m,k)] = 'C'
                                    k += 1
                                break
                        print g ####
                    elif g == 's':
                        go.remove('s')
                        k = n
                        while k <= y+cheight-1:
                            k += 1
                            if is_character(space, (m,k), 'C') or is_character(space, (m,k), 'c'):
                                deadends.remove(end)
                                while k >= n:
                                    space[(m,k)] = 'C'
                                    k -= 1
                                break
                        print g ####
                    elif g == 'e':
                        go.remove('e')
                        h = m
                        while h <= x+cwidth-1:
                            h += 1
                            if is_character(space, (h,n), 'C') or is_character(space, (h,n), 'c'):
                                deadends.remove(end)
                                while h >= m:
                                    space[(h,n)] = 'C'
                                    h -= 1
                                break
                        print g ####
                    else:
                        go.remove('w')
                        h = m
                        while h >= x:
                            h -= 1
                            if is_character(space, (h,n), 'C') or is_character(space, (h,n), 'c'):
                                deadends.remove(end)
                                while h <= m:
                                    space[(h,n)] = 'C'
                                    h += 1
                                break
                        print g ####
                    if len(deadends) == 0:
                        break
    for d in newdoors:
        doors.append(d)
    for end in deadends:
        print end ####
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
