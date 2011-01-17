__copyright__ = """ Copyright (c) 2011 Torsten Schmits

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

import string

from lib.speller.trial import *
from lib.speller.input import *
from lib.speller.experiment import *

class Speller(object):
    __stimulus = None
    __sequences = None

    def __init__(self):
        self.__init_attributes()

    def __init_attributes(self):
        self._trial_types = ['Calibration', 'FreeSpelling', 'CopySpelling']
        # 1: Calibration 2: FreeSpelling 3: CopySpelling
        self.trial_type = 3
        self.phrases = ['BBCI_MATRIX']
        self.symbols = string.ascii_uppercase + '_,.<'
        self.delete_symbol = '<'
        self.inter_trial = .1
        self.inter_phrase = .1
        # display countdown before each letter
        self.trial_countdown = False
        # display countdown before each phrase
        self.phrase_countdown = True
        self.countdown_symbol_duration = .1
        self.countdown_start = 1
        # allow classifier input to be simulated by keyboard
        self.allow_keyboard_input = True

    def update_parameters(self):
        super(Speller, self).update_parameters()
        self._trial_name = self._trial_types[self.trial_type - 1]
        self.setup()

    @classmethod
    def stimulus(self, f):
        self.__stimulus = f
        return f

    @classmethod
    def sequences(self, f):
        self.__sequences = f
        return f

    def setup(self):
        self._setup_trial()
        self._setup_input_handler()
        self._setup_experiment()

    def _setup_trial(self):
        trial_type = self._trial_name + 'Trial'
        self._trial = eval(trial_type)(self._view, self._trigger, self._iter,
                                       self)
        if self.__stimulus:
            self._trial._sequence = getattr(self, self.__stimulus.__name__)

    def _setup_input_handler(self):
        input_handler_type = self._trial_name + 'InputHandler'
        self._input_handler = eval(input_handler_type)(self)

    def _setup_experiment(self):
        experiment_type = self._trial_name + 'Experiment'
        self._experiment = eval(experiment_type)(self._view, self._trial,
                                                 self.phrases,
                                                 self._input_handler,
                                                 self._flag, self._iter,
                                                 self)
        if self.__sequences:
            self._experiment._sequences = getattr(self,
                                                  self.__sequences.__name__)

    def keyboard_input(self, event):
        if self._trial.asking:
            self._input_handler.keyboard(event)
        super(Speller, self).keyboard_input(event)

    def current_target(self):
        return self._trial.current_target

    def run(self):
        self._experiment.run()

    def on_control_event(self, data):
        """ Classifier input. """
        cls = data.get('cl_output', None)
        if cls is not None:
            self._input_handler.eeg_select(cls)
