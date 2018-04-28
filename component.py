""" The game loop looks for mouse and keyboard inputs.  Scrolling zooms and clicking moves the player or gives info.

Everything gets blitted onto tiles or a station image which in turn get blitted onto the game window.

To form a station, you spawn a component, which spawns corridors,
which define equipment areas and spawn airlocks, which spawn more components.
Then you fill in the equipment, according to that component's flava.

Each station is an object with a list of components
each component is an object with a radix, dimensions, airlock objects (a door is an airlock's coords), flavor, and equipment
equipment is an object with an index, dimensions, type, flavor, and inventory (a dict)
radix is a tuple, dimensions are two numbers, airlocks are objects but doors is a list of tuples,
flavor is a dict of numbers for each flavor, i.e. {'med': 5, 'sci': 2}

Index = upper left point.  Extremity = lower right.  Coordinate = that point.  Radix = spawn root point.
"""

# __repr__(self) overrides what happens when you print a thing
# time.time() tells you what time it is (seconds since 1970)
# @ decorates a function with another function, so the first one runs inside the second

import pdb          # pdb.set_trace() stops everything and lets you do pdb commands
import traceback    # traceback.print_stack() just prints the stack at that point
import doctest      # doctest.testmod() returns None if all fake Python sessions in comments in this module return what they say, like so
import math

'''
>>> function(*args)
returnvalue
'''

from random import random, randint, seed

super_seed = randint(1,1000)
# super_seed = 410
print "This seed is", super_seed
seed(super_seed)    # this will let you go back to good randomnesses

winLocX = 8
winLocY = 30
import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (winLocX, winLocY)
import pygame
pygame.init()

branchPersistence = 0.8     # corridor branches persist (or die) by a power of this
compFreq         = 0.4     # probability that a component will in fact spawn
minCompHeight   = 4       # component dimensions
minCompWidth    = 4
maxCompHeight   = 12
maxCompWidth    = 12
bigCompFreq     = 0.15    # how often are comps bigger than max & by what factor?
compMultiplier = 2

noFlavor = {'power':0, 'cargo':0, 'quarters':0, 'life support':0, 'medical':0, 'hydroponics':0, \
                 'command':0, 'reclamation':0, 'manufacture':0}
defaultFlavor = {'power':500, 'cargo':0, 'quarters':-500, 'life support':500, 'medical':-300, 'hydroponics':-100, \
                 'command':-700, 'reclamation':-500, 'manufacture':-700}
equipmentFlavors = {'power':{}, 'cargo':{}, 'quarters':{}, 'life support':{}, 'medical':{}, 'hydroponics':{}, \
                 'command':{}, 'reclamation':{}, 'manufacture':{}}        # this is each flavor's equipment value per tile, and a pointer to that equipment
equipmentLoot = {'converter': [('nothing', 1, (0,0))], \
                 'battery': [('nothing', 1, (0,0))], \
                 'thermoregulator': [('nothing', 1, (0,0))], \
                 'recycler':[('nothing', 1, (0,0))], \
                 'suppressor':[('nothing', 0.3, (0,0)), ('electrolytes', 0.7, (1,3))], \
                 'pressurizer':[('nothing', 1, (0,0))], \
                 'dehumidifier':[('nothing', 0.25, (0,0)), ('water', 0.75, (1,3))], \
                 'infirmary':[('nothing', 0.1, (0,0)), ('food', 0.5, (1,3)), ('water', 0.7, (1,4)), ('medicine', 0.95, (1,5)), ('electrolytes', 0.6, (1,2))], \
                 'medstation':[('nothing', 0.5, (0,0)), ('food', 0.1, (1,3)), ('water', 0.6, (1,4)), ('medicine', 0.8, (1,9))], \
                 'farm':[('nothing', 0.6, (0,0)), ('food', 0.75, (1,7)), ('water', 0.2, (1,3)), ('medicine', 0.1, (1,3))], \
                 'box':[('nothing', 0.8, (0,0)), ('food', 0.2, (1,10)), ('medicine', 0.05, (1,4))], \
                 'purifier':[('nothing', 0.1, (0,0)), ('water', 0.95, (3,10))], \
                 'extruder':[('nothing', 0.1, (0,0)), ('metal', 0.6, (1,4)), ('wire', 0.8, (1,10))], \
                 'fabricator':[('nothing', 0.1, (0,0)), ('metal', 0.2, (1,2)), ('wire', 0.8, (1,6)), \
                               ('plastic', 0.4, (1,3)), ('silica', 0.4, (1,3)), ('electrolytes', 0.3, (1,3)), \
                               ('hydrogen', 0.2, (1,3)), ('diodes', 0.5, (1,4)), ('photocells', 0.2, (1,3)), \
                               ('transistors', 0.4, (1,4)), ('leds', 0.3, (1,4)), ('screens', 0.1, (1,2)), \
                               ('capacitors', 0.4, (1,4)), ('resistors', 0.5, (1,4)), ('oscillators', 0.1, (1,2)), \
                               ('batteries', 0.3, (1,3)), ('antennas', 0.1, (1,2)), ('transformers', 0.2, (1,3)), \
                               ('inductors', 0.2, (1,3))], \
                 'assembler':[('nothing', 0.1, (0,0)), ('wire', 0.8, (1,6)), ('plastic', 0.1, (1,2)), ('silica', 0.5, (1,6)), \
                               ('diodes', 0.5, (1,6)), ('photocells', 0.2, (1,4)), ('transistors', 0.4, (1,6)), \
                               ('leds', 0.3, (1,6)), ('screens', 0.1, (1,3)), ('capacitors', 0.4, (1,6)), \
                               ('resistors', 0.5, (1,6)), ('oscillators', 0.1, (1,3)), ('batteries', 0.3, (1,4)), \
                               ('antennas', 0.1, (1,3)), ('transformers', 0.2, (1,4)), ('inductors', 0.2, (1,4))], \
                 'furnace':[('nothing', 0.3, (0,0)), ('metal', 0.2, (1,3)), ('silica', 0.1, (1,3)), ('scrap', 0.4, (1,5))], \
                 'mold':[('nothing', 0.4, (0,0)), ('trash', 0.4, (1,5)), ('plastic', 0.2, (1,3))], \
                 'electrolyzer':[('nothing', 0.1, (0,0)), ('water', 0.9, (5,10)), ('hydrogen', 0.7, (5,15))], \
                 'hold':[('nothing', 0.1, (0,0)), ('metal', 0.2, (1,2)), ('wire', 0.2, (1,2)), \
                               ('plastic', 0.2, (1,2)), ('silica', 0.1, (1,4)), ('electrolytes', 0.1, (1,2)), \
                               ('hydrogen', 0.1, (1,2)), ('diodes', 0.1, (1,2)), ('photocells', 0.1, (1,2)), \
                               ('transistors', 0.1, (1,2)), ('leds', 0.1, (1,2)), ('screens', 0.05, (1,2)), \
                               ('capacitors', 0.1, (1,2)), ('resistors', 0.1, (1,2)), ('oscillators', 0.1, (1,2)), \
                               ('batteries', 0.2, (1,2)), ('antennas', 0.1, (1,2)), ('transformers', 0.1, (1,2)), \
                               ('inductors', 0.1, (1,2)), ('scrap', 0.1, (1,10)), ('trash', 0.1, (4,10)), \
                               ('food', 0.3, (1,8)), ('water', 0.1, (1,10)), ('medicine', 0.1, (1,2))], \
                 'locker':[('nothing', 0.1, (0,0)), ('leds', 0.05, (1,4)), ('screens', 0.05, (1,2)), \
                               ('batteries', 0.2, (1,2)), ('antennas', 0.1, (1,2)), ('trash', 0.5, (4,10)), \
                               ('food', 0.5, (1,15)), ('water', 0.5, (1,20)), ('medicine', 0.2, (1,5))], \
                 'trashed':[('nothing', 0.1, (0,0)), ('wire', 0.4, (1,2)), ('silica', 0.3, (1,2)), \
                               ('diodes', 0.1, (1,2)), ('photocells', 0.1, (1,2)), \
                               ('transistors', 0.1, (1,2)), ('leds', 0.1, (1,2)), ('screens', 0.05, (1,2)), \
                               ('capacitors', 0.1, (1,2)), ('resistors', 0.1, (1,2)), ('oscillators', 0.1, (1,2)), \
                               ('batteries', 0.1, (1,2)), ('antennas', 0.05, (1,2)), ('transformers', 0.1, (1,2)), \
                               ('inductors', 0.1, (1,2)), ('scrap', 0.8, (1,8)), ('trash', 0.6, (1,5))], \
                 'cabin':[('nothing', 0.1, (0,0)), ('screens', 0.1, (1,3)), ('batteries', 0.2, (1,3)), ('trash', 0.1, (1,2)), \
                               ('food', 0.6, (1,8)), ('water', 0.6, (1,6)), ('medicine', 0.4, (1,6))], \
                 'dormitory':[('nothing', 0.1, (0,0)), ('screens', 0.05, (1,2)), ('batteries', 0.1, (1,2)), ('trash', 0.1, (1,2)), \
                               ('food', 0.3, (1,4)), ('water', 0.5, (1,3)), ('medicine', 0.1, (1,2))], \
                 'refectory':[('nothing', 0.1, (0,0)), ('trash', 0.1, (1,2)), \
                               ('food', 0.6, (1,8)), ('water', 0.6, (1,6)), ('medicine', 0.05, (1,2))], \
                 'sensors':[('nothing', 1, (0,0))], \
                 'comms':[('nothing', 1, (0,0))], \
                 'bridge':[('nothing', 0.1, (0,0)), ('screens', 0.05, (1,3)), ('batteries', 0.1, (1,3)), ('trash', 0.1, (1,3)), \
                               ('food', 0.2, (1,2)), ('water', 0.4, (1,3)), ('medicine', 0.1, (1,2))]}
                                        # lists of (name, weight, (min, max)) for loot(stuff) - min & max CAN be floats
