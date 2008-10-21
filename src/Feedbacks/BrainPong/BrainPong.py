#from Feedback import Feedback
import pygame, random, sys, math

#class BucketFeedback(Feedback):
class BrainPong(object):

################################################################################
# Derived from Feedback
#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

    def on_init(self):
        """
        Initializes variables etc., but not pygame itself.
        """
        #self.logger.debug("on_init")
        
        self.parameters = {
        #   Name from GUI : (local variablename, default value)
            'duration' : ('durationPerTrial', 30000),
            'trials_per_run' : ('trials', 10),
            'break_every' : ('pauseAfter', 5),
            'duration_break' : ('pauseDuration', 9000),
            'directions' : ('availableDirections', ['left', 'right']),
            'fps' : ('FPS', 60),
            'fullscreen' : ('fullscreen', False),
            'screen_width' : ('screenWidth',  1200),
            'screen_height' : ('screenHeight', 700),
            'countdown_from' : ('countdownFrom', 1),
            'hit_miss_duration' : ('hitMissDuration', 1000),
            'time_until_next_trial' : ('timeUntilNextTrial',500),
            'walls' : ('walls',True)
            #'bowlSize' : ('bowlDiameter', 50),
            #'barSize' : ('barSize', (300, 50))
        }
        for p in self.parameters.values():
            self.__setattr__(p[0], p[1])
        
        self.showGameOverDuration = 1000
        
        self.alternate = True
        
        # Feedback state booleans
        self.quit, self.quitting = False, False
        self.pause, self.shortPause = False, False
        self.gameover, self.hit, self.miss = False, False, False
        self.countdown, self.firstTickOfTrial = True, True
        self.showsPause, self.showsShortPause = False, False
       
        self.elapsed, self.trialElapsed, self.countdownElapsed = 0,0,0
        self.hitMissElapsed, self.shortPauseElapsed, self.completedTrials = 0,0,0
        self.showsHitMiss = False
        
        self.f = 0
        self.hitMiss = [0,0]
        
        # Colours
        self.backgroundColor = (50, 50, 50)
        self.barColor = (237, 100, 148)#(0,50,50)
        self.bowlColor = (237, 100, 148)#(0,0,255) #(100, 149, 237)
        self.hitFontColor = (0,200,0) 
        self.missFontColor = (200,0,0)
        self.fontColor = (0,150,150)
        self.countdownColor = (237, 100, 148)
        
        # Bowl direction
        self.left = True
        self.down = True
        
        self.it = 0;

    def on_play(self):
        """
        Initialize pygame, the graphics and start the game.
        """
        #self.logger.debug("on_play")
        self.init_pygame()
        self.init_graphics()
        self.quit = False
        self.quitting = False
        self.main_loop()


    def on_pause(self):
        """
        Flip the pause variable.
        """
        #self.logger.debug("on_pause")
        self.pause = not self.pause
        self.showsPause = False


    def on_quit(self):
        """
        Quit the main loop indirectly by setting quit, wait for the mainloop
        until it has quit and close pygame.
        """
        #self.logger.debug("on_quit")
        self.quitting = True
        #self.logger.debug("Waiting for main loop to quit...")
        while not self.quit:
            pygame.time.wait(100)
        #self.logger.debug("Quitting pygame.")
        pygame.quit()


    def on_interaction_event(self, data):
        """
        Translate the incoming variable-value tuples to the local variables.
        """
        #self.logger.debug("on_interaction_event: %s" % str(data))
        for var, val in data.items():
            if self.parameters.has_key(var):
                local = self.parameters[var][0]
                self.__setattr__(local, val)
            #else:
                #self.logger.warning("Caught unknown variable %s" % str(var))

    def on_control_event(self, data):
        ##self.logger.debug("on_control_event: %s" % str(data))
        self.f = data[-1]

