__copyright__ = """ Copyright (c) 2010 Torsten Schmits

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.

"""

import logging, os

import VisionEgg
from VisionEgg.Core import Screen, Viewport
from VisionEgg.FlowControl import Presentation

from pygame import Color

from lib import marker

from model.color_word import ColorWord
from util.switcherator import Flag, Switcherator

class VisionEggView(object):
    """ This class handles VisionEgg internals and the creation of
    common/standard stimuli like centered words, a fixation cross or
    a countdown. Inherit this and pass the type to VisionEggFeedback
    for customization.
    """
    def __init__(self):
        self.__init_attributes()

    def __init_attributes(self):
        """ Setup internal attributes. """
        self._logger = logging.getLogger('VisionEggView')
        self._logger.addHandler(logging.FileHandler('log'))
        self._screen_acquired = False
        self._viewports = []

    def set_trigger_function(self, trigger):
        self._trigger = trigger

    def set_event_handlers(self, event_handlers):
        """ Set pygame/VisionEgg event handler function. """
        self._event_handlers = event_handlers

    def set_iterator_semaphore(self, flag):
        """ Specify the object to be used as semaphore for iterators.
        See L{Switcherator} for more.
        """
        self._iter = lambda it: Switcherator(flag, it)

    def update_parameters(self, **kwargs):
        """ Apply new parameters set from pyff. """
        for k, v in kwargs.iteritems():
            setattr(self, '_' + k, v)
        if self._screen_acquired:
            self.reinit()

    def acquire(self):
        """ Allow L{update_parameters} initialize VisionEgg. """
        self._screen_acquired = True

    def reinit(self):
        """ Initialize VisionEgg objects. """
        self.__init_screen()
        self.__init_text()
        self.__init_presentation()
        self.__init_viewports()
        self.init()

    def init(self):
        """ Overload this for additional custom VisionEgg
        initialization.
        """
        pass

    def __init_screen(self):
        """ Create the VisionEgg Screen object using the pyff
        configuration parameters 'fullscreen' and 'geometry' and the
        font and background colors according to parameters
        'font_color_name' and 'bg_color'.
        """
        params = { 'fullscreen': self._fullscreen, 'sync_swap': True }
        if not self._fullscreen:
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%d, %d' % (self._geometry[0],
                                                            self._geometry[1])
            params['size'] = self._geometry[2:]
        self.screen = Screen(**params)
        self._set_bg_color()
        self._set_font_color()

    def __init_text(self):
        """ Provide a text in the screen center for standard stimuli and
        fixation cross etc.
        """
        sz = self.screen.size
        self._center_text = ColorWord((sz[0] / 2., sz[1] / 2.),
                                      symbol_size=self._font_size)

    def __init_viewports(self):
        """ Provide a standard viewport. """
        self._standard_viewport = Viewport(screen=self.screen,
                                         stimuli=self._center_text)
        self.add_viewport(self._standard_viewport)

    def __init_presentation(self):
        """ Provide a standard presentation object. """
        self.presentation = Presentation(handle_event_callbacks=
                                         self._event_handlers)

    def add_viewport(self, viewport):
        """ Add an additional custom viewport object to the list of
        viewports.
        """
        self._viewports.append(viewport)
        self.presentation.set(viewports=self._viewports)

    def clear_stimuli(self):
        """ Remove all existing stimuli in the standard viewport. """
        self.set_stimuli()

    def add_stimuli(self, *stimuli):
        """ Add additional custom stimulus objects to the list of
        stimuli.
        """
        stimuli = self._standard_viewport.parameters.stimuli + list(stimuli)
        self.set_stimuli(*stimuli)

    def set_stimuli(self, *stimuli):
        """ Set the list of stimulus objects.  """
        self._standard_viewport.set(stimuli=list(stimuli))

    def add_text(self, text, font_size=None, **kw):
        if not kw.has_key('anchor'):
            kw['anchor'] = 'center'
        font_size = font_size or self._font_size
        txt = VisionEgg.Text.Text(text=text, font_size=font_size, **kw)
        self.add_stimuli(txt)
        return txt

    def add_image(self, filename, **kw):
        if not kw.has_key('anchor'):
            kw['anchor'] = 'center'
        txtr = VisionEgg.Textures.Texture(filename)
        img = VisionEgg.Textures.TextureStimulus(texture=txtr, **kw)
        self.add_stimuli(img)
        return img

    def _set_font_color(self):
        """ Set the standard font color by pygame name. """
        try:
            self._font_color = Color(self._font_color_name).normalize()
        except ValueError:
            self._logger.warn('No such pygame.Color: %s' %
                              str(self._font_color_name))

    def _set_bg_color(self):
        """ Set the standard background color by pygame name. """
        try:
            self.screen.set(bgcolor=Color(self._bg_color).normalize())
        except ValueError:
            self._logger.warn('No such pygame.Color: %s' % str(self._bg_color))

    def present_frames(self, num_frames):
        """ Launch the presentation main loop for a given number of
        frames.
        """
        self.presentation.set(go_duration=(num_frames, 'frames'))
        self.presentation.go()

    def present(self, sec):
        self.presentation.set(go_duration=(sec, 'seconds'))
        self.presentation.go()

    def update(self):
        """ Repaint the canvas for one frame to update changed stimuli.
        """
        self.present_frames(1)

    def center_word(self, text, color=None):
        """ Set the standard word in the screen center. """
        self._center_text.set(text=text)
        self._center_text.set(colors=color or (self._font_color for l in
                                           self._center_text))

    def ask(self):
        """ Display a question mark in the center and wait for keyboard
        input. The query is terminated by calling L{answered}.
        """
        self.center_word('?')
        self._asking = True
        self.presentation.run_forever()
        self.presentation.set(quit=False)

    def answered(self):
        """ Abort the current presentation (usually the question mark)
        after subject input.
        """
        self.presentation.set(quit=True)
        self.clear_symbol()

    def show_fixation_cross(self):
        """ Display the pyff parameter 'fixation_cross_symbol' for the
        period of time given by pyff parameter 'fixation_cross_time'.
        """
        self.center_word(self._fixation_cross_symbol)
        self._trigger(marker.FIXATION_START)
        self.present(self._fixation_cross_time)
        self._trigger(marker.FIXATION_END)

    def clear_symbol(self):
        """ Remove the center word from the screen. """
        self.center_word('')
        self.update()

    def countdown(self):
        """ Display a countdown according to pyff parameters
        'countdown_start' and 'countdown_symbol_duration'.
        """
        self._trigger(marker.COUNTDOWN_START)
        for i in self._iter(reversed(xrange(self._countdown_start + 1))):
            self.center_word(str(i))
            self.present(self._countdown_symbol_duration)
        self._trigger(marker.COUNTDOWN_END)
        self.clear_symbol()

    def close(self):
        """ Shut down the screen. """
        self._screen_acquired = False
        self.screen.close()

    def quit(self):
        """ Stop the presentation. """
        self.presentation.set(quit=True)
        self.presentation.set(go_duration=(1, 'frames'))