equipmentPower = {'converter':30, 'battery':0, 'thermoregulator':-3, 'recycler':-5, 'suppressor':0, 'pressurizer':-3, \
                  'dehumidifier':-1, 'infirmary':-5, 'medstation':0, 'farm':-2, 'box':0, 'purifier':-6, \
                  'extruder':-14, 'fabricator':-8, 'assembler':-6, 'furnace':-16, 'mold':-10, 'electrolyzer':-20, \
                  'hold':0, 'locker':0, 'trashed':0, 'cabin':-2, 'dormitory':-1, 'refectory':-1, 'sensors':-2, \
                  'comms':-3, 'bridge':-5}

stations = []
outerSpace = {}
cardinals = ['n', 'e', 's', 'w']

displayInfo = pygame.display.Info()
winZoom         = 10      # how many pixels per tile
maxZoom         = 50
minZoom         = 3
winWidth        = int(displayInfo.current_w/winZoom)-1      # window dimensions measured in tiles
winHeight       = int(displayInfo.current_h/winZoom)-7
wIndex = (float(winWidth) / -2, float(winHeight) / -2)        # this is the upper left corner of a screen centered on (0,0)

clock = pygame.time.Clock()
clock.tick(240)
mouse = {'pos':(0,0), 1:0, 2:0, 3:0, 4:0, 5:0, 6:0} # {position, button 1, button 2, etc}
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])


gameDisplay = pygame.display.set_mode((winWidth * winZoom, winHeight * winZoom))      # the actual window will start at ten pixels per tile
pygame.display.set_caption('Space Station')
backgroundColor = (0, 0, 0)
background = pygame.image.load('images/background.bmp').convert()
blankTile = pygame.image.load('images/blank tile.png')
defaultTile = pygame.image.load('images/default tile.bmp').convert()           # these are now Surfaces, and converted to a nice /pixel/ format
corridorTile = pygame.image.load('images/corridor tile.bmp').convert()         # later if I have sprites I can set_colorkey((255,255,255)) to make the white parts transparent
airlockTile = pygame.image.load('images/airlock tile.bmp').convert()
defaultPattern = pygame.Surface((winWidth * winZoom, winHeight * winZoom))


def patterner(background, tile, size):
    """This draws a repeating background pattern out of tile images"""
    x = int(winWidth * winZoom / size[0] + 1)               # how many big ol' tiles fit side to side
    y = int(winHeight * winZoom / size[1] + 1)              # how many fit up and down
    for row in range(y):
        for spot in range(x):
            background.blit(tile, (spot * size[0], row * size[1]))      # blit that many in a pattern
    return background

class Tile(object):
    """A part of the background of the station"""

    def __init__(self, name, image, size, flavors):
        self.name = name
        self.tile = pygame.image.load('images/'+image).convert()
        self.pattern = patterner(defaultPattern.copy(), pygame.transform.scale(self.tile, size), size)
        self.flavors = flavors
        for flavor in flavors.keys():                                       # look at your flavors, and in equipmentFlavor
            equipmentFlavors[flavor][name] = (self, flavors[flavor])        # add a tuple of (a pointer back to yourself, and your flavor strength)


converter = Tile('converter', 'converter tile.bmp', (30,30), {'power':3})               # c = power/voltage converters
battery = Tile('battery', 'battery tile.bmp', (30,30), {'power':3})                     # b = NiH2 battery
thermoregulator = Tile('thermoregulator', 'thermoregulator tile.bmp', (30,30), {'life support':5})  # t
recycler = Tile('recycler', 'recycler tile.bmp', (30,30), {'life support':1})           # o = atmospheric/oxygen recycler
pressurizer = Tile('pressurizer', 'pressurizer tile.bmp', (30,30), {'life support':2})    # p = pressure control
suppressor = Tile('suppressor', 'suppressor tile.bmp', (30,30), {'life support':20})      # s = fire suppression system
dehumidifier = Tile('dehumidifier', 'dehumidifier tile.bmp', (10,10), {'life support':60}) # d
infirmary = Tile('infirmary', 'infirmary tile.bmp', (30,30), {'medical':10})         # i
medstation = Tile('medstation', 'medstation tile.bmp', (10,10), {'medical':40})    # +
farm = Tile('farm', 'farm tile.bmp', (30,30), {'hydroponics':5})               # a = algae farm
box = Tile('box', 'box tile.bmp', (10,10), {'hydroponics':30})                # g = grow box
purifier = Tile('purifier', 'purifier tile.bmp', (30,30), {'hydroponics':2})       # w = water purifier
extruder = Tile('extruder', 'extruder tile.bmp', (30,30), {'manufacture':5})       # x = wire extruder
fabricator = Tile('fabricator', 'fabricator tile.bmp', (30,30), {'manufacture':2})   # * = component fabricator
assembler = Tile('assembler', 'assembler tile.bmp', (30,30), {'manufacture':1})     # & = circuit assembler
furnace = Tile('furnace', 'furnace tile.bmp', (30,30), {'reclamation':1})         # f = metal/silica furnace
mold = Tile('mold', 'mold tile.bmp', (30,30), {'reclamation':1})               # m = plastic mold
electrolyzer = Tile('electrolyzer', 'electrolyzer tile.bmp', (30,30), {'reclamation':2})    # e
hold = Tile('hold', 'hold tile.bmp', (30,30), {'cargo':20})                             # h
locker = Tile('locker', 'locker tile.bmp', (30,30), {'cargo':40})                      # l
trashed = Tile('trashed', 'trashed tile.bmp', (30,30), {'cargo':1})                     # ~
cabin = Tile('cabin', 'cabin tile.bmp', (30,30), {'quarters':20})               # $ = boss's cabin
dormitory = Tile('dormitory', 'dormitory tile.bmp', (30,30), {'quarters':5})    # q
refectory = Tile('refectory', 'refectory tile.bmp', (30,30), {'quarters':15})   # r
sensors = Tile('sensors', 'sensors tile.bmp', (30,30), {'command':20})          # @
comms = Tile('comms', 'comms tile.bmp', (30,30), {'command':5})                 # %
bridge = Tile('bridge', 'bridge tile.bmp', (30,30), {'command':30})            # !


drawnTiles = {'#': defaultTile, 'C': corridorTile}


playerImage = pygame.image.load('images/player image.png')
playerWalk1 = pygame.image.load('images/player walk1.png')
playerWalk2 = pygame.image.load('images/player walk2.png')
playerAction = pygame.image.load('images/player action.png')


class Sprite(object):
    """Things that are in space and have an image that isn't part of the background"""
    def __init__(self, space, coords, images):
        self.space = space
        self.coords = coords
        self.image = images[0]


