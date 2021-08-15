import pygame
import random
import sys
from pygame.constants import QUIT, KEYDOWN, K_ESCAPE
import pathlib

RELATIVE_PATH = str(pathlib.Path(__file__).absolute().parent)

FPS = 30
SCREENWIDTH = 288
SCREENHEIGHT = 512
PIPEGAPSIZE = 100   # gap between upper and lower part of pipe
BASEY = SCREENHEIGHT * 0.79

pygame.init()
pygame.display.set_caption('Flappy Bird')
FPSCLOCK = pygame.time.Clock()
SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))

# list of all possible players (tuple of 3 positions of flap)
PLAYERS_LIST = (
    # red bird
    (
        f'{RELATIVE_PATH}/assets/sprites/redbird-upflap.png',
        f'{RELATIVE_PATH}/assets/sprites/redbird-midflap.png',
        f'{RELATIVE_PATH}/assets/sprites/redbird-downflap.png',
    ),
    # blue bird
    (
        f'{RELATIVE_PATH}/assets/sprites/bluebird-upflap.png',
        f'{RELATIVE_PATH}/assets/sprites/bluebird-midflap.png',
        f'{RELATIVE_PATH}/assets/sprites/bluebird-downflap.png',
    ),
    # yellow bird
    (
        f'{RELATIVE_PATH}/assets/sprites/yellowbird-upflap.png',
        f'{RELATIVE_PATH}/assets/sprites/yellowbird-midflap.png',
        f'{RELATIVE_PATH}/assets/sprites/yellowbird-downflap.png',
    ),
)

# list of backgrounds
BACKGROUNDS_LIST = (
    f'{RELATIVE_PATH}/assets/sprites/background-day.png',
    f'{RELATIVE_PATH}/assets/sprites/background-night.png',
)

# list of pipes
PIPES_LIST = (
    f'{RELATIVE_PATH}/assets/sprites/pipe-green.png',
    f'{RELATIVE_PATH}/assets/sprites/pipe-red.png',
)


def getHitmask(image):
    """returns a hitmask using an image's alpha."""
    mask = []
    for x in range(image.get_width()):
        mask.append([])
        for y in range(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask


def load():
    global IMAGES, SOUNDS, HITMASKS
    # image dicts
    IMAGES = {}
    # numbers sprites for score display
    IMAGES['numbers'] = (
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/0.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/1.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/2.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/3.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/4.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/5.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/6.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/7.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/8.png').convert_alpha(),
        pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/9.png').convert_alpha()
    )

    # game over sprite
    IMAGES['gameover'] = pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/gameover.png').convert_alpha()
    # message sprite for welcome screen
    IMAGES['message'] = pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/message.png').convert_alpha()
    # base (ground) sprite
    IMAGES['base'] = pygame.image.load(f'{RELATIVE_PATH}/assets/sprites/base.png').convert_alpha()
    # background
    randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
    IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()

    # select random player sprites
    randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
    IMAGES['player'] = (
        pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
        pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
        pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
    )

    # select random pipe sprites
    pipeindex = random.randint(0, len(PIPES_LIST) - 1)
    IMAGES['pipe'] = (
        pygame.transform.flip(
            pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), False, True),
        pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
    )

    # sounds
    SOUNDS = {}
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'
    SOUNDS['die'] = pygame.mixer.Sound(f'{RELATIVE_PATH}/assets/audio/die' + soundExt)
    SOUNDS['hit'] = pygame.mixer.Sound(f'{RELATIVE_PATH}/assets/audio/hit' + soundExt)
    SOUNDS['point'] = pygame.mixer.Sound(f'{RELATIVE_PATH}/assets/audio/point' + soundExt)
    SOUNDS['swoosh'] = pygame.mixer.Sound(f'{RELATIVE_PATH}/assets/audio/swoosh' + soundExt)
    SOUNDS['wing'] = pygame.mixer.Sound(f'{RELATIVE_PATH}/assets/audio/wing' + soundExt)

    # hitmask
    HITMASKS = {}
    # hitmask for pipes
    HITMASKS['pipe'] = (
        getHitmask(IMAGES['pipe'][0]),
        getHitmask(IMAGES['pipe'][1]),
    )
    # hitmask for player
    HITMASKS['player'] = (
        getHitmask(IMAGES['player'][0]),
        getHitmask(IMAGES['player'][1]),
        getHitmask(IMAGES['player'][2]),
    )

    return IMAGES, SOUNDS, HITMASKS


IMAGES, SOUNDS, HITMASKS = load()
PLAYER_WIDTH = IMAGES['player'][0].get_width()
PLAYER_HEIGHT = IMAGES['player'][0].get_height()
PIPE_WIDTH = IMAGES['pipe'][0].get_width()
PIPE_HEIGHT = IMAGES['pipe'][0].get_height()
BACKGROUND_WIDTH = IMAGES['background'].get_width()


def quit_game(event):
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        pygame.quit()
        sys.exit()


def getRandomPipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = IMAGES['pipe'][0].get_height()
    pipeX = SCREENWIDTH + 10

    pipes = [
        {'x': pipeX, 'y': gapY - pipeHeight},  # upper pipe
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE}  # lower pipe
    ]
    return pipes


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collides with base or pipes."""
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    # if player crashes into ceil
    if player['y'] + player['h'] >= BASEY - 1:
        return [True, True]

    else:
        playerRect = pygame.Rect(player['x'], player['y'],
                                 player['w'], player['h'])
        pipeW = IMAGES['pipe'][0].get_width()
        pipeH = IMAGES['pipe'][0].get_height()

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # upper and lower pipe rects
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

            # player and upper/lower pipe hitmasks
            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]


def playerShm(playerShm):
    """SHM: 简谐运动
    当某物体进行简谐运动时，物体所受的力跟位移成正比，并且总是指向平衡位置。它是一种由自身系统性质决定的周期性运动（如单摆运动和弹簧振子运动）。实际上简谐振动就是正弦振动：　X = A*cos(w*t + epsilon)

    oscillates the value of playerShm['val'] between 8 and -8
    val: -8 to 8
    dir: direction: -1, 1 (down, up)
    """
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1

    if playerShm['dir'] == 1:
        playerShm['val'] += 1
    else:
        playerShm['val'] -= 1