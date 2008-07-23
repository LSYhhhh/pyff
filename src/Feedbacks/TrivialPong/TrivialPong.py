from Feedback import Feedback

import pygame
import os


class TrivialPong(Feedback):
    
    def on_init(self):
        self.FPS = 60
        
        self.pause, self.stopping, self.stop = False, False, False
        

    def main_loop(self):
        while 1:
            self.clock.tick(self.FPS)

            if self.pause:
                continue
            if self.stopping:
                break

            val = self._data[-1]
            w_half = self.screen.get_width() / 2
            pos = w_half + w_half * val
            self.barrect.center = pos, self.height - 20

            self.ballrect = self.ballrect.move(self.speed)
            if self.ballrect.left < 0 or self.ballrect.right > self.width:
                self.speed[0] = -self.speed[0]
            if self.ballrect.top < 0 or self.ballrect.bottom > self.height:
                self.speed[1] = -self.speed[1]
        
            if self.barrect.left < 0 or self.barrect.right > self.width:
                self.barspeed[0] = -self.barspeed[0]
            if self.barrect.top < 0 or self.barrect.bottom > self.height:
                self.barspeed[1] = -self.barspeed[1]
        
            if self.barrect.colliderect(self.ballrect):
                self.speed[0] = -self.speed[0]
                self.speed[1] = -self.speed[1]
            
            self.screen.fill( (0,0,0) )
            self.screen.blit(self.ball, self.ballrect)
            self.screen.blit(self.bar, self.barrect)
            pygame.display.flip()
        
        self.stop = True
    
    
    def on_play(self):
        pygame.init()
        
        self.size = self.width, self.height = 800, 600
        self.speed = [2, 2]
        black = 0, 0, 0

        path = os.path.dirname( globals()["__file__"] ) 

        self.screen = pygame.display.set_mode(self.size)
        self.ball = pygame.image.load(os.path.join(path, "ball.png"))
        self.ballrect = self.ball.get_rect()
        self.bar = pygame.image.load(os.path.join(path, "bar.png"))
        self.barrect = self.bar.get_rect()
        self.barspeed = [3, 0]

        self.clock = pygame.time.Clock()
        
        self.main_loop()
    
    
    def on_pause(self):
        self.logger.debug("on_pause")
        self.pause = not self.pause
    
    
    def on_quit(self):
        self.stopping = True
        while not self.stop:
            pass
        self.logger.debug("main loop returned, quitting pygame")
        pygame.quit()
    
    
    def on_interaction_event(self, data):
        pass
    
    
    def on_control_event(self, data):
        pass
    