class Person(Sprite):
    """A Sprite that represents either the player or an NPC on a station"""
    def face(self):
        """Determines the facing of a Person based on the next element in their path"""
        if self.path:
            dest = self.path[0]
            if self.coords[0] == dest[0]:
                if self.coords[1] == dest[1]+1:
                    self.facing = 'n'
                elif self.coords[1] == dest[1]-1:
                    self.facing = 's'
            elif self.coords[1] == dest[1]:
                if self.coords[0] == dest[0]+1:
                    self.facing = 'w'
                elif self.coords[0] == dest[0]-1:
                    self.facing = 'e'

    def __init__(self, space, station, coords, images, inventory):
        Sprite.__init__(self, space, coords, images)
        self.station = station
        self.station.population.append(self)
        self.coords = coords
        self.inventory = inventory
        self.upgrades = []
        self.walk_1 = images[1]
        self.walk_2 = images[2]
        self.action = images[3]
        self.mode = 0
        self.wardrobe = [self.image, self.walk_1, self.walk_2, self.action]
        self.facing = 'n'
        self.path = []          # where are you going to go, first?
        self.face()
        self.plan = []          # what are you going to interact with as you move, in order?


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


def game_loop(mouse, grid, index, zoom, player, space):
    """This is the main loop from which the game runs"""
    timer = 0
    clickpos = (0,0)
    while True:

        timer = timer%20+1
        if player.path:
            if timer == 1 and player.mode == 3:
                player.mode = 0
                player.coords = player.path.pop(0)
                if player.plan and not player.path:
                    if isinstance(player.plan[0], Equipment):
                        player.facing = filter(lambda direc: what_equipment(go(player.coords, direc)) == player.plan[0], cardinals)[0]
                        player.plan = []
                    player.plan = []
                grid.update(index, zoom, space)
            if timer in [6,11,16] and timer == player.mode * 5 + 6:
                player.mode = (timer-1)/5
                player.face()
                grid.update(index, zoom, space)
        else:
            player.mode = 0
            grid.update(index, zoom, space)

        x, y = pygame.mouse.get_rel()    # if nothing else, mark this moment to measure mouse movement from (dump relative movement up to this point)
        for event in pygame.event.get():  # go as long as player doesn't hit the upper right x
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            elif pygame.mouse.get_focused() or pygame.key.get_focused():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse[event.button] = 1
                    mouse['pos'] = event.pos
                    clickpos = event.pos
                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse[event.button] = 0
                    mouse['pos'] = event.pos
                    h, k = mouse['pos']
                    coords = (int(round(float(h) / zoom + index[0] - 0.5)), int(round(float(k) / zoom + index[1] - 0.5)))
                    if event.button == 1 and abs(clickpos[0] - h) < 10 and abs(clickpos[1] - k) < 10:           # if the user clicks on the screen
                        if what_equipment(coords) == 'corridor':
                            print "corridor"
                            player.path = path(player.coords, coords, 'corridor', space)
                            player.mode = 0
                            player.plan = []
                        elif isinstance(what_equipment(coords), Airlock):
                            print "airlock"
                            doorpath = filter(lambda x: x and what_equipment((x[-1][0],x[-1][1])) == 'corridor', \
                                                 [path(player.coords, go(coords,'n'), 'corridor', space), \
                                                  path(player.coords, go(coords,'s'), 'corridor', space), \
                                                  path(player.coords, go(coords,'e'), 'corridor', space), \
                                                  path(player.coords, go(coords,'w'), 'corridor', space)])
                            if doorpath:
                                player.path = doorpath.pop()
                                player.mode = 0
                            player.plan = []
                        elif what_equipment(coords) == 'space':
                            print "space"
                        elif what_equipment(coords) == 'component':
                            print "component"
                            player.plan = []
                        elif isinstance(what_equipment(coords), Equipment):
                            equip = what_equipment(coords)
                            print_thing(what_equipment(coords).type, what_equipment(coords).inv)
                            player.path = path(player.coords, equip.access_points(), 'corridor', space)
                            player.mode = 0
                            player.plan.append(equip)
                            if not player.path:
                                player.facing = filter(lambda direc: what_equipment(go(player.coords, direc)) == player.plan[0], cardinals)[0]
                elif event.type == pygame.MOUSEMOTION:
                    mouse['pos'] = event.pos

                if mouse[1]:
                    index = (index[0] - min(max(float(x) / zoom, -10), 10), index[1] - min(max(float(y) / zoom, -10), 10))
                    grid.update(index, zoom, space)
                elif mouse[4] and zoom > minZoom:
                    index = (index[0]+winWidth*5/zoom, index[1]+winHeight*5/zoom)       # move the index toward the center
                    zoom -= zoom/7 + (zoom % 7 > 0)                                     # zoom out (zoom % 5 > 0 gives True or False.  True adds as 1)
                    index = (index[0]-winWidth*5/zoom, index[1]-winHeight*5/zoom)       # move the index back, net positive x and y change
                    grid.update(index, zoom, space)
                elif mouse[5] and zoom < maxZoom:
                    index = (index[0]+winWidth*5/zoom, index[1]+winHeight*5/zoom)
                    zoom = min(maxZoom, zoom + zoom/7 + (zoom % 7 > 0))
                    index = (index[0]-winWidth*5/zoom, index[1]-winHeight*5/zoom)
                    grid.update(index, zoom, space)

                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_w) or (event.key == pygame.K_q) and \
                        (pygame.KMOD_RCTRL & pygame.key.get_mods() or pygame.KMOD_LCTRL & pygame.key.get_mods()):   # if ctrl-q or ctrl-w
                        pygame.quit()
                        quit()


        pygame.display.update()  # redraw everything
        clock.tick(80)  # frames per second


class Grid(object):
    """The Grid is basically the screen or UI"""
    def __init__(self):
        pass

    def update(self, index, zoom, space):
        """This wipes the screen, then fills in anything from that part of outerSpace"""
        intdex = (int(round(index[0])), int(round(index[1])))
        gameDisplay.blit(background, (0, 0))
        window = filter(lambda coords: intdex[0]-2 <= coords[0] < (winWidth+20)*zoom + intdex[0] and intdex[1]-2 <= coords[1] < (winHeight+10)*zoom + intdex[1], space.keys())
        for point in window:            # then get all the relevant points from space
            m, n = point
            gameDisplay.blit(pygame.transform.scale(drawnTiles[space[m,n]],(zoom, zoom)), (round((m - index[0]) * zoom), round((n - index[1]) * zoom)))
        nearby = filter(lambda x: x.space == space and intdex[0]-500 < x.stradix[0] < intdex[0]+(winWidth+1000)*zoom \
                        and intdex[1]-500 < x.stradix[1] < intdex[1]+(winHeight+1000)*zoom, stations)
        for station in nearby:
            gameDisplay.blit(pygame.transform.scale(station.image, (station.width*zoom, station.height*zoom)), \
                             (round((station.index[0] - index[0]) * zoom), round((station.index[1] - index[1]) * zoom)))
        playeronex = playerOne.coords[0] - index[0] + (playerOne.mode%4)/4.0 if playerOne.facing == 'e' \
            else playerOne.coords[0] - index[0] - (playerOne.mode%4)/4.0 if playerOne.facing == 'w' \
            else playerOne.coords[0] - index[0]
        playeroney = playerOne.coords[1] - index[1] + (playerOne.mode%4)/4.0 if playerOne.facing == 's' \
            else playerOne.coords[1] - index[1] - (playerOne.mode%4)/4.0 if playerOne.facing == 'n' \
            else playerOne.coords[1] - index[1]
        playeroner = 90 if playerOne.facing == 'e' else 180 if playerOne.facing == 'n' else 270 if playerOne.facing == 'w' else 0
        gameDisplay.blit(pygame.transform.rotate(pygame.transform.scale(playerOne.wardrobe[playerOne.mode if playerOne.mode < 2 \
            else 0 if playerOne.mode==2 else playerOne.mode-1], (zoom, zoom)), playeroner), \
                         (playeronex * zoom, playeroney * zoom))


def print_thing(name, dict):
    """Prints the items in an inventory dict that don't equal zero"""
    no_zeros = {}
    for thing in dict:
        if dict[thing] == 0:
            continue
        else:
            no_zeros[thing] = dict[thing]
    print name, "contains",
    if no_zeros:
        for thing in no_zeros:
            print no_zeros[thing], thing,
        print
    else:
        print "nothing"


def loot(stuff):
    """Like pick, loot takes a list of tuples (name, weight, (min, max)) but returns a DICT of name: quantity pairs"""
    r = random()
    swag = {}
    for i in stuff:
        if r < i[1] and not i[0] == 'nothing':
            swag[i[0]] = int((random()**2*(i[2][1]-i[2][0]+1)) + i[2][0])
    return swag                 # alternately, for a bell curve rather than a quadratic, use int((1+max-min)(0.5((2*random()-1)**3+1))+min)


