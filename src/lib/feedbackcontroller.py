# feedbackcontroller.py -
# Copyright (C) 2007-2009  Bastian Venthur
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


import socket
import logging
import traceback
import sys
import asyncore

from lib import bcinetwork
from lib import bcixml
from FeedbackBase.Feedback import Feedback
from lib.feedbackprocesscontroller import FeedbackProcessController
import ipc


class FeedbackController(object):
    def __init__(self, plugin=None, fbpath=None, port=None):
        # Setup my stuff:
        self.logger = logging.getLogger("FeedbackController")
        self.encoder = bcixml.XmlEncoder()
        self.decoder = bcixml.XmlDecoder()
        # Set up the socket
        self.ipcchannel = ipc.IPCConnectionHandler(self)
        self.udpconnectionhandler = UDPDispatcher(self)
        # Windows only, set the parallel port port
        self.ppport = port
        self.fbplugin = plugin
        fbdirs = ["Feedbacks"]
        if fbpath:
            fbdirs.append(fbpath)
        self.fbProcCtrl = FeedbackProcessController(fbdirs, Feedback, 1)
        self.fc_data = {}


    def start(self):
        """Start the Feedback Controller's activities."""
        self.logger.debug("Started mainloop.")
        ipc.ipcloop()
        self.logger.debug("Left mainloop.")
        
    
    def stop(self):
        """Stop the Feedback Controller's activities."""
        self.fbProcCtrl.stop_feedback()
        asyncore.close_all()

    
    def handle_signal(self, signal):
        # check our signal if it contains anything useful, if not drop it and
        # print a warning
        try:
            if signal.type == bcixml.REPLY_SIGNAL:
                self.send_to_peer(signal)
            elif signal.type == bcixml.CONTROL_SIGNAL:
                self._handle_cs(signal)
            elif signal.type == bcixml.INTERACTION_SIGNAL:
                self._handle_is(signal)
            elif signal.type == bcixml.FC_SIGNAL:
                self._handle_fcs(signal)
            else:
                self.logger.warning("Unknown signal type, ignoring it. (%s)" % str(signal.type))
        except:
            self.logger.error("Handling is or cs caused an exception.")
            self.logger.error(traceback.format_exc())


    def _handle_fcs(self, signal):
        # We assume, that the signal only contains variables which are to set
        # in the Feedback Controller
        self.fc_data = signal.data.copy()

    def _handle_cs(self, signal):
        # We don't care about control signals, send it to the feedback
        self.send_to_feedback(signal)

    
    def _handle_is(self, signal):
        self.logger.info("Got interaction signal: %s" % str(signal))
        cmd = signal.commands[0] if len(signal.commands) > 0 else None
        
        # A few commands need to be handled by the Feedback Controller, the
        # rest goes to the Feedback
        if cmd == bcixml.CMD_GET_FEEDBACKS:
            reply = bcixml.BciSignal({"feedbacks" : self.fbProcCtrl.get_feedbacks()}, 
                                     None, bcixml.REPLY_SIGNAL)
            reply.peeraddr = signal.peeraddr
            self.send_to_peer(reply)
            return
        elif cmd == bcixml.CMD_GET_VARIABLES:
            # Put it in the pipe and hope that the reply will appear on our end.
            self.send_to_feedback(signal)
            return

        if cmd == bcixml.CMD_QUIT:
            self.send_to_feedback(signal)
            self.ipcchannel.close_channel()
            self.fbProcCtrl.stop_feedback()
        elif cmd == bcixml.CMD_SEND_INIT:
            name = signal.data["_feedback"]
            self.fbProcCtrl.start_feedback(name, port=self.ppport, fbplugin=self.fbplugin)
        else:
            self.send_to_feedback(signal)
    

    def send_to_feedback(self, signal):
        """Send data to the feedback."""
        try:
            self.ipcchannel.send_message(signal)
        except:
            self.logger.warning("Couldn't send data to Feedback.")
            self.logger.warning(traceback.format_exc())

        
    def send_to_peer(self, signal):
        self.udpconnectionhandler.send_signal(signal)


class UDPDispatcher(asyncore.dispatcher):
    
    def __init__(self, fc):
        asyncore.dispatcher.__init__(self)
        self.fc = fc
        self.decoder = bcixml.XmlDecoder()
        self.encoder = bcixml.XmlEncoder()
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind((bcinetwork.LOCALHOST, bcinetwork.FC_PORT))

    def send_signal(self, signal):
        data = self.encoder.encode_packet(signal)
        self.socket.sendto(data, (signal.peeraddr[0], bcinetwork.GUI_PORT))

    def handle_connect(self): pass
    
    def writable(self):
        return False
        
    def handle_read(self):
        try:
            data, address = self.recvfrom(bcinetwork.BUFFER_SIZE)
            signal = self.decoder.decode_packet(data)
            signal.peeraddr = address
            self.fc.handle_signal(signal)
        except:
            self.fc.logger.warning(traceback.format_exc())
        