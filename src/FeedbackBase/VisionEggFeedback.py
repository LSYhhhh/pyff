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

import logging

import VisionEgg
import pygame

from FeedbackBase.MainloopFeedback import MainloopFeedback

from lib.vision_egg.view import VisionEggView
from lib.vision_egg.util.stimulus import StimulusSequenceFactory
from lib.vision_egg.util.switcherator import Flag, Switcherator

VisionEgg.config.VISIONEGG_GUI_INIT = 0
VisionEgg.config.VISIONEGG_LOG_TO_STDERR = 0
VisionEgg.logger.setLevel(logging.ERROR)

class VisionEggFeedback(MainloopFeedback):
    """ Main controlling class for VisionEgg feedbacks. It holds and
    creates the view object, handles keyboard input and provides an
    interface for creating stimulus sequence objects, that ensure
    precise presentation timing.
    The view methods L{add_viewport}, L{add_stimuli} and L{set_stimuli}
    are forwarded for convenience.
    """
    def __init__(self, view_type=VisionEggView, *args, **kwargs):
        """ @param view_type: If a custom view class should be used, its
        type can be specified here. See _create_view for more.
        """
        MainloopFeedback.__init__(self, *args, **kwargs)
        self._view_type = view_type
        self.__init_parameters()
        self.__init_attributes()

    def __init_parameters(self):
        """ Initialize the pyff parameters. The list _view_parameters
        defines what to pass along to the view object.
        wait_style_fixed: Whether to calculate the presentation time
        of the next stimulus by the previously calculated waiting time
        or the actual real time at the end of the presentation period.
        fullscreen: Run the feedback in fullscreen/window.
        geometry: Upperleft x-pos, y-pos, width, height.
        bg_color: Background color.
        font_color_name: The color used for built-in text, like
        countdown or the center text.
        font_size: Size of the center text.
        fixation_cross_time: How long to display the built-in fixation
        cross when invoked.
        count_down_symbol_duration: How long to display each digit of
        the built-in countdown when invoked.
        count_down_start: First digit of the built-in countdown.
        print_frames: Whether to debug-print the number of frames
        rendered during each stimulus presentation.
        """
        self.wait_style_fixed = True
        self.fullscreen = False
        self.geometry = [100, 100, 640, 480]
        self.bg_color = 'grey'
        self.font_color_name = 'green'
        self.font_size = 150
        self.fixation_cross_time = 1.
        self.count_down_symbol_duration = 0.5
        self.count_down_start = 5
        self.print_frames = True
        self._view_parameters = ['fullscreen', 'geometry', 'bg_color',
                                 'font_color_name', 'font_size',
                                 'fixation_cross_time',
                                 'count_down_symbol_duration',
                                 'count_down_start']

    def __init_attributes(self):
        """ Setup internal attributes. """
        self._view = self._create_view()
        self.add_viewport = self._view.add_viewport
        self.add_stimuli = self._view.add_stimuli
        self.set_stimuli = self._view.set_stimuli
        self.set_iterator_semaphore(Flag())
        self.__setup_events()
        self.__setup_stim_factory()

    def _create_view(self):
        """ Instantiate the view class. Overload this for custom
        parameter specification. """
        return self._view_type()

    def set_iterator_semaphore(self, flag):
        """ Specify the object to be used as semaphore for iterators.
        See L{Switcherator} for more.
        """
        self._flag = flag
        self._iter = lambda it: Switcherator(flag, it, suspendable=True)
        self._view.set_iterator_semaphore(flag)
        
    def __setup_events(self):
        """ Set L{keyboard_input} to serve as keyboard handler. """
        handlers = [(pygame.KEYDOWN, self.keyboard_input)]
        self._view.set_event_handlers(handlers)

    def __setup_stim_factory(self):
        """ Create the factory for stimulus sequence handlers. """
        self._stimseq_fact = StimulusSequenceFactory(self._view, self._flag,
                                                     self.print_frames)

    def stimulus_sequence(self, prepare, presentation_time):
        """ Returns an object presenting a series of stimuli.
        @param prepare: This is the core connection between the sequence
        handler and user code. It can either be a generator (so
        presentation continues at a yield statement) or a function
        (continue upon 'return True'. 'return False' terminates the
        presentation sequence). The function should prepare the
        succeeding stimulus.
        @param presentation_time: The duration of presentation of a
        single stimulus, in seconds. Can also be a sequence of values.
        If the prepare function doesn't terminate when the sequence is
        exhausted, it is restarted.
        """
        return self._stimseq_fact.create(prepare, presentation_time,
                                         self.wait_style_fixed)

    def keyboard_input(self, event):
        """ Handle pygame events like keyboard input. """
        quit_keys = [pygame.K_q, pygame.K_ESCAPE]
        if event.key in quit_keys or event.type == pygame.QUIT:
            self.quit()

    def pre_mainloop(self):
        """ Reset the iterator semaphore and initialize the screen. """
        self._flag.reset()
        try:
            self._view.acquire()
            self.update_parameters()
        except pygame.error, e:
            self.logger.error(e)

    def on_interaction_event(self, data):
        if not self._running:
            self.update_parameters()

    def _mainloop(self):
        self._running = True
        self.run()
        self._running = False

    def on_pause(self):
        self._flag.toggle_suspension()

    def on_stop(self):
        self.quit()

    def update_parameters(self):
        """ Apply new parameters set from pyff. """
        params = dict([[p, getattr(self, p, None)] for p in
                        self._view_parameters])
        self._view.update_parameters(**params)

    def quit(self):
        self._flag.off()
        self._view.quit()

    def post_mainloop(self):
        self._view.close()