def pick(stuff):
    """Like loot, pick takes a list of tuples (name, weight, (min, max)) but returns ONE tuple of (name, quantity)"""
    total = 0
    for i in stuff:
        total += i[1]
    r = random()*total
    for i in stuff:
        if r < i[1]:
            return (i[0], int((random()**2*(i[2][1]-i[2][0]+1)) + i[2][0]))
            break
        else:
            r -= i[1]


def go(coords, direction):
    """Goes from coords one step in direction within a grid"""
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


def path(start, ends, pathtype, space=outerSpace):
    """Tries to find a path of the chosen character (pathtype) from start to end within a grid"""
    if isinstance(ends, tuple):
        end = [ends]
    elif isinstance(ends, list):
        end = ends
    spots = []
    for e in end:
        spots.append((e[0], e[1], 0))
    # spots = [(end[0], end[1], 0)]
    tries = 0
    solution = []
    for spot in spots:
        tries += 1
        if tries > 500:
            return False
        adjacent = filter(lambda adj: what_equipment((adj[0],adj[1]))==pathtype, \
                          [(spot[0], spot[1]+1, spot[2]+1), (spot[0]+1, spot[1], spot[2]+1), \
                           (spot[0], spot[1]-1, spot[2]+1), (spot[0]-1, spot[1], spot[2]+1)])   # filter adj spots for the pathtype
        if spot[0] == start[0] and spot[1] == start[1]:     # if we find the start, build a low-value solution back to end
            solution.append(spot)
            for sol in solution:
                if filter(lambda e: e[0] == sol[0] and e[1] == sol[1], end):
                    solution.pop(0)
                    print solution
                    return solution
                else:    # look through the elements of solution for the end, adding lowest-value adj spots back to end
                    solution.append(sorted(filter(lambda sp: sp[0] == sol[0] and sp[1] in [sol[1]+1,sol[1]-1] \
                                    or sp[1] == sol[1] and sp[0] in [sol[0]+1,sol[0]-1], spots), key=lambda spot: spot[2])[0])
        for adj in adjacent:        # if we haven't found the start yet, expand the search, ignoring higher value repeats
            repeat = False
            for spot in spots:
                if spot[0] == adj[0] and spot[1] == adj[1] and spot[2] < adj[2]:
                    repeat = True
                    break
            if what_equipment((adj[0],adj[1])) == pathtype and not repeat:
                spots.append(adj)
    return False


def replace(space, index, extremity, target, replacement):
    """Replaces the target character with the replacement within a designated rectangle of the grid"""
    x = index[0]
    y = index[1]
    width = abs(extremity[0] - x) + 1
    height = abs(extremity[1] - y) + 1
    for n in range(height):
        for m in range(width):
            if is_character(space, (x+m, y+n), target):
                space[(x+m, y+n)] = replacement
    return space


def is_character(space, coords, character=' '):
    """Checks if this element of the grid is blank (or the chosen character)"""
    if not coords in space.keys():
        if ' ' == character:
            return True
        else:
            return False
    elif space[coords] == character:        # is it the thing?
        return True
    else:
        return False


def is_area(space, index, width, height, character=' '):
    """Like is_any, but checks if the area is COMPLETELY blank (or COVERED by the chosen character)"""
    x, y = index
    for ln in range(height):                    # is the area blocked at all?
        for pt in range(width):
            if not is_character(space, (x+pt, y+ln), character):
                return False
    return True


def is_any(space, index, width, height, character):
    """Like is_area, but this checks if there are ANY of this thing in the area"""
    x = index[0]
    y = index[1]
    for ln in range(height):
        for pt in range(width):
            if is_character(space, (x+pt, y+ln), character):
                return True
    return False


def what_equipment(coords, stationlist=stations, space=outerSpace):
    """Returns 'airlock', 'corridor', 'space', or a pointer to the equipment at the coords (or 'component' in weird cases)"""
    nearby = filter(lambda x: x.space == space and coords[0]-500 < x.stradix[0] < coords[0]+(winWidth+1000)*maxZoom \
                        and coords[1]-500 < x.stradix[1] < coords[1]+(winHeight+1000)*maxZoom, stationlist)
    for station in nearby:
        for airlock in station.airlocks:
            if coords == airlock.coords:
                return airlock
        if is_character(station.space, coords, 'C'):
            return 'corridor'
        for comp in station.components:
            if comp.index[0] <= coords[0] < comp.index[0] + comp.width and \
                    comp.index[1] <= coords[1] < comp.index[1] + comp.height:
                for equip in comp.equipment:
                    if equip.eindex[0] <= coords[0] < equip.eindex[0] + equip.width and \
                            equip.eindex[1] <= coords[1] < equip.eindex[1] + equip.height:
                        return equip
        if is_character(station.space, coords, '#'):
            return 'component'
    else:
        return 'space'


def block_off(space, index, half_width, half_height):
    """Turn an irregular area of undesignated component into blocks for equipment"""
    width = 2 * half_width + 1
    height = 2 * half_height + 1
    blocks = []                     # these will be tuples of (index, width, height) in which equipment can be placed
    attempts = 0
    while attempts < 1000 and is_any(space, index, width, height, '#'):      # while there's any '#' left
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
    return blocks


def season(flavor):
    """This boosts all existing flavors, adds some, and subtracts relative to total"""
    seasonings = 0
    for spice in flavor.keys():
        flavor[spice] = int(448*math.atan(0.00224*flavor[spice]))  # trust me, this is great.  The big numbers get reduced good.
        if flavor[spice] < 0:
            flavor[spice] = (flavor[spice]*5) / 6             # extra boost to the negatives
        seasonings += max(0, flavor[spice])                 # add up all the seasonings
    for spice in flavor.keys():
        flavor[spice] += randint(0,15)**2
        flavor[spice] -= seasonings/27

    return flavor


def flavor_add(base, addition):
    """Adds equipment flavor to the base"""
    for spice in base.keys():
        base[spice] += addition[spice]
    return base


def flavor_subtract(base, subtraction):
    "Subtracts equipment flavor from the base"
    for spice in base.keys():
        base[spice] -= subtraction[spice]
    print "Subtracting used flavor of", subtraction
    return base


@check_return_not_none
def flood(space, coords, target, replacement):
    """Floods contiguous target characters with a replacement character"""
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


def entry(space, index, cwidth, cheight, airlock):
    """Gives the adjacent corridor coordinates of an airlock, given its component's size and index"""
    x, y = index
    m, n = airlock.coords
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


def corridors_linked(space, index, cwidth, cheight, airlocks):
    """Checks if the corridors in a component are linked, starting with the airlock entries"""
    x, y = index
    linked = True
    a = airlocks[0]
    m, n = entry(space, index, cwidth, cheight, a)
    others = list(airlocks)
    others.remove(a)
    flood(space, (m,n), 'C', 'Z')                         # flood the first airlock's corridors with Zs
    for o in others:
        h, k = entry(space, index, cwidth, cheight, o)
        if is_character(space, (h,k), 'C'):
            linked = False                  # are there any Cs left?  Then something's unattached.
    flood(space, (m,n), 'Z', 'C')
    return linked


@check_return_not_none
def link_corridors(space, index, cwidth, cheight, airlocks, attempt=1):
    """Recursively attempts to link the airlock entries in a component with corridors"""
    if attempt > 20 or len(airlocks) == 0:
        return space
    x, y = index
    ndoors = filter(lambda airlock: airlock.coords[1]==y-1,airlocks)              # north doors
    sdoors = filter(lambda airlock: airlock.coords[1]==y+cheight,airlocks)        # south doors
    wdoors = filter(lambda airlock: airlock.coords[0]==x-1,airlocks)              # west doors
    edoors = filter(lambda airlock: airlock.coords[0]==x+cwidth,airlocks)         # east doors
    linked = True
    a = airlocks[0]
    m, n = entry(space, index, cwidth, cheight, a)
    if corridors_linked(space, index, cwidth, cheight, airlocks): # are all airlocks already linked?  Note that this resets corridors to 'C'
        flood(space, (m,n), 'C', 'Z')
        if is_any(space, index, cwidth, cheight, 'C'):          # if there are any stranded corridors, eliminate them
            replace(space, index, (index[0]+cwidth-1,index[1]+cheight-1), 'C', '#')
        flood(space, (m,n), 'Z', 'C')
        return space
    else:                                                       # Are airlocks unlinked?  Let's fix that
        flood(space, (m,n), 'C', 'Z')                           # flood the first airlock's corridors with Zs
        unattached = filter(lambda airlock: is_character(space, entry(space, index, cwidth, cheight, airlock), 'C'), airlocks)
        attached = filter(lambda airlock: is_character(space, entry(space, index, cwidth, cheight, airlock), 'Z'), airlocks)
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
            if corridors_linked(space, index, cwidth, cheight, airlocks):
                if is_any(space, index, cwidth, cheight, 'C'):    # if there are any stranded corridors, eliminate them
                    replace(space, index, (index[0]+cwidth-1,index[1]+cheight-1), 'C', '#')
                flood(space, (m,n), 'Z', 'C')
                return space
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
            if corridors_linked(space, index, cwidth, cheight, airlocks):   # did it work?
                if is_any(space, index, cwidth, cheight, 'C'):          # if there are any stranded corridors, eliminate them
                    replace(space, index, (index[0]+cwidth-1,index[1]+cheight-1), 'C', '#')
                flood(space, (m,n), 'Z', 'C')
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
            if corridors_linked(space, index, cwidth, cheight, airlocks):     # did THAT work?
                if is_any(space, index, cwidth, cheight, 'C'):          # if there are any stranded corridors, eliminate them
                    replace(space, index, (index[0]+cwidth-1,index[1]+cheight-1), 'C', '#')
                flood(space, (m,n), 'Z', 'C')
                return space
        flood(space, (m,n), 'Z', 'C')  # fine!  Let's try closer to "un" and "at".
        link_corridors(space, index, cwidth, cheight, airlocks, attempt + 1)
        return space


