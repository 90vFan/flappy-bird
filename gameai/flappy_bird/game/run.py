import sys
import argparse
from itertools import cycle
import random
import pygame
from pygame.constants import KEYDOWN, K_SPACE, K_UP
from loguru import logger
from time import sleep

from gameai.flappy_bird.game.settings import *


parser = argparse.ArgumentParser("learn.py")
parser.add_argument("--iter", type=int, default=1000,
                    help="number of iterations to run")
parser.add_argument(
    "--verbose", type=bool, default=True, help="output [iteration | score] to stdout"
)
parser.add_argument("-d", "--daemon", type=bool, default=False,
                    help="run in daemon without visualization")
args = parser.parse_args()
ITERATIONS = args.iter
VERBOSE = args.verbose
DAMEON = args.daemon

PLAYER_INDEX_GEN = cycle([0, 1, 2, 1])


class Game(object):
    def __init__(self, iter_loop: int=0, daemon=False) -> None:
        self.daemon = daemon
        self.score = 0
        # index of player to blit on screen
        self.playerIndex = 0
        # iterator used to change playerIndex after every 5th iteration
        self.loopIter = iter_loop

        self.playerx = int(SCREENWIDTH * 0.2)
        self.playery = int((SCREENHEIGHT - PLAYER_HEIGHT) / 2)
        self.basex = 0
        # amount by which base can maximum shift to left
        self.baseShift = IMAGES['base'].get_width() - BACKGROUND_WIDTH

        # get 2 new pipes to add to upperPipes lowerPipes list
        newPipe1 = getRandomPipe()
        newPipe2 = getRandomPipe()
        # list of upper pipes
        self.upperPipes = [
            {'x': SCREENWIDTH + 200, 'y': newPipe1[0]['y']},
            {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
        ]
        # list of lowerpipe
        self.lowerPipes = [
            {'x': SCREENWIDTH + 200, 'y': newPipe1[1]['y']},
            {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
        ]
        # shm values: value: [-8, 8], direction: {0,1}
        self.player_shm_vals = {'val': 0, 'dir': 1}

        # player velocity, max velocity, downward acceleration, acceleration on flap
        self.pipeVelX = -4
        self.playerVelY = -9         # self.'s velocity along Y, default same as playerFlapped
        self.playerMaxVelY = 10      # max vel along Y, max descend speed
        self.playerMinVelY = -8      # min vel along Y, max ascend speed
        self.playerAccY = 1          # players downward acceleration
        self.playerRot = 15          # player's rotation
        self.playerVelRot = 3        # angular speed
        self.playerRotThr = 20       # rotation threshold
        self.playerFlapAcc = -9      # players speed on flapping
        self.playerFlapped = False   # True when player flaps

    def main_play(self):
        if self.daemon:
            # TODO
            return

        while True:
            input_actions = [1, 0]
            for event in pygame.event.get():
                quit_game(event)

                if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                    if self.playery > -2 * PLAYER_HEIGHT:
                    # FIXME: why larger than -2*p_h
                    # if self.playery > 0:
                        self.playerVelY = self.playerFlapAcc
                        self.playerFlapped = True
                        SOUNDS['wing'].play()
                        input_actions = [0, 1]

            self.frame_step(input_actions)

    def frame_step(self, input_actions):
        pygame.event.pump()
        reward = 0.1
        terminal = False

        # input_actions: [0, 1], [1, 0]
        if sum(input_actions) != 1:
            raise ValueError('Multiple input actions!')
        # input_actions[0] == 1: do nothing
        # input_actions[1] == 1: flap the bird
        if input_actions[1] == 1 and self.playery > -2 * PLAYER_HEIGHT:
                # logger.info(f'JUMP player x, y: ({self.playerx}, {self.playery})')
                self.playerVelY = self.playerFlapAcc
                self.playerFlapped = True
                if not self.daemon:
                    SOUNDS['wing'].play()

        is_crashed = self._check_player_crash()
        if is_crashed:
            terminal = True
            reward = -1
            if not self.daemon:
                SCREEN.blit(IMAGES['gameover'], (50, 180))

        if self.playery < -15:
            reward = -0.1

        is_scored = self._check_score()
        if is_scored:
            reward = 1

        self._move_player()
        self._move_pipes_to_left()
        if not self.daemon:
            self._draw_sprites()
            self._draw_score()
            self._draw_player()
        playerShm(self.player_shm_vals)

        if not self.daemon:
            image_data = pygame.surfarray.array3d(pygame.display.get_surface())
            pygame.display.update()
            FPSCLOCK.tick(FPS)
        else:
            image_data = None

        return image_data, reward, terminal

    def _check_player_crash(self):
        # check for crash here
        #logger.info(f'PLAYER x: {self.playerx}, y: {self.playery}')
        crashTest = checkCrash({'x': self.playerx, 'y': self.playery, 'index': self.playerIndex},
                               self.upperPipes, self.lowerPipes)
        if crashTest[0]:
            if not self.daemon:
                SOUNDS['hit'].play()
                SOUNDS['die'].play()
            if VERBOSE:
                self.print_iteration()
            # 重新初始化
            iteration = self.loopIter + 1
            self.__init__(iter_loop=iteration)

        # rotate only when it's a pipe crash
        if not crashTest[1] and self.playerRot > -30:
                self.playerRot -= self.playerVelRot

        return crashTest[0]

    def _check_score(self):
        is_scored = False
        # check for score
        playerMidPos = self.playerx + PLAYER_WIDTH / 2
        for pipe in self.upperPipes:
            pipeMidPos = pipe['x'] + PIPE_WIDTH / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                self.score += 1
                if not self.daemon:
                    SOUNDS['point'].play()
                is_scored = True
        return is_scored

    def _change_basex(self):
        # TODO: what is basex
        # playerIndex basex change
        if (self.loopIter + 1) % 3 == 0:
            self.playerIndex = next(self.playerIndexGen)
        self.loopIter = (self.loopIter + 1) % 30
        self.basex = -((-self.basex + 100) % self.baseShift)

    def _move_player(self):
        # rotate the player
        if self.playerRot > -30:
            self.playerRot -= self.playerVelRot

        # player's movement
        if self.playerVelY < self.playerMaxVelY and not self.playerFlapped:
            self.playerVelY += self.playerAccY

        if self.playerFlapped:
            self.playerFlapped = False
            # more rotation to cover the threshold (calculated in visible rotation)
            self.playerRot = 15

        # player's movement in y axis: move up in v_y or to top ceil
        player_height = IMAGES['player'][self.playerIndex].get_height()
        self.playery += min(self.playerVelY, BASEY - self.playery - player_height)

    def _move_pipes_to_left(self):
        # move pipes to left
        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            uPipe['x'] += self.pipeVelX
            lPipe['x'] += self.pipeVelX

        # add new pipe when first pipe is about to touch left of screen
        if len(self.upperPipes) > 0 and 0 < self.upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            self.upperPipes.append(newPipe[0])
            self.lowerPipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if len(self.upperPipes) > 0 and self.upperPipes[0]['x'] < -PIPE_WIDTH:
            self.upperPipes.pop(0)
            self.lowerPipes.pop(0)

    def _draw_sprites(self):
        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))

        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (self.basex, BASEY))

    def _draw_score(self):
        """displays score in center of screen"""
        scoreDigits = [int(x) for x in list(str(self.score))]
        totalWidth = 0   # total width of all numbers to be printed

        for digit in scoreDigits:
            totalWidth += IMAGES['numbers'][digit].get_width()

        Xoffset = (SCREENWIDTH - totalWidth) / 2

        for digit in scoreDigits:
            SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.1))
            Xoffset += IMAGES['numbers'][digit].get_width()

    def _draw_player(self):
        # Player rotation has a threshold
        visibleRot = self.playerRotThr
        if self.playerRot <= self.playerRotThr:
            visibleRot = self.playerRot

        playerSurface = pygame.transform.rotate(IMAGES['player'][self.playerIndex], visibleRot)
        SCREEN.blit(playerSurface, (self.playerx, self.playery + self.player_shm_vals['val']))

    def print_iteration(self):
        logger.debug(f'Iteration: {self.loopIter} | score: {self.score}')

        # if bot.gameCNT == (ITERATIONS):
        #     bot.dump_qvalues(force=True)
        #     sys.exit()


if __name__ == '__main__':
    g = Game(daemon=self.daemon)
    g.main_play()