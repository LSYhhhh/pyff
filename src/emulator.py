#!/usr/bin/env python

# emulater.py - a simple BCI system emulator
# Copyright (C) 2007-2008  Bastian Venthur
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""A BCI-system emulator."""


import bcinetwork
from bcinetwork import BciNetwork
import bcixml
from bcixml import BciSignal

import cmd
import threading
import math
import time


class Emulator(cmd.Cmd):
    
    prompt = "> "
    intro = "Welcome to the BCI emulator. Type help to see a list of available commands."
    
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.stopping = True

    def do_quit(self, line):
        """Quit the Emulator."""
        return True
    
    def postloop(self):
        print

    def do_generate_cs(self, line):
        """Generates a control signal and sends it to the Feedback Controller."""
        self.net = BciNetwork("localhost", bcinetwork.FC_PORT)
        self.signal = BciSignal(None, None, bcixml.CONTROL_SIGNAL)
        self.stopping = False
        self.t = threading.Thread(target=self._cs_loop)
        self.t.start()
        print "Enter: stop_cs to stop the signal."
        
    def _cs_loop(self):
        c = 0
        while not self.stopping:
            time.sleep(0.04)
            c += 1
            sample1 = math.sin(c)
            sample2 = math.sin(c/90.0)
            sample3 = math.sin(c/180.0)
            #self.signal.data = {"data" : [sample1, sample2, sample3]}
            self.signal.data = {"cl_output" : sample1}
            self.net.send_signal(self.signal)

    def do_stop_cs(self, line):
        """Stops the loop which sends data to the Feedback Controller."""
        self.stopping = True
        self.t.join()
        
    def do_status(self, line):
        """Get the status of the emulator."""
        for var, val in self.__dict__.iteritems():
            print str(var), str(val)
        
        

if __name__ == "__main__":
    Emulator().cmdloop()
