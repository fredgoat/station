from random import random

decay = 0.7
width = 25
height = 25

starting_grid = '\n'.join(' '*width for x in xrange(height))

def place_character(grid,coordinate,character):
    x, y = coordinate
    lines = grid.split('\n')
    lines[y] = lines[y][:x] + character + lines[y][x+1:]
    return '\n'.join(lines)

def is_blank(grid,coordinate):
    x, y = coordinate
    if y < 0:
        return False
    if x < 0:
        return False
    lines = grid.split('\n')
    if y >= len(lines):
        return False
    line = lines[y]
    if x >= len(line):
        return False
    if line[x] == ' ':
        return True
    else:
        return False

def place_life(grid,coordinate):
    x, y = coordinate
    is_available = is_blank(grid,(x  ,y  )) and\
                   is_blank(grid,(x+1,y  )) and\
                   is_blank(grid,(x  ,y+1)) and\
                   is_blank(grid,(x+1,y+1))
    if not is_available:
        return grid
    grid = place_character(grid,(x  ,y  ),'L')
    grid = place_character(grid,(x+1,y  ),'L')
    grid = place_character(grid,(x  ,y+1),'L')
    grid = place_character(grid,(x+1,y+1),'L')
    return grid

def place_nswalkway(grid,coordinate,nsprob,ewprob):
    if not is_blank(grid,coordinate):
        return grid
    x, y = coordinate
    grid = place_character(grid,coordinate,'w')

    if random() < 0.9:
        grid = place_life(grid,(x,y+1))
    if random() < nsprob:
        grid = place_nswalkway(grid,(x,y+1),nsprob,ewprob)
    if random() < nsprob:
        grid = place_nswalkway(grid,(x,y-1),nsprob,ewprob)
    if random() < ewprob:
        grid = place_ewwalkway(grid,(x+1,y),ewprob*decay,nsprob*decay)
    if random() < ewprob:
        grid = place_ewwalkway(grid,(x-1,y),ewprob*decay,nsprob*decay)
    return grid

def place_ewwalkway(grid,coordinate,nsprob,ewprob):
    if not is_blank(grid,coordinate):
        return grid
    x, y = coordinate
    grid = place_character(grid,coordinate,'w')
    
    if random() < nsprob:
        grid = place_nswalkway(grid,(x,y+1),ewprob*decay,nsprob*decay)
    if random() < nsprob:
        grid = place_nswalkway(grid,(x,y-1),ewprob*decay,nsprob*decay)
    if random() < ewprob:
        grid = place_ewwalkway(grid,(x+1,y),nsprob,ewprob)
    if random() < ewprob:
        grid = place_ewwalkway(grid,(x-1,y),nsprob,ewprob)
    return grid

grid = place_nswalkway(starting_grid,(width/2,height/2),0.7,0.2)

print grid
