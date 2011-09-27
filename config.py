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

import string

class Config(object):
    def init(self):
        self.symbol_duration = 0.05
        self.sequences_per_trial = 2
        self.font_color = 'orangered'
        self.alternating_colors = True
        self.font_size = 150
        self.bg_color = 'grey'
        self.screen_width = 400
        self.screen_height = 400
        self.fullscreen = False
        self.current_word_index = 0
        self.current_letter_index = 0
        self.sound = False
        self.words = ['WINKT', 'FJORD', 'HYBRID', 'LUXUS', 'SPHINX', 'QUARZ',
                      'VODKA', 'YACHT', 'GEBOT', 'MEMME']
        self.meaningless = '*+&%?;'
        self.target_index = 0
        self.alphabet = string.ascii_uppercase + '.,:<'
        self.burst_duration = 1.
        self.mode = 'ask'
        self._view_parameters = ['symbol_duration', 'bg_color', 'font_color',
                                 'present_word_time', 'present_target_time',
                                 'fixation_cross_time', 'count_down_start',
                                 'count_down_symbol_duration', 'color_groups',
                                'alternating_colors', 'font_size']
        self.key_yes = 'j'
        self.key_no = 'k'
        self.inter_burst = .1
        self.inter_sequence = .5
        self.inter_block = 1.
        self.inter_trial = 1.
        self.present_word_time = 2.
        self.fixation_cross_time = 1.
        self.present_target_time = 1.
        self.custom_pre_sequences = [10, 5]
        self.custom_post_sequences = [3]
        self.trial_type = 1
        self.count_down_start = 5
        self.count_down_symbol_duration = .5
        self.max_diff = 10
        self.color_groups = ["ABCDEFGHIJ", "KLMNOPQRST", "UVWXYZ.,:<"]