class Station(object):
    """Stations spawn initial components and are the centers of the game"""
    def spawn_component(self, cradix, flavor, airlocks, nsprob, ewprob):
        """Try to create a component at the coords with the airlocks given"""
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
            if self.component_count > 0 and not airlocks:
                break
            realairlocks = filter(lambda a: (a.coords[0] == index[0] - 1 or a.coords[0] == index[0] + cwidth) and \
                                         (index[1] <= a.coords[1] <= index[1] + cheight - 1) or \
                                         (a.coords[1] == index[1] - 1 or a.coords[1] == index[1] + cheight) and \
                                         (index[0] <= a.coords[0] <= index[0] + cwidth - 1), airlocks)
            if not realairlocks and self.component_count > 0:
                fakeairlocks = []
                for a in airlocks:
                    if a not in realairlocks:
                        fakeairlocks.append(a)
            elif is_area(self.space, (index[0] - 1, index[1] - 1), cwidth + 2, cheight + 2) and not \
                    (self.component_count > 0 and not realairlocks) and not \
                    filter(lambda a: a.coords in [(index[0]-1,index[1]-1), (index[0]+cwidth,index[1]-1), \
                                                  (index[0]-1,index[1]+cheight), (index[0]+cwidth,index[1]+cheight)], \
                           self.airlocks): # not blocked?  any airlocks that actually connect? no diagonal airlocks?
                if random()**(self.component_count/10) > compFreq:
                    self.component_count += 1
                    print "Component", self.component_count, "forming on attempt", crashcount                             ####
                    airlocks = realairlocks
                    if cradix[2] == 'n' or cradix[2] == 's':
                        self.components.append(NSComponent(self.space, self, cradix, half_width, half_height, flavor, airlocks, nsprob, ewprob))
                    else:
                        self.components.append(WEComponent(self.space, self, cradix, half_width, half_height, flavor, airlocks, nsprob, ewprob))
                else:
                    print "Component", self.component_count+1, "decided not to form"
                break
        if crashcount * (1+self.component_count) >= 100:
            print "Gave up on spawning component", self.component_count+1, "after", crashcount, "tries"

    def update_equipment(self):
        """Update station parameters with any changes equipment or people make to temperature etc"""
        self.power_change, self.power_storage, self.oxygen_change, self.air_capacity, self.pressure_change, self.humidity_change, self.temperature_change = 0, 0, 0, 0, 0, 0, 0
        for component in self.components:
            self.air_capacity += component.width * component.height
            self.temperature_change -= component.width * component.height / 1000.0
            for equip in component.equipment:
                self.power_change += equip.power / 500.0
                self.temperature_change += abs(equip.power/5000.0)
                if equip.type == 'battery':
                    self.power_storage += equip.width * equip.height * 10
                if equip.type == 'recycler':
                    self.oxygen_change += equip.width * equip.height / 5.0
                if equip.type == 'dehumidifier':
                    self.humidity_change -= equip.width * equip.height / 20.0
                    self.temperature_change += equip.width * equip.height / 50
                if equip.type == 'pressurizer':
                    self.pressure_change += equip.width * equip.height / (self.air_capacity*5)
                if equip.type == 'thermoregulator':
                    self.temperature_change += equip.width * equip.height / 20.0 if self.temperature < 23 else equip.width * equip.height / -20.0
            for airlock in component.airlocks:
                if airlock not in self.airlocks:
                    self.airlocks.append(airlock)
        self.temperature_change += len(self.population)/10.0
        self.oxygen_change -= len(self.population)
        self.humidity_change += len(self.population) / 50.0

    def update_image(self):
        """Update the station's blit image"""
        for comp in self.components:
            for equip in comp.equipment:
                eindex = (round((equip.eindex[0] - self.index[0]) * winZoom), round((equip.eindex[1] - self.index[1]) * winZoom))
                self.image.blit(pygame.transform.scale(equipmentFlavors[equip.flavor][equip.type][0].pattern, \
                    (winWidth * winZoom, winHeight * winZoom)), eindex, (0, 0, equip.width * winZoom, equip.height * winZoom))
        for airlock in self.airlocks:
            coords = (round((airlock.coords[0] - self.index[0]) * winZoom), round((airlock.coords[1] - self.index[1]) * winZoom))
            self.image.blit(pygame.transform.scale(airlockTile, (winZoom, winZoom)), coords)

    def extent(self):
        """Give the cardinal extremes of a station in the order (w, n, e, s)"""
        west, north, east, south = 0,0,0,0
        for comp in self.components:
            west = min(west, comp.index[0])
            north = min(north, comp.index[1])
            east = max(east, comp.index[0]+comp.width-1)
            south = max(south, comp.index[1]+comp.height-1)
            for airlock in comp.airlocks:
                west = min(west, airlock.coords[0])
                north = min(north, airlock.coords[1])
                east = max(east, airlock.coords[0])
                south = max(south, airlock.coords[1])
        return (west, north, east, south)

    def enter(self):
        """Return the corridor side of an external airlock"""
        airlock = self.airlocks[int(random()*len(self.airlocks))]
        entries = []
        for airlock in self.airlocks:
            for d in xrange(4):
                if what_equipment(go(airlock.coords, cardinals[d]), [self], self.space) == 'corridor' and \
                        what_equipment(go(airlock.coords, cardinals[(d+2)%4])) != 'corridor':
                    entries.append(go(airlock.coords, cardinals[d]))
        if entries:
            return entries[int(random()*len(entries))]
        else:
            for airlock in self.airlocks:
                for d in xrange(4):
                    if what_equipment(go(airlock.coords, cardinals[d]), [self], self.space) == 'corridor':
                        entries.append(go(airlock.coords, cardinals[d]))
                if entries:
                    return entries[int(random()*len(entries))]

    def __init__(self, space, stradix, flavor):
        self.space = space
        self.stradix = stradix
        self.flavor = flavor
        self.components = []
        self.component_count = 0
        self.airlocks = []
        self.population = []
        self.power_change, self.power_storage, self.oxygen_change, self.air_capacity, self.pressure_change, self.humidity_change, self.temperature = 0, 0, 0, 0, 0, 0, 0
        self.spawn_component(self.stradix, self.flavor, [], (1-random()**2) * 0.75 + 0.2, (1-random()**2) * 0.75 + 0.2)     # ns and we probs are random between .2 and .95
        self.update_equipment()
        self.power = self.power_storage if self.power_change > 0 else 0
        self.humidity = 0.0 if self.humidity_change <= 0 else 0.8
        self.pressure = 1.0 if self.pressure_change > 0 else 0.3
        self.oxygen = self.air_capacity * self.pressure if self.oxygen_change > 0 else 0.2 * self.air_capacity * self.pressure
        self.temperature = 23.0 + self.temperature_change * 10
        self.width = self.extent()[2] - self.extent()[0] + 1
        self.height = self.extent()[3] - self.extent()[1] + 1
        self.index = (self.extent()[0], self.extent()[1])
        self.image = pygame.transform.scale(blankTile.copy(), (self.width * winZoom, self.height * winZoom))       # create a blank backdrop
        self.update_image()                                                                     # put stuff on it


