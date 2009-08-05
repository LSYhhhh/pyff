# feedbackprocesscontroller.py -
# Copyright (C) 2009  Bastian Venthur
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


from threading import Thread
import logging
import asyncore

from processing import Process, Event

from lib.PluginController import PluginController
import ipc


class FeedbackProcess(Process):
    def __init__(self, feedbackClass, ipcReady):
        Process.__init__(self)
        self.feedbackClass = feedbackClass
        self.ipcReady = ipcReady

    def run(self):
        feedback = self.feedbackClass()
        feedback.logger.debug("Initialized Feedback.")
        # Start the Feedbacks IPC Channel
        asyncore.socket_map.clear()
        conn = ipc.get_feedbackcontroller_connection()
        ipc.FeedbackIPCChannel(conn, feedback)
        feedback.logger.debug("Starting IPC loop.")
        fbipcthread = Thread(target=ipc.ipcloop)
        fbipcthread.start()
        self.ipcReady.set()
        # Start the Feedbacks Mainloop
        try:
            feedback.on_init()
            feedback._playloop()
        finally:
            feedback.logger.debug("Closing IPC socket.")
            conn.close()


class FeedbackProcessController(object):
    """Takes care of starting and stopping of Feedback Processes."""
    
    def __init__(self, plugindirs, baseclass, timeout):
        """Initialize the Feedback Process Controller."""
        # Where are we: 
        # Proc/Thread: FB/??
        self.logger = logging.getLogger("FeedbackProcessController")
        self.currentProc = None
        self.timeout = timeout
        self.pluginController = PluginController(plugindirs, baseclass)
        self.pluginController.find_plugins()
        
    
    def start_feedback(self, name):
        """Starts the given Feedback in a new process."""
        # Where are we: 
        # Proc/Thread: FC/??
        self.logger.debug("Starting new Process...",)
        if self.currentProc:
            self.logger.warning("Trying to start feedback but another one is still running. Killing the old one now and proceed.")
            self.stop_feedback()
        try:
            feedbackClass = self.pluginController.load_plugin(name)
        except ImportError:
            # TODO: Hmm anything else we can do?
            raise
        ipcReady = Event()
        self.currentProc = FeedbackProcess(feedbackClass, ipcReady)
        self.currentProc.start()
        # Wait until the network from the Process is ready, this is neccessairy
        # since spawning a new process under Windows is very slow.
        self.logger.debug("Waiting for IPC channel to become ready...")
        ipcReady.wait()
        self.logger.debug("IPC channel ready.")
        self.logger.debug("Done starting process.")

    
    def stop_feedback(self):
        """Stops the current Process.
        
        First it tries to join the process with the given timeout, if that fails
        it terminates the process the hard way.
        """
        # Where are we: 
        # Proc/Thread: FC/??
        self.logger.debug("Stopping process...",)
        if not self.currentProc:
            self.logger.debug("No process running, nothing to do.")
            return
        
        self.currentProc.join(self.timeout)
        if self.currentProc.isAlive():
            self.logger.warning("Process still alive, terminating it...",)
            self.currentProc.terminate()
            self.currentProc.join(self.timeout)
            if self.currentProc.isAlive():
                self.logger.error("Process still alive, giving up.")
        
        del(self.currentProc)
        self.currentProc = None
        self.logger.debug("Done stopping process.")
        
    
    def get_feedbacks(self):
        """Return a list of available Feedbacks."""
        # Where are we: 
        # Proc/Thread: FC/??
        return self.pluginController.availablePlugins.keys()

