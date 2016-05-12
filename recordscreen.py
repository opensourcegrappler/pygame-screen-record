import array
import math

import cairo
import pygame
import rsvg
import numpy as np
import subprocess as sp
import time
import cv2

WIDTH = 384
HEIGHT = 384
dimen = str(WIDTH)+'x'+str(HEIGHT)

#initialise the ffmpeg pipe
proc = sp.Popen(['ffmpeg',
             '-y', 
             '-f', 'rawvideo',
             '-vcodec','rawvideo',
             '-s', dimen,
             '-pix_fmt','rgba',
             '-r','10',
             '-i','-',
             '-an',
             '-vcodec', 'qtrle',
                 'newvideo.mov'], stdin=sp.PIPE)

#initialise a cairo surface ready for the svg, 4 channel (rgba)
data = array.array('c', chr(0) * WIDTH * HEIGHT * 4)
surface = cairo.ImageSurface.create_for_data(
    data, cairo.FORMAT_ARGB32, WIDTH, HEIGHT, WIDTH * 4)

#initialise the pygame window
pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
svg = rsvg.Handle(file="guage.svg")
ctx = cairo.Context(surface)
svg.render_cairo(ctx)

screen = pygame.display.get_surface()
image = pygame.image.frombuffer(data.tostring(), (WIDTH, HEIGHT),"ARGB")

#initialise array of example data to feed guage
xx = np.linspace(1,360,360)
    
#initialise the main loop counter
i=0

#start the main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            raise SystemExit

    #iterate through the values of roll
    roll = float(xx[i])
        
    #create some text and blit it to the screen
    font = pygame.font.SysFont("dinnextltpro", HEIGHT/5)
    text = font.render(str(int(abs(roll))), 1, (255,255,255,255))
    textpos = text.get_rect()
    textpos.center = (WIDTH*(0.85),HEIGHT*(0.85))
    screen.blit(text,textpos)
    
    #rotate and recenter the guage
    rotatedSurf = pygame.transform.rotate(image, roll)
    rotRect = rotatedSurf.get_rect()
    rotRect.center = (WIDTH/2,HEIGHT/2) # center of screen

    #blit the guage on the screen
    screen.blit(rotatedSurf,rotRect)

    #get the rgb channels from the screen and make a dummy alpha channel
    r = pygame.surfarray.pixels_red(screen)
    g = pygame.surfarray.pixels_green(screen)
    b = pygame.surfarray.pixels_blue(screen)
    a = np.ones_like(r)*255

    #merge the rgba channels
    mergedImage = cv2.merge((r,g,b,a))

    #rotate the image 90 degrees
    rows,cols,draws = mergedImage.shape
    M = cv2.getRotationMatrix2D((cols/2,rows/2),-90,1)
    rotatedMergedImage = cv2.warpAffine(mergedImage,M,(cols,rows))

    #flip the image horizontally
    rotatedMergedImage = cv2.flip(rotatedMergedImage,1)

    #create a mask of black pixels
    black = rotatedMergedImage[:,:,0] == 0

    #apply the mask to the frame buffer
    rotatedMergedImage[black] = [0,0,0,0]

    #feed the frame buffer to the ffmpeg pipe
    proc.stdin.write(rotatedMergedImage)

    #break the main loop if the end of the data is reached
    if i> len(xx):
        break
    else:
        i += 1

    #delete the arrays of pixel ref data so the screen is no longer locked
    r = []
    g = []
    b = []
    a = []

    #refresh the screen, remove the last frame
    pygame.display.flip()
    screen.fill((0,0,0,255))

#close the pipe, wait for processes to finish
proc.stdin.close()
proc.wait()
