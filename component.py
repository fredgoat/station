# python Documents\GitHub\station\compo.py
''' So basically, you spawn a component, which spawns corridors,
which define equipment areas and spawn airlocks, which spawn more components.
Then you fill in the equipment, according to that component's flava.
'''

from random import random, randint

decay           = 0.7     # component branches die off by a power of this
gridwidth       = 25      # map dimensions
gridheight      = 25
mincompheight   = 4       # component dimensions
mincompwidth    = 4
maxcompheight   = 9
maxcompwidth    = 9
bigcompfreq     = 0.15    # how often are comps bigger than max & by what factor?
comp_multiplier = 2

components = []

blank_map_rows = '\n'.join(' '*gridwidth for x in xrange(gridheight)).split('\n')

def place_character(grid,coordinate,character):
    x, y = coordinate
    grid[y] = grid[y][:x] + character + grid[y][x+1:]
    return grid

def is_character(grid,coordinate,character=' '):
    x, y = coordinate
    if y < 0:                       # is this in the grid?
        return False
    if x < 0:
        return False
    if y >= len(grid):
        return False
    line = grid[y]
    if x >= len(line):
        return False
    if line[x] == character:        # is it the thing?
        return True
    else:
        return False

def place_nscomponent(grid, coordinate, flavor, doors):
    x, y = coordinate
    crashcount = 0
    while len(components) == 0 and crashcount < 100:    # try this until you get it, but don't die.
        cwidth  = randint(mincompwidth + 1, maxcompwidth)
        cheight = randint(mincompheight, maxcompheight - 2)
        crashcount = crashcount + 1
        if random() < bigcompfreq:          # maybe this is a super big component?
            cwidth  *= comp_multiplier
            cheight *= comp_multiplier
        else:
            for ln in range(cheight):       # is the area blocked?
                for pt in range(cwidth):
                    if not is_character(grid, (x+pt, y+ln)):
                        return grid
            for ln in range(cheight):       # if not, place component
                for pt in range(cwidth):
                    grid[y+ln] = grid[y+ln][:x+pt] + '#' + grid[y+ln][x+pt+1:]
            grid = place_nscorridors(grid, coordinate, cwidth, cheight, doors)
#            grid = place_equipment(grid, coordinate, cwidth, cheight, flavor)
            components.append(dict(coordinate=coordinate, flavor=flavor, doors=doors)) # store the comp
            return grid

def place_ewcomponent(grid, coordinate, flavor, doors):
    x, y = coordinate
    crashcount = 0
    while len(components) == 0 and crashcount < 100:
        cwidth  = randint(mincompwidth, maxcompwidth - 2)
        cheight = randint(mincompheight + 1, maxcompheight)
        crashcount = crashcount + 1
        if random() < bigcompfreq:
            cwidth  *= comp_multiplier
            cheight *= comp_multiplier
        else:
            for ln in range(cheight):       # is the area blocked?
                for pt in range(cwidth):
                    if not is_character(grid, (x+pt, y+ln)):
                        return grid
            for ln in range(cheight):           # if not, place component
                for pt in range(cwidth):
                    grid[y+ln] = grid[y+ln][:x+pt] + '#' + grid[y+ln][x+pt+1:]
            grid = place_ewcorridors(grid, coordinate, cwidth, cheight, doors)
#           grid = place_equipment(grid, coordinate, cwidth, cheight, flavor)
            components.append(dict(coordinate=coordinate, flavor=flavor, doors=doors)) # store the comp
            return grid

def place_nscorridors(grid, coordinate, cwidth, cheight, doors):
    x, y = coordinate
    crashcount = crashcount + 1
    if crashcount > 100:
        return grid
    else:
    ndoors = filter(lambda coord: coord[0]==y,doors)                # north doors
    sdoors = filter(lambda coord: coord[0]==y+cheight-1,doors)      # south doors
    maincorridors = max(randint(1, cwidth/3), len(ndoors), len(sdoors))     # how many n/s corridors left?
    for nd in ndoors:               # place corridors spawned by north doors
        m, n = nd
        if grid[m][n] == '#':
            cl = min(randint(cheight/3, cheight*2), cheight)
            for c in range(ndcl):
                place_character(grid, (m,n+c), 'C')
                maincorridors -= 1
            if cl != cheight:
                place_character(grid, (m,n+cl-1), 'c')            # dead-ends get lowercase c
    for sd in sdoors:               # place corridors spawned by south doors
        m, n = sd
        if grid[m][n] == '#':
            cl = min(randint(cheight/3, cheight*2), cheight)
            for c in range(cl):
                place_character(grid, (m,n-c), 'C')
                maincorridors -= 1
            if cl != cheight:
                place_character(grid, (m,n-cl+1), 'c')
    while maincorridors > 0:        # place any other main corridors at random
        spot = randint(0,cwidth)
        if randint(0,1) == 1:       # do they start at the north?
            if grid[y][x+spot] == '#':
                cl = min(randint(cheight/3, cheight*2), cheight)
                for c in range(cl):
                    place_character(grid, (x+spot,y+c), 'C')
                    maincorridors -= 1
                if cl != cheight:
                    place_character(grid, (x+spot,y+cl-1), 'c')
        else:                       # or south?
            if grid[y+cheight-1][x+spot] == '#':
                cl = min(randint(cheight/3, cheight*2), cheight)
                for c in range(cl):
                    place_character(grid, (x+spot,y+cheight-c), 'C')
                    maincorridors -= 1
                if cl != cheight:
                    place_character(grid, (x+spot,y+cheight-cl+1), 'c')
    return grid

grid = place_nscomponent(blank_map_rows, (gridwidth/2,gridheight/2), {}, [])

print '\n'.join(grid)