class Component(object):
    """Components make up a station and spawn corridors, which spawn airlocks and block off equipment"""
    def place(self):
        """Places the equipment as a rectangle of pound signs in space"""
        x, y = self.index
        print 'index:', self.index, 'extremity:', (x + self.width - 1, y + self.height - 1), 'width:', self.width, 'height:', self.height ####
        for ln in range(self.height):       # then place component
            for pt in range(self.width):
                self.space[(x+pt,y+ln)] = '#'

    def connect_deadends(self, deadends):
        """Tries to link dead-end corridors that didn't get fixed in branches"""
        x, y = self.index
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        ndoors = filter(lambda airlock: airlock.coords[1]==y-1,self.airlocks)              # north doors
        sdoors = filter(lambda airlock: airlock.coords[1]==y+cheight,self.airlocks)        # south doors
        wdoors = filter(lambda airlock: airlock.coords[0]==x-1,self.airlocks)              # west doors
        edoors = filter(lambda airlock: airlock.coords[0]==x+cwidth,self.airlocks)         # east doors
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

    def prune_doors(self, newdoors):
        """Takes a list of potential door coords and weeds out conflicts"""
        for newd in newdoors:               # label newdoors with an a and make sure none of them are adjacent to other doors
            self.space[newd] = 'a'
            if filter(lambda d: newd[0]-1 <= d.coords[0] <= newd[0]+1 and newd[1]-1 <= d.coords[1] <= newd[1]+1, self.station.airlocks):
                del self.space[newd]
                newdoors.remove(newd)
            elif is_any(self.space, (newd[0]-1, newd[1]-1), 3, 1, 'a') or is_any(self.space, (newd[0]-1, newd[1]+1), 3, 1, 'a') \
                    or is_character(self.space, (newd[0]-1, newd[1]), 'a') or is_character(self.space, (newd[0]+1, newd[1]), 'a'):
                newdoors.remove(newd)
                del self.space[newd]
            else:       # if the airlock's corridor is diagonal opposite a component, this won't work
                if is_character(self.space, go(newd, 'n'), 'C') and \
                        (is_character(self.space, go(go(newd, 's'), 'e'), '#') or \
                         is_character(self.space, go(go(newd, 's'), 'w'), '#')) or \
                        is_character(self.space, go(newd, 's'), 'C') and \
                        (is_character(self.space, go(go(newd, 'n'), 'e'), '#') or \
                         is_character(self.space, go(go(newd, 'n'), 'w'), '#')) or \
                        is_character(self.space, go(newd, 'e'), 'C') and \
                        (is_character(self.space, go(go(newd, 'w'), 'n'), '#') or \
                         is_character(self.space, go(go(newd, 'w'), 's'), '#')) or \
                        is_character(self.space, go(newd, 'w'), 'C') and \
                        (is_character(self.space, go(go(newd, 'e'), 'n'), '#') or \
                         is_character(self.space, go(go(newd, 'e'), 's'), '#')):
                    newdoors.remove(newd)
                del self.space[newd]

    def place_equipment(self):
        """Picks equipment based on component flavor, keeping track of what's already there"""
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
                    seas -= max(0, self.flavor[flav])                   # pick a flavor from self.flavor, weighted jenga style
                    attempts += 1
                attempts = 0
                while attempts < 50:
                    attempts += 1
                    equip = equipmentFlavors[flav].keys()[randint(0,len(equipmentFlavors[flav].keys())-1)]      # pick 'generator' or something
                    burden = equipmentFlavors[flav][equip][1] * block[1] * block[2] * 5*minCompHeight*minCompWidth/(self.width*self.height)                              # how much flavor would that size generator have?
                    if self.flavor[flav]/20 - attempts*5 < burden < self.flavor[flav]/5 + attempts*20:                                      # is it a reasonable amount of flavor?
                        self.equipment.append(Equipment(self.space, self.station, self, block[0], block[1], block[2], equip, flav))
                        print "Placing", equip, "at", block[0]
                        for f in equipmentFlavors[flav][equip][0].flavors.keys():                           # go through all flavors for that equipment, [equip][0] is the Tile object
                            self.flavored[f] += equipmentFlavors[f][equip][1] * block[1] * block[2]         # add tile flavor * area to self.flavor/ed
                        break
                if attempts >= 50:
                    equip = equipmentFlavors[flav].keys()[randint(0,len(equipmentFlavors[flav].keys())-1)]      # whatever, fine, just place it
                    print "No equipment wants to go here, so let's just put this", equip
                    self.equipment.append(Equipment(self.space, self.station, self, block[0], block[1], block[2], equip, flav))
                    for f in equipmentFlavors[flav][equip][0].flavors.keys():
                        self.flavored[f] += equipmentFlavors[f][equip][1] * block[1] * block[2]

    def airlock_update(self):
        """Adds this component to all airlocks' component lists"""
        for airlock in self.airlocks:
            if self not in airlock.components:
                airlock.components.append(self)

    def __init__(self, space, station, cradix, half_width, half_height, flavor, airlocks, nsprob, ewprob):
        self.space = space
        self.cradix = cradix
        self.airlocks = airlocks
        self.airlock_update()
        self.nsprob = nsprob
        self.ewprob = ewprob
        self.station = station
        self.equipment = []                 # equipment is a list of objects with attributes eindex, width, height, type, flavor, and inv (a list of (name, quantity) tuples)
        self.half_width = half_width
        self.half_height = half_height
        self.width = 2 * half_width + 1
        self.height = 2 * half_height + 1
        self.flavor = season(flavor.copy())        # the flavor the component wants to have (mutate it from that provided by the spawn source)
        print "This component's flavors will be", self.flavor
        self.index = (cradix[0] - 2 * half_width if cradix[2] == 'e' else cradix[0] if cradix[2] == 'w' \
        else cradix[0] - half_width, cradix[1] if cradix[2] == 'n' else cradix[1] - 2 * half_height \
        if cradix[2] == 's' else cradix[1] - half_height)       # index are at the top left, cradix is at the center on the spawning side, cradix[2] is direction spawning happens /from/
        self.place()
        self.flavored = noFlavor            # the flavor from the equipment placed


