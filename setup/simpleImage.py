import pygame
import sys

pygame.display.init()

imgSurf = pygame.image.load ('question01.png')
screen = pygame.display.set_mode ( imgSurf.get_size(), pygame.FULLSCREEN )
screen.blit ( imgSurf, ( 0, 0 ) )
pygame.display.flip()

raw_input()
pygame.quit()
