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

from time import sleep
import datetime, collections, logging, itertools

import pygame

from lib.vision_egg.util.frame_counter import FrameCounter

def time():
    """ Return microsecond-accurate time since last midnight. 
    Workaround for time() having only 10ms accuracy when VE is running.
    """
    n = datetime.datetime.now()
    return 60. * (60 * n.hour + n.minute) + n.second + n.microsecond / 1000000.

class StimulusPainter(object):
    """ Painter for a series of stimuli. """
    def __init__(self, prepare, wait, view, flag, wait_style_fixed=False,
                 print_frames=False, suspendable=True, pre_stimulus=None):
        self._prepare_func = prepare
        self._wait_times = itertools.cycle(wait)
        self._view = view
        self._flag = flag
        self._wait_style_fixed = wait_style_fixed
        self._print_frames = print_frames
        self._suspendable = suspendable
        self._pre_stimulus = pre_stimulus
        self._wait_time = 0.1
        self._logger = logging.getLogger('StimulusPainter')
        self._frame_counter = FrameCounter(self._flag)
        self._suspended_time = 0.

    def run(self):
        if self._print_frames:
            self._frame_counter.start()
        if self._prepare():
            self._last_start = time()
            self._frame_counter.lock()
            self._present()
            while self._prepare():
                self._wait()
                self._present()
            self._wait()

    def _wait(self):
        next_wait_time = self._next_wait_time + self._suspended_time
        self._suspended_time = 0.
        wait_time = self._last_start - time() + next_wait_time
        try:
            if wait_time > 0:
                sleep(wait_time)
        except IOError, e:
            self._logger.error('Encountered "%s" with wait_time of %s'
                               % (e, wait_time))
        if self._wait_style_fixed:
            self._last_start += next_wait_time
        else:
            self._last_start = time()
        if self._print_frames:
            self._logger.debug('Frames after waiting: %d' %
                               self._frame_counter.last_interval)

    def _prepare(self):
        if self._flag:
            if self._suspendable and self._flag.suspended:
                suspend_start = time()
                self._flag.wait()
                self._suspended_time = time() - suspend_start
            return self._do_prepare()

    def _present(self):
        if self._print_frames:
            self._logger.debug('Frames before stimulus change: %d' %
                               self._frame_counter.last_interval)
            self._frame_counter.lock()
        if self._pre_stimulus is not None:
            self._pre_stimulus()
        self._view.update()

    @property
    def _next_wait_time(self):
        return self._wait_times.next()

class StimulusSequence(StimulusPainter):
    def _do_prepare(self):
        return self._prepare_func()

class StimulusIterator(StimulusPainter):
    """ Painter using an iterator. """
    def _do_prepare(self):
        try:
            self._prepare_func.next()
            return True
        except StopIteration:
            return False

class StimulusSequenceFactory(object):
    """ This class instantiates StimulusPainter in create().
    Depending on whether the supplied prepare object is a function or a
    generator, StimulusSequence or StimulusIterator are used,
    respectively.
    """
    def __init__(self, view, flag, print_frames=False):
        self._view = view
        self._flag = flag
        self._print_frames = print_frames

    def create(self, prepare, presentation_times, wait_style_fixed,
               suspendable=True, pre_stimulus=None):
        """ Create a StimulusPainter using the preparation object
        prepare, with given presentation times and wait style.
        If suspendable is True, the sequence halts when on_pause is
        pressed.
        Global parameters from pyff are used as given in __init__.
        """
        if not isinstance(presentation_times, collections.Sequence):
            presentation_times = [presentation_times]
        typ = StimulusIterator if hasattr(prepare, '__iter__') else \
               StimulusSequence
        return typ(prepare, presentation_times, self._view, self._flag,
                   wait_style_fixed=wait_style_fixed,
                   print_frames=self._print_frames, suspendable=suspendable,
                   pre_stimulus=pre_stimulus)