class NSComponent(Component):
    """Components oriented north-south"""
    def spawn_webranches(self, deadends):
        """Spawns branches west and east from the main corridors' deadends"""
        x, y = self.index
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        nairlocks = filter(lambda airlock: airlock.coords[1]==y-1,self.airlocks)              # north airlocks
        sairlocks = filter(lambda airlock: airlock.coords[1]==y+cheight,self.airlocks)        # south airlocks
        wairlocks = filter(lambda airlock: airlock.coords[0]==x-1,self.airlocks)              # west airlocks
        eairlocks = filter(lambda airlock: airlock.coords[0]==x+cwidth,self.airlocks)         # east airlocks
        branches = max(1,randint(cheight/5, int(cheight/3.5)), len(eairlocks) + len(wairlocks))     # how many e/w corridors left?
        eokay = wokay = False
        if len(eairlocks) > 0:
            eokay = True
        if len(wairlocks) > 0:
            wokay = True
        if random() < self.ewprob:
            tricoin = random()
            if tricoin > 0.3:
                eokay = True
            if tricoin < 0.7:
                wokay = True
        for ea in eairlocks:
            m, n = ea.coords
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
        for wa in wairlocks:
            m, n = wa.coords
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
                       and not is_character(self.space, (x+cwidth-1,y+spot+1), 'C') and not is_character(self.space, (x+cwidth+1,y+spot), '#'):
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
                       and not is_character(self.space, (x+cwidth-1,y+spot+1), 'C') and not is_character(self.space, (x-2,y+spot), '#'):
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
        self.connect_deadends(deadends)                 # now let's connect some dead-ends
        self.prune_doors(newdoors)
        for door in newdoors:
            self.airlocks.append(Airlock(self.space, self.station, door, [self]))
        self.station.update_equipment()
        if newdoors:
            direc = ['w', 'e']
            if not filter(lambda airlock: airlock.coords[0]==x-1,self.airlocks):          # any west doors?
                direc.remove('e')
            if not filter(lambda airlock: airlock.coords[0]==x+cwidth,self.airlocks):     # or east doors?
                direc.remove('w')
            while direc:
                tion = direc.pop(randint(0,len(direc)-1))                    # pick a direction and spawn some components!
                spawnx = self.index[0] - 2 if tion == 'e' else self.index[0] + cwidth + 1
                self.station.spawn_component((spawnx, self.index[1] + self.half_height, tion), \
                                             self.flavor, self.airlocks, \
                                             self.nsprob, branchPersistence * self.ewprob)
        for end in deadends:
            self.space[end] = 'C'

    def spawn_nscorridors(self, space, cradix, half_width, half_height, flavor, nsprob, ewprob):
        """Spawns the NSComponent's main north-south corridors"""
        x, y = self.index                           # top left index of the component
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        nairlocks = filter(lambda airlock: airlock.coords[1]==y-1,self.airlocks)          # north airlocks (each is an (x,y) just outside the comp)
        sairlocks = filter(lambda airlock: airlock.coords[1]==y+cheight,self.airlocks)      # south airlocks
        maincorridors = max(1,randint(cwidth/10, int(cwidth/3.5)), len(nairlocks) + len(sairlocks))     # how many n/s corridors left?
        deadends = []
        newdoors = []
        for na in nairlocks:               # place corridors spawned by north airlocks
            m, n = na.coords
            if is_character(space, (m,n+1), '#'):
                cl = min(randint(cheight/5, cheight*9/5), cheight)
                for c in range(cl):
                    space[(m,n+c+1)] = 'C'
                maincorridors -= 1
                if cl != cheight:
                    space[(m,n+cl)] = 'c'            # dead-ends get lowercase c
                    deadends.append((m,n+cl))
                elif not is_character(self.space, (m,n+cl+2), '#'):
                    newdoors.append((m,n+cl+1))
        for sa in sairlocks:               # place corridors spawned by south airlocks
            m, n = sa.coords
            if is_character(space, (m,n-1), '#'):
                cl = min(randint(cheight/5, cheight*9/5), cheight)
                for c in range(cl):
                    space[(m,n-c-1)] = 'C'
                maincorridors -= 1
                if cl != cheight:
                    space[(m,n-cl)] = 'c'
                    deadends.append((m,n-cl))
                elif not is_character(self.space, (m,n-cl-2), '#'):
                    newdoors.append((m,n-cl-1))
        if random() < nsprob or self.station.component_count == 1:
            while maincorridors > 0:        # place any other main corridors at random
                spot = randint(0,cwidth-1)
                if cradix[2] == 's':       # do they start at the north, to mirror the airlock-spawned southern corridors?
                    if is_character(space, (x+spot,y), '#') and not is_character(space, (x+spot+1,y), 'C') \
                       and not is_character(space, (x+spot-1,y), 'C') and not is_character(space, (x+spot-1,y+cheight-1), 'C') \
                       and not is_character(space, (x+spot+1,y+cheight-1), 'C'): # and not is_character(self.space, (x+spot,y-2), '#'):
                        cl = min(randint(cheight/5, cheight*9/5), cheight)
                        for c in range(cl):
                            space[(x+spot,y+c)] = 'C'
                        maincorridors -= 1
                        newdoors.append((x+spot,y-1))
                        if cl != cheight:
                            space[(x+spot,y+cl-1)] = 'c'
                            deadends.append((x+spot,y+cl-1))
                        elif not is_character(self.space, (x+spot,y+cl+1), '#'):
                            newdoors.append((x+spot,y+cl))
                elif cradix[2] == 'n':                       # or at the south, to mirror the airlock-spawned norther corridors?
                    if is_character(space, (x+spot,y+cheight-1), '#') and not is_character(space, (x+spot+1,y), 'C') \
                       and not is_character(space, (x+spot-1,y), 'C') and not is_character(space, (x+spot-1,y+cheight-1), 'C') \
                       and not is_character(space, (x+spot+1,y+cheight-1), 'C'): # and not is_character(self.space, (x+spot,y+cheight+1), '#'):
                        cl = min(randint(cheight/5, cheight*9/5), cheight)
                        for c in range(cl):
                            space[(x+spot,y+cheight-c-1)] = 'C'
                        maincorridors -= 1
                        newdoors.append((x+spot,y+cheight))
                        if cl != cheight:
                            space[(x+spot,y+cheight-cl)] = 'c'
                            deadends.append((x+spot,y+cheight-cl))
                        elif not is_character(self.space, (x+spot,y+cheight-cl-2), '#'):
                            newdoors.append((x+spot,y+cheight-cl-1))
        self.prune_doors(newdoors)
        for door in newdoors:
            self.airlocks.append(Airlock(self.space, self.station, door, [self]))
        self.station.update_equipment()
        if newdoors:
            self.station.spawn_component((cradix[0], cradix[1] + cheight + 1 if cradix[2] == 'n' else cradix[1] - cheight - 1, cradix[2]), \
                                         self.flavor, self.airlocks, nsprob * branchPersistence, ewprob)
        self.spawn_webranches(deadends)

    def __init__(self, space, station, cradix, half_width, half_height, flavor, airlocks, nsprob, ewprob):
        Component.__init__(self, space, station, cradix, half_width, half_height, flavor, airlocks, nsprob, ewprob)
        self.spawn_nscorridors(space, cradix, half_width, half_height, self.flavor, nsprob, ewprob)
        link_corridors(space, self.index, self.width, self.height, self.airlocks)
        self.place_equipment()


