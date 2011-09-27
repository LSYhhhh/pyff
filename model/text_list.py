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

from copy import copy

from VisionEgg.Text import Text

class TextList(list):
    """ TODO inherit Viewport

    """
    def __init__(self, position):
        list.__init__([])
        self._position = position

    def add(self, text, size):
        new = Text(font_size=size, text=text, anchor='bottom')
        self.append(new)
        self.rearrange()

    def rearrange(self):
        height = self._max_height # TODO check against screen size?
        width = self._width
        pos = list(self._position)
        pos[0] -= width / 2.
        for t in self:
            s = t.parameters.size
            w = s[0] / 2.
            pos[0] += w
            t.set(position=copy(pos))
            pos[0] += w

    @property
    def _max_height(self):
        heights = [t.parameters.size[1] for t in self]
        return max([0] + heights)

    @property
    def _width(self):
        return reduce(lambda l, t: l + t.parameters.size[0], self, 0)

    def clear(self):
        del self[:]
