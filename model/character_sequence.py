""" {{{ Copyright (c) 2010 Torsten Schmits

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this
program; if not, see <http://www.gnu.org/licenses/>.

}}} """

from random import Random, choice
from copy import copy
from itertools import chain
import logging

from AlphaBurst.util.list import slices
from AlphaBurst.util.color import color
from AlphaBurst.sequence_algorithm import RSVP

class CharacterSequence(list):
    def __init__(self, alphabet, redundance, burst_count=3, shuffle=False,
                 alt_color=False):
        list.__init__(self, [])
        self._alphabet = list(alphabet)
        self._redundance = redundance
        self._burst_count = burst_count
        self._shuffle = shuffle
        self._alt_color = alt_color
        self.__init_attributes()
        self.reset()

    def __init_attributes(self):
        self._random = Random('BBCI')
        self._burst_signi_len = len(self._alphabet) / self._burst_count
        self._redundance_len = 6
        self._burst_len = self._burst_signi_len + self._redundance_len
        self.done = False

    def reset(self):
        self._current_index = 0
        self.done = False
        self._sequence = copy(self._alphabet)
        if self._shuffle:
            self._random.shuffle(self._sequence)
        self._create_burst_sequence()
        self._zip_colors()

    def _create_burst_sequence(self):
        """ Insert redundant symbols into the character sequence. """
        make_burst = lambda b: self._new_redundance + b
        bursts = map(make_burst, slices(self._sequence, self._burst_signi_len))
        self.burst_sequence = list(chain(*bursts))

    def _zip_colors(self):
        """ Create a list of alternating colors and zip them to the
        burst sequence, keep as a list of burst lists.
        """
        nsym = len(self.burst_sequence)
        self._colors = map(self._positional_color, xrange(nsym))
        zipped = zip(self.burst_sequence, self._colors)
        self[:] = slices(zipped, self._burst_len)
        self._bursts = self

    def _positional_color(self, i):
        if self._alt_color:
            return color(i)

    @property
    def _new_redundance(self):
        return self._random.sample(self._redundance, self._redundance_len)

    @property
    def next_burst(self):
        burst = self._bursts[self._current_index]
        self.done = self._current_index + 1 == len(self._bursts)
        if not self.done:
            self._current_index += 1
        return burst

    def get_color(self, symbol):
        try:
            i = self.burst_sequence.index(symbol)
            return self._colors[i]
        except ValueError:
            return None

class CharacterSequenceFactory(object):
    def __init__(self, color_groups, redundance, alt_color, target):
        self._color_groups = color_groups
        self._redundance = redundance
        self._alt_color = alt_color
        self._target = target
        self._color_offset = (i for i, g in enumerate(self._color_groups) if
                              self._target in g).next()
        self._rsvp = RSVP(self._color_groups)

    def sequence(self, alphabet, shuffle=False):
        return CharacterSequence(alphabet, self._redundance, shuffle=shuffle,
                                 alt_color=self._alt_color)

    def extra_sequence(self, target_count):
        """ Create one sequence with additional targets at random
        positions, preserving the color groups.
        """
        bursts = self._rsvp.trial(2, self._alt_color) 
        seq = sum(bursts[:3], [])
        indexes = range(0, len(seq), 3)
        random_index = lambda: self._color_offset + choice(indexes)
        while len(filter(lambda l: l == self._target, seq)) < target_count:
            seq[random_index()] = self._target
        return self.sequence(seq)

    def sequences(self, count, pre=[], post=[]):
        main_bursts = self._rsvp.trial(count, self._alt_color) 
        main_seqs = [sum(main_bursts[i:i + 3], []) for i in
                     xrange(0, len(main_bursts), 3)]
        extra = self.extra_sequence
        sequences = map(extra, pre) + map(self.sequence, main_seqs) + map(extra,
                                                                         post)
        return Sequences(sequences)

class Sequences(list):
    def __init__(self, sequences):
        list.__init__(self, sequences)
        self._seq_iter = iter(self)
        self.done = False
        self.next()

    @property
    def next_burst(self):
        return self.current_sequence.next_burst

    @property
    def sequence_done(self):
        return self.current_sequence.done

    def next(self):
        try:
            self.current_sequence = self._seq_iter.next()
        except StopIteration:
            self.done = True

    def occurences(self, symbol):
        return sum(len(filter(lambda s: s == symbol, seq.burst_sequence)) for
                   seq in self)