class WEComponent(Component):
    """Components oriented west-east"""
    def spawn_nsbranches(self, deadends):
        """Spawns branches west and east from the main corridors' deadends"""
        x, y = self.index
        cwidth = 2 * self.half_width + 1
        cheight = 2 * self.half_height + 1
        nairlocks = filter(lambda airlock: airlock.coords[1]==y-1,self.airlocks)              # north airlocks
        sairlocks = filter(lambda airlock: airlock.coords[1]==y+cheight,self.airlocks)        # south airlocks
        wairlocks = filter(lambda airlock: airlock.coords[0]==x-1,self.airlocks)              # west airlocks
        eairlocks = filter(lambda airlock: airlock.coords[0]==x+cwidth,self.airlocks)         # east airlocks
        branches = max(1,randint(cwidth/5, int(cwidth/3.5)), len(nairlocks) + len(sairlocks))     # how many n/s corridors left?
        nokay = sokay = False
        if len(nairlocks) > 0:
            nokay = True
        if len(sairlocks) > 0:
            sokay = True
        if random() < self.nsprob:
            tricoin = random()
            if tricoin > 0.3:
                nokay = True
            if tricoin < 0.7:
                sokay = True
        for sa in sairlocks:
            m, n = sa.coords
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
        for na in nairlocks:
            m, n = na.coords
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
                       and not is_character(self.space, (x+spot+1,y+cheight-1), 'C') and not is_character(self.space, (x+spot,y+cheight+1), '#'):
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
                       and not is_character(self.space, (x+spot+1,y+cheight-1), 'C') and not is_character(self.space, (x+spot,y-2), '#'):
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
        self.connect_deadends(deadends)                 # now let's connect some dead-ends
        self.prune_doors(newdoors)
        for door in newdoors:
            self.airlocks.append(Airlock(self.space, self.station, door, [self]))
        self.station.update_equipment()
        if newdoors:
            direc = ['n', 's']
            if not filter(lambda airlock: airlock.coords[1]==y-1,self.airlocks):          # any north airlocks?
                direc.remove('s')
            if not filter(lambda airlock: airlock.coords[1]==y+cheight,self.airlocks):    # or south airlocks?
                direc.remove('n')
            while direc:
                tion = direc.pop(randint(0,len(direc)-1))                    # pick a direction and spawn some components!
                spawny = self.index[1] - 2 if tion == 's' else self.index[1] + cheight + 1
                self.station.spawn_component((self.index[0] + self.half_width, spawny, tion), \
                                             self.flavor, self.airlocks, \
                                             self.nsprob * branchPersistence, self.ewprob)
        for end in deadends:
            self.space[end] = 'C'

    def spawn_wecorridors(self, space, cradix, half_width, half_height, flavor, nsprob, ewprob):
        """Spawns the WEComponent's main west-east corridors"""
        x, y = self.index                               # top left index of the component
        cwidth = 2 * half_width + 1
        cheight = 2 * half_height + 1
        wairlocks = filter(lambda airlock: airlock.coords[0]==x-1,self.airlocks)          # west airlocks (each is an (x,y) just outside the comp)
        eairlocks = filter(lambda airlock: airlock.coords[0]==x+cwidth,self.airlocks)      # east airlocks
        maincorridors = max(1,randint(cheight/10, int(cheight/3.5)), len(wairlocks) + len(eairlocks))     # how many w/e corridors left?
        deadends = []
        newdoors = []
        for wa in wairlocks:               # place corridors spawned by west airlocks
            m, n = wa.coords
            if is_character(space, (m+1,n), '#'):
                cl = min(randint(cwidth/5, cwidth*9/5), cwidth)
                for c in range(cl):
                    space[(m+c+1,n)] = 'C'
                maincorridors -= 1
                if cl != cwidth:
                    space[(m+cl,n)] = 'c'            # dead-ends get lowercase c
                    deadends.append((m+cl,n))
                elif not is_character(self.space, (m+cl+2,n), '#'):
                    newdoors.append((m+cl+1,n))
        for ea in eairlocks:               # place corridors spawned by east airlocks
            m, n = ea.coords
            if is_character(space, (m-1,n), '#'):
                cl = min(randint(cwidth/5, cwidth*9/5), cwidth)
                for c in range(cl):
                    space[(m-c-1,n)] = 'C'
                maincorridors -= 1
                if cl != cwidth:
                    space[(m-cl,n)] = 'c'
                    deadends.append((m-cl,n))
                elif not is_character(self.space, (m-cl-2,n), '#'):
                    newdoors.append((m-cl-1,n))
        if random() < ewprob or self.station.component_count == 1:
            while maincorridors > 0:        # place any other main corridors at random
                spot = randint(0,cheight-1)
                if cradix[2] == 'e':       # do they start at the west, to mirror the airlock-spawned eastern corridors?
                    if is_character(space, (x,y+spot), '#') and not is_character(space, (x,y+spot+1), 'C') \
                       and not is_character(space, (x,y+spot-1), 'C') and not is_character(space, (x+cwidth-1,y+spot-1), 'C') \
                       and not is_character(space, (x+cwidth-1,y+spot+1), 'C'): # and not is_character(self.space, (x-2,y+spot), '#'):
                        cl = min(randint(cwidth/5, cwidth*9/5), cwidth)
                        for c in range(cl):
                            space[(x+c,y+spot)] = 'C'
                        maincorridors -= 1
                        newdoors.append((x-1,y+spot))
                        if cl != cwidth:
                            space[(x+cl-1,y+spot)] = 'c'
                            deadends.append((x+cl-1,y+spot))
                        elif not is_character(self.space, (x+cl+1,y+spot), '#'):
                            newdoors.append((x+cl,y+spot))
                elif cradix[2] == 'w':                       # or at the east, to mirror the airlock-spawned western corridors?
                    if is_character(space, (x+cwidth-1,y+spot), '#') and not is_character(space, (x,y+spot+1), 'C') \
                       and not is_character(space, (x,y+spot-1), 'C') and not is_character(space, (x+cwidth-1,y+spot-1), 'C') \
                       and not is_character(space, (x+cwidth-1,y+spot+1), 'C'): # and not is_character(self.space, (x+cwidth+1,y+spot), '#'):
                        cl = min(randint(cwidth/5, cwidth*9/5), cwidth)
                        for c in range(cl):
                            space[(x+cwidth-c-1,y+spot)] = 'C'
                        maincorridors -= 1
                        newdoors.append((x+cwidth,y+spot))
                        if cl != cwidth:
                            space[(x+cwidth-cl,y+spot)] = 'c'
                            deadends.append((x+cwidth-cl,y+spot))
                        elif not is_character(self.space, (x+cwidth-cl-2,y+spot), '#'):
                            newdoors.append((x+cwidth-cl-1,y+spot))
        self.prune_doors(newdoors)
        for door in newdoors:
            self.airlocks.append(Airlock(self.space, self.station, door, [self]))
        self.station.update_equipment()
        if newdoors:
            self.station.spawn_component((cradix[0] + cwidth + 1 if cradix[2] == 'w' else cradix[0] - cwidth - 1, cradix[1], cradix[2]), \
                                         self.flavor, self.airlocks, nsprob, ewprob * branchPersistence)
        self.spawn_nsbranches(deadends)

    def __init__(self, space, station, cradix, half_width, half_height, flavor, airlocks, nsprob, ewprob):
        Component.__init__(self, space, station, cradix, half_width, half_height, flavor, airlocks, nsprob, ewprob)
        self.spawn_wecorridors(space, cradix, half_width, half_height, flavor, nsprob, ewprob)
        link_corridors(space, self.index, self.width, self.height, self.airlocks)
        self.place_equipment()


class Equipment(object):
    """Equipment is the guts of a station

    besides helping the player survive and attain goals, sometimes equipment contains loot when spawned"""
    def starting_loot(self):
        stuff = loot(equipmentLoot[self.type])
        for s in stuff:
            self.inv[s] += int(random()*(10*stuff[s]*self.width*self.height)**0.5)      # random*20x^0.5, so smalls get biggified and bigs get smallened

    def access_points(self, character='C'):
        """This finds all the points surrounding this equipment which match the desired character"""
        x, y = self.eindex
        adjacent = []
        for ln in range(self.height):
            adjacent.append((x-1, y+ln))
            adjacent.append((x+self.width, y+ln))
        for pt in range(self.width):
            adjacent.append((x+pt, y-1))
            adjacent.append((x+pt, y+self.height))
        return filter(lambda a: is_character(self.space, a, character), adjacent)

    def __init__(self, space, station, component, eindex, width, height, type, flavor):
        self.space = space
        self.station = station
        self.component = component
        self.eindex = eindex
        self.width = width
        self.height = height
        self.access = self.access_points()
        self.type = type
        self.flavor = flavor
        self.inv = {'metal':0, 'wire':0, 'plastic':0, 'silica':0, 'electrolytes':0, 'hydrogen':0, 'diodes':0, \
                    'photocells':0, 'transistors':0, 'leds':0, 'screens':0, 'capacitors':0, 'resistors':0, \
                    'oscillators':0, 'batteries':0, 'antennas':0, 'transformers':0, 'inductors':0, 'scrap':0, \
                    'trash':0, 'food':0, 'water':0, 'medicine':0}
        self.starting_loot()
        self.power = equipmentPower[type]*width*height


class Airlock(object):
    """Airlocks join adjacent components"""
    def __init__(self, space, station, coords, components):
        self.space = space
        self.station = station
        self.coords = coords
        self.components = components    # external = len(self.components) - 1?


grid = Grid()
gameDisplay.fill(backgroundColor)     # and a blank image window

stations.append(Station(outerSpace, (0, 0, cardinals[randint(0, 3)]), season(defaultFlavor)))  # (what region?, (origin x,origin y,from what direction?), what flavors?)

playerOne = Person(outerSpace, stations[0], stations[0].enter(), [playerImage, playerWalk1, playerWalk2, playerAction], \
                   {'metal':0, 'wire':0, 'plastic':0, 'silica':0, 'electrolytes':0, 'hydrogen':0, 'diodes':0, \
                    'photocells':0, 'transistors':0, 'leds':0, 'screens':0, 'capacitors':0, 'resistors':0, \
                    'oscillators':0, 'batteries':0, 'antennas':0, 'transformers':0, 'inductors':0, 'scrap':0, \
                    'trash':0, 'food':0, 'water':0, 'medicine':0})

stations[0].update_equipment()
print "Station power is", stations[0].power, "out of", stations[0].power_storage, "changing by", stations[0].power_change, \
    "while oxygen is", stations[0].oxygen, "out of", stations[0].air_capacity, "changing by", stations[0].oxygen_change, \
    "pressure is", stations[0].pressure, "changing by", stations[0].pressure_change
print "Station humidity is", stations[0].humidity, "changing by", stations[0].humidity_change, \
    "temperature is", stations[0].temperature, "changing by", stations[0].temperature_change, \
    "and station, which stretches from", stations[0].index, "to", (stations[0].extent()[2],stations[0].extent()[3]), \
    "contains", len(stations[0].population), "souls."

grid.update(wIndex, winZoom, outerSpace)              # put that space on the screen

game_loop(mouse, grid, wIndex, winZoom, playerOne, outerSpace)  # run the game until the user hits the x
pygame.quit()  # if by some miracle you get here without that happening, quit immediately omg
quit()

# Do:  Fix seed 274 can't remove deadend.  Components forming with airlocks at diagonals.  Make UI (parametric readouts!) /NPCs/equipment rules!

# Make solar arrays?  Make transportation (roboferry? jetpack zipline?)
# Other equipment?  Armory?  Science?  Propulsion?  Other resources? (23 currently)  Lubricants? Insulation?
# Items?  Pack?  Keycard?  Jetpack/autobot? Angle grinder?  Welder?
# Rally NPCs: Proximity to liked characters.  Enjoyable work.  Childcare?  Shared victories?
# Crises: Space storms?  Meteorites, static discharge, accidents, equipment failures.  Boredom? Anxiety? Drama.  Theft?  Of "medicine"?