#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Derived from Feedback
################################################################################

    def main_loop(self):
        """
        Main Loop. Represents the loop which refreshes the screen x times per
        second. Runs forever or until the GUI emits the stop signal.
        """
        # just to reset the time when tick was called last time...
        self.clock.tick(self.FPS)
        while not self.quitting:
            self.process_pygame_events()
            pygame.time.wait(10)
            self.elapsed = self.clock.tick(self.FPS)
            self.tick()
        #self.logger.debug("Left the main loop.")
        self.quit = True


    def tick(self):
        """
        One tick of the main loop.
        
        Decides in wich state the feedback currently is and calls the apropriate
        tick method.
        """
        if self.pause:
            self.pause_tick()
        elif self.gameover:
            self.gameover_tick()
        elif self.countdown:
            self.countdown_tick()
        elif self.hit or self.miss:
            self.hit_miss_tick()
        elif self.shortPause:
            self.short_pause_tick()
        else:
            self.trial_tick()
    
    
    def trial_tick(self):
        """
        One tick of the trial loop.
        """
        self.trialElapsed += self.elapsed
        
        if self.firstTickOfTrial:
            self.trialElapsed = 0
            # initialize feedback start screen
            self.init_graphics()
            self.draw_initial() 
            pygame.time.wait(self.timeUntilNextTrial)
            self.firstTickOfTrial = False     

        # Sonst laufe im normalen Trial weiter
        # Redraw background
        self.screen.blit(self.background, self.backgroundRect)
        if self.walls:
            self.screen.blit(self.wall, self.wallRect1)
            self.screen.blit(self.wall, self.wallRect2)
        
        
        # Check, if trial is over (if y-pos of bowl is on bottom of the screen)
        # or if the trial time is over
        (bowlPosX, bowlPosY) = self.bowlRect.midbottom
        if bowlPosY >= self.screenHeight:
            self.miss = True; return
        if self.trialElapsed > self.durationPerTrial:
            self.hit = True; return
            
        # Calculate motion of bowl
        stepX = 2
        stepY = 2*stepX #math.tan(math.radians(60))*stepX
        if self.left == True:   stepX = -stepX
        if self.down == False:  stepY = -stepY
        
        # if bowl is hitting the bar "surface"
        (barLeftX, barRightX) = (self.barMoveRect.left, self.barMoveRect.right)
        if bowlPosY+stepY >= self.barSurface:
            # check if bar is at the same x-coordinate, 
            # if yes: bounce ball, else: miss
            if bowlPosX > barLeftX and bowlPosX < barRightX:
                self.down = False
            else:
                tolerance = 10
                if barLeftX-bowlPosX>10 or bowlPosX-barRightX>10:
                    self.miss = True; return
                
        # if bowl is hitting the "ceiling"    
        elif bowlPosY-self.bowlRect.height+stepY < 0:
            self.down = True
            
        # if bowl is hitting the side of the screen
        border1 = bowlPosX+stepX-(self.bowlRect.width/2+self.wallSize[0])
        border2 = bowlPosX+stepX+self.bowlRect.width/2+self.wallSize[0]
        if  border1<0 or  border2>self.screenWidth:
                self.left = not self.left
        
        # Move bowl
        self.bowlRect.move_ip(stepX,stepY)
        self.screen.blit(self.bowl, self.bowlRect)
        
        # Move bar according to classifier output (TODO: use self.f)
        self.it += 1
        class_out = math.sin(self.it*0.03)
        moveLength = (self.screenWidth-2*self.wallSize[0]-self.barRect.width) / 2
        self.barMoveRect = self.barRect.move(class_out*moveLength,0)
        self.screen.blit(self.bar, self.barMoveRect)
        
        # Repaint everything
        pygame.display.update()



    def pause_tick(self):
        """
        One tick of the pause loop.
        """
        if self.showsPause:
            return
        self.do_print("Pause", self.fontColor, self.size/6)
        self.showsPause = True

        
    def short_pause_tick(self):
        """
        One tick of the short pause loop.
        """
        self.shortPauseElapsed += self.elapsed
        if self.shortPauseElapsed >= self.pauseDuration:
            self.showsShortPause = False
            self.shortPause = False
            self.shortPauseElapsed = 0
            self.countdown = True
            return
        if self.showsShortPause:
            return
        self.do_print("Short Break...", self.fontColor, self.size/6)
        self.showsShortPause = True

    
    def countdown_tick(self):
        """
        One tick of the countdown loop.
        """
        self.countdownElapsed += self.elapsed
        if self.countdownElapsed >= self.countdownFrom * 1000:
            self.countdown = False
            self.countdownElapsed = 0
            return
        t = (self.countdownFrom * 1000 - self.countdownElapsed) / 1000
        self.do_print(str(t), self.countdownColor, self.size/3)

        
    def gameover_tick(self):
        """
        One tick of the game over loop.
        """
        self.do_print("Game Over! (%i : %i)" % (self.hitMiss[0], self.hitMiss[1]), self.fontColor, self.size/6)
        pygame.time.wait(self.showGameOverDuration)

        
    def hit_miss_tick(self):
        """
        One tick of the Hit/Miss loop.
        """
        self.hitMissElapsed += self.elapsed
        if self.hitMissElapsed >= self.hitMissDuration:
            self.hitMissElapsed = 0
            self.hit, self.miss = False, False
            self.showsHitMiss = False
            return
        if self.showsHitMiss:
            return
        
        self.completedTrials += 1; 
        self.firstTickOfTrial = True
        s = ""
        if self.hit:
            s = "Hit"
            color = self.hitFontColor
            self.hitMiss[0] += 1
            
        else:
            s = "Miss"
            color = self.missFontColor
            self.hitMiss[-1] += 1
            
        if self.completedTrials % self.pauseAfter == 0:
            self.shortPause = True
        if self.completedTrials >= self.trials:
            self.gameover = True
            
        self.do_print(s, color, self.size/7)
        self.screen.blit(self.bowl, self.bowlRect)
        self.screen.blit(self.bar, self.barMoveRect)
        if self.walls:
            self.screen.blit(self.wall, self.wallRect1)
            self.screen.blit(self.wall, self.wallRect2)
        pygame.display.flip()
        self.showsHitMiss = True


    def do_print(self, text, color, size=None, center=None, superimpose=False):
        """
        Print the given text in the given color and size on the screen.
        """
        if not color:
            color = self.fontColor
        if not size:
            size = self.size/10
        if not center:
            center = self.screen.get_rect().center

        font = pygame.font.Font(None, size)
        if not superimpose:
            self.screen.blit(self.background, self.backgroundRect)
        surface = font.render(text, 1, color)
        self.screen.blit(surface, surface.get_rect(center=center))
        if not superimpose:
            pygame.display.update()


    def init_graphics(self):
        """
        Initialize the surfaces and fonts depending on the screen size.
        """
        self.screen = pygame.display.get_surface()
        self.size = min(self.screen.get_height(), self.screen.get_width())
        barHeight = self.screenHeight/15
        self.barSurface = self.screenHeight-barHeight * 3/2
        
        # init background
        img = pygame.image.load('bg.png').convert()
        self.background = pygame.Surface((self.screenWidth, self.screenHeight))
        pygame.transform.scale(img, (self.screenWidth, self.screenHeight), self.background)
        #self.background = pygame.transform.rotate(self.background, 90)
        self.backgroundRect = self.background.get_rect(center=self.screen.get_rect().center)
                
        # init walls
        if self.walls:
            self.wallSize = ((self.screenWidth-self.barSurface)/2,self.screenHeight)
            img = pygame.image.load('wall_metal_blue.png').convert()
            self.wall = pygame.Surface(self.wallSize)
            pygame.transform.scale(img, self.wallSize, self.wall)
            self.wallRect1 = self.wall.get_rect(topleft=(0,0), size=self.wallSize)
            self.wallRect2 = self.wall.get_rect(topleft=(self.screenWidth-self.wallSize[0],0), size=self.wallSize)   
            self.fontsize_target = self.size/16
        else:
            self.wallSize=(0,0)
        
        # init bar
        barWidth = (self.screenWidth-2*self.wallSize[0]) / 3
        barSize = (barWidth, barHeight)
        img = pygame.image.load('bar_metallic3.png').convert()
        self.bar = pygame.Surface(barSize)
        pygame.transform.scale(img, barSize, self.bar)
        self.barMB = (self.screenWidth/2, self.barSurface+barHeight)
        self.barRect = self.bar.get_rect(midbottom=self.barMB, size=(barWidth, barHeight))
        
        # init bowl
        diameter = barWidth/5
        bowlSize = (diameter, diameter)
        img = pygame.image.load('bowl_metallic.png').convert()
        self.bowl = pygame.Surface(bowlSize)
        pygame.transform.scale(img, bowlSize, self.bowl)
        self.bowlRect = self.bowl.get_rect(center=((self.screenWidth-2*self.wallSize[0])/3+self.wallSize[0], diameter/2), size=(self.bowl.get_width(), self.bowl.get_height()))
        self.bowl.set_colorkey((0,0,0))
        
        # init helper rectangle for bar (deep copy)
        self.barMoveRect = self.barRect.move(0,0)

    def draw_initial(self):
        # draw images on the screen
        self.screen.blit(self.background, self.backgroundRect)
        self.screen.blit(self.bowl, self.bowlRect)
        self.screen.blit(self.bar, self.barRect)
        if self.walls:
            self.screen.blit(self.wall, self.wallRect1)
            self.screen.blit(self.wall, self.wallRect2)
        pygame.display.flip()


    def init_pygame(self):
        """
        Set up pygame and the screen and the clock.
        """
        pygame.init()
        pygame.display.set_caption('BrainPong')
        if self.fullscreen:
            self.screen = pygame.display.set_mode((self.screenWidth, self.screenHeight), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.screenWidth, self.screenHeight), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()


    def process_pygame_events(self):
        """
        Process the the pygame event queue and react on VIDEORESIZE.
        """
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.init_graphics()
            elif event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                sys.exit()

# HACK
    def main(self):
        self.on_init()
        self.on_play()


if __name__ == '__main__':
    BrainPong().main()
