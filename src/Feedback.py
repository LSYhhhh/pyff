# Feedback.py -
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

import logging
import threading


class Feedback(object):
    """
    Base class for all feedbacks.
    
    This class provides methods which are called by the FeedbackController on
    certain events. Override the methods as needed.
    
    As a bare minimum you should override the on_play method in your derived
    class to do anything useful.
    
    To get the data from interaction signals, you can use the "_data" variable
    in your feedback which will always hold the latest interaction signal.
    
    To get the data from the control signals, you can use the variable names 
    just as sent by the GUI but prefixed with a "_".
    
    This class provides the send_parallel method which you can use to send 
    arbitrary data to the parallel port. You don't have to override this 
    method in your feedback.
    """

    def __init__(self, pp, prefix="_"):
        """
        Initializes the feedback.
        
        You should not override this method, override on_init instead. If you
        must override this method, make sure to call Feedback.__init__(self, pp) 
        before anything else in your overridden __init__ method.
        """
     
        # Prefix for all variables coming from the GUI and the variable holding
        # the controll signal
        self.PREFIX = prefix
        self.__setattr__(self.PREFIX+"data", None)
        
        self.logger = logging.getLogger("Feedback")
        self.logger.debug("Loaded my logger.")
        self.__parallelPort = pp
 
    #
    # Internal routines not inteded for overwriting
    #
    def __on_control_event(self, data):
        """
        Store the data in the feedback and call on_control_event.
        
        You should not override this method, use on_control_event instead.
        """
        self.__setattr__(self.PREFIX+"data", data)
        self.on_control_event(data)
    
    def __on_interaction_event(self, data):
        """
        Store the variable-value pairs in the feedback and call 
        on_interaction_event.
        
        You should not override this method, use on_interaction_event instead.
        """
        data2 = dict()
        for key in data:
            # Oh man, das wird sich nochmal raechen!
            # Originalversion:
            #self.__setattr__(key, data[key])
            # Problem: Variablen wie feedback_opt.fb_port oder
            # fedback_opt(1).bla
            # Loesung: nehme nur den Namen nach dem letzten Punkt
            key2 = key.split(".")[-1]
            self.__setattr__(self.PREFIX+key2, data[key])
            data2[key2] = data[key]
        
        self.on_interaction_event(data2)
    
    def __on_init(self):
        """
        Calls on_init.
        
        You should not override this method, use on_init instead.
        """
        self.on_init()
    
    def __on_play(self):
        """
        Calls on_play.
        
        You should not override this method, use on_play instead.
        """
        self.on_play()
    
    def __on_pause(self):
        """
        Calls on_pause.
        
        You should not override this method, use on_pause instead.
        """
        self.on_pause()
    
    def __on_quit(self):
        """
        Calls on_quit.
        
        You should not override this method, use on_quit instead.
        """
        self.on_quit()


    #
    # Empty routines intended to be overwritten by derived classes
    #
    def on_init(self):
        """
        This method is called right after the feedback object was loaded by the
        FeedbackController.
        
        Override this method to initialize everything you need before the 
        feedback starts.
        """
        self.logger.warn("on_init not implemented yet!")
        
    
    def on_play(self):
        """
        This method is called by the FeedbackController when it received a 
        "Play" event via interaction signal.
        
        Override this method to actually start your feedback.
        """
        self.logger.warn("on_play not implemented yet!")

    
    def on_pause(self):
        """
        This method is called by the FeedbackController when it received a
        "Pause" event via interaction signal.
        
        Override this method to pause your feedback.
        """
        self.logger.warn("on_pause not implemented yet!")


    def on_quit(self):
        """
        This Method is called just before the FeedbackController will destroy 
        the feedback object. The FeedbackController will not destroy the 
        feedback object until this method has returned.
        
        Override this method to cleanup everything as needed or save information
        before the object gets destroyed.
        """
        self.logger.warn("on_quit not implemented yet!")

    
    def on_interaction_event(self, data):
        """
        This method is called after the FeedbackController received a 
        interaction signal. The FeedbackController parses the signal, extracts
        the variable-value pairs, stores them as object-variables in your
        feedback and calls this method.
        
        If the FeedbackController detects a "play", "pause" or "quit"
        signal, it calls the appropriate on_-method after this method has
        returned.
        
        If the FeedbackController detects an "init" signal, it calls "on_init"
        before "on_interaction_event"!
        
        Override this method if you want to react on interaction events.
        """
        self.logger.warn("on_interaction_event not implemented yet!")


    def on_control_event(self, data):
        """
        This method is called after the FeedbackController received a control
        signal. The FeedbackController parses the signal, extracts the values
        stores the resulting tuple in the object-variable "data" and calls this
        method.
        
        Override this method if you want to react on control events.
        """
        self.logger.warn("on_control_event not implemented yet!")


    #
    # Common routines for all feedbacks
    #
    def send_parallel(self, data, reset=True):
        """Sends the data to the parallel port."""
        if self.__parallelPort:
            self.__parallelPort.setData(data)
            if reset:
                t = threading.Timer(0.01, self.send_parallel, (0x0, False))
                t.start()
