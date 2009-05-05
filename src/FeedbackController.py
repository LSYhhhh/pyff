#!/usr/bin/env python
# coding: utf8

# FeedbackController.py -
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
import asyncore
import threading
import logging
import sys
import os
import traceback
from optparse import OptionParser
from ctypes import windll
try:
    import parallel
except ImportError:
    print "Unable to import parallel module, have you pyparallel installed?"

from lib import bcinetwork
from lib import bcixml
from lib import PluginController
from FeedbackBase.Feedback import Feedback


class FeedbackController(object):
    def __init__(self, plugin=None, fbpath=None, port=None):
        # Setup my stuff:
        self.logger = logging.getLogger("FeedbackController")
        self.encoder = bcixml.XmlEncoder()
        self.decoder = bcixml.XmlDecoder()
        self.port = port
        # Setup the parallel port
        
        
        self.pp = None
        self.logger.debug("Platform: " + sys.platform)
        if sys.platform == 'win32':        
            try:
                self.pp = windll.inpout32
                
            except:
                self.logger.warning("Could not load inpout32.dll. Please make sure it is located in the system32 directory")        
        else:
            try:
                self.pp = parallel.Parallel()
                
            except:
                self.logger.warning("Unable to open parallel port!")
                
        
        self.feedback = Feedback(self.pp, port)
        self.playEvent = threading.Event()
        if plugin:
            self.logger.debug("Loading plugin %s" % str(plugin))
            try:
                self.inject(plugin)
            except:
                self.logger.error(str(traceback.format_exc()))
        if fbpath:
            self.logger.debug("Testing additional Feedback path.")
            if os.path.exists(fbpath):
                self.logger.debug("Additional Feedback path exists, adding it to path.")
                fbpath = os.path.normpath(fbpath)
                sys.path.append(fbpath)
            else:
                self.logger.warning("Additional Feedback path does not exist!")
        fbPath = [os.path.abspath("./Feedbacks")]
        if fbpath: fbPath.append(os.path.abspath(fbpath)) 
        self.pluginController = PluginController.PluginController(fbPath, Feedback)
        self.pluginController.find_plugins()
        self.feedbacks = self.pluginController.availablePlugins.keys()
        self.logger.info("Registered the following Feedbacks:")
        for i in self.feedbacks:
            self.logger.info("\t%s" % str(i))
        
        self.fc_data = {}
        
        
#
# Feedback Controller Plugin-Methods
#    
    def pre_init(self): pass
    def post_init(self): pass
    def pre_play(self): pass
    def post_play(self): pass
    def pre_pause(self): pass
    def post_pause(self): pass
    def pre_stop(self): pass
    def post_stop(self): pass
    def pre_quit(self): pass
    def post_quit(self): pass
#
# /Feedback Controller Plugin-Methods
#    

    SUPPORTED_PLUGIN_METHODS = ["pre_init", "post_init", 
                                "pre_play", "post_play", 
                                "pre_pause", "post_pause",
                                "pre_stop", "post_stop",
                                "pre_quit", "post_quit"]
    
    def inject(self, module):
        """Inject methods from module to Feedback Controller."""
        
        try:
            m = __import__(module, fromlist=[None])
        except ImportError:
            self.logger.info("Unable to import module %s, aborting injection." % str(module))
        else:
            for meth in FeedbackController.SUPPORTED_PLUGIN_METHODS:
                if hasattr(m, meth) and callable(getattr(m, meth)):
                    setattr(FeedbackController, meth, getattr(m, meth))
                    self.logger.info("Sucessfully injected: %s" % meth)
                else:
                    self.logger.debug("Unable to inject %s" % meth)
                    has = hasattr(m, meth)
                    call = False
                    if has:
                        call = callable(getattr(m, meth))
                    self.logger.debug("hassattr/callable: %s/%s" % (str(has), str(call)))
                    


    def start(self):
        """Start the Feedback Controllers activities."""
        
        # Listen on the network in a second thread
        Dispatcher(bcinetwork.FC_PORT, self)
        self.networkThread = threading.Thread(target=asyncore.loop, args=())
        self.networkThread.start()
        
        # start my main loop
        self.logger.debug("Started main loop.")
        self.main_loop()
        self.logger.debug("Left main loop.")

    
    def on_signal(self, address, datagram):
        signal = None
        try:
            signal = self.decoder.decode_packet(datagram)
            signal.peeraddr = address
        except bcixml.DecodingError, e:
            # ok, somehow the parsing failed, just drop the packet and print a
            # warning
            self.logger.warning("Parsing of signal failed, ignoring it. (%s)" % str(e))
            return
        # check our signal if it contains anything useful, if not drop it and
        # print a warning
        try:
            if signal.type == bcixml.CONTROL_SIGNAL:
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

        
    def main_loop(self):
        while True:
            # Block until we received a play signal
            self.logger.debug("Waiting for play-event.")
            self.playEvent.wait()
            self.logger.debug("Got play-event, starting Feedback's on_play()")
            self.playEvent.clear()
            # run the Feedbacks on_play in our thread
            try:
                self.feedback._on_play()
            except:
                self.logger.error("Feedbacks on_play threw an exception:")
                self.logger.error(traceback.format_exc())
            #self.call_method_safely(self.feedback._Feedback__on_play())
            self.logger.debug("Feedback's on_play terminated.")


    def _handle_fcs(self, signal):
        # We assume, that the signal only contains variables which are to set
        # in the Feedback Controller
        self.fc_data = signal.data.copy()
        

    def _handle_cs(self, signal):
        self.feedback._on_control_event(signal.data)

    
    def _handle_is(self, signal):
        self.logger.info("Got interaction signal: %s" % str(signal))
        cmd = None
        if len(signal.commands) > 0:
            cmd = signal.commands[0]
        # check if this signal is for the FC only (and not for the feedback)
        if cmd == bcixml.CMD_GET_FEEDBACKS:
            ip, port = signal.peeraddr[0], bcinetwork.GUI_PORT
            bcinetw = bcinetwork.BciNetwork(ip, port)
            answer = bcixml.BciSignal({"feedbacks" : self.feedbacks}, None, bcixml.INTERACTION_SIGNAL)
            self.logger.debug("Sending %s to %s:%s." % (str(answer), str(ip), str(port)))
            bcinetw.send_signal(answer)
            return
        elif cmd == bcixml.CMD_GET_VARIABLES:
            ip, port = signal.peeraddr[0], bcinetwork.GUI_PORT
            bcinetw = bcinetwork.BciNetwork(ip, port)
            answer = bcixml.BciSignal({"variables" : self.feedback.__dict__}, None, bcixml.INTERACTION_SIGNAL)
            self.logger.debug("Sending %s to %s:%s." % (str(answer), str(ip), str(port)))
            bcinetw.send_signal(answer)
            return
        
        self.feedback._on_interaction_event(signal.data)
        if cmd == bcixml.CMD_PLAY:
            self.logger.info("Received PLAY signal")
            self.pre_play()
            self.playEvent.set()
            self.post_play()
            #self.feedback._Feedback__on_play()
        elif cmd == bcixml.CMD_PAUSE:
            self.logger.info("Received PAUSE signal")
            self.pre_pause()
            self.feedback._on_pause()
            self.post_pause()
        elif cmd == bcixml.CMD_STOP:
            self.logger.info("Received STOP signal")
            self.pre_stop()
            self.feedback._on_stop()
            self.post_stop()
        elif cmd == bcixml.CMD_QUIT:
            self.logger.info("Received QUIT signal")
            self.pre_quit()
            self.feedback._on_quit()
            # Load the default dummy Feedback
            self.feedback = Feedback(self.pp, self.port)
            self.post_quit()
        elif cmd == bcixml.CMD_SEND_INIT:
            self.logger.info("Received SEND_INIT signal")
            # Working with old Feedback!
            self.feedback._on_quit()
            name = getattr(self.feedback, "_feedback")
            try:
                self.logger.debug("Trying to load feedback: %s" % str(name))
                self.feedback = self.pluginController.load_plugin(name)(self.pp, self.port)
            except:
                self.logger.error("Unable to load feedback: %s" % str(name))
                self.logger.error(traceback.format_exc())
                self.feedback = Feedback(self.pp, self.port)
            # Proably a new one!
            self.pre_init()
            self.feedback._on_init()
            self.post_init()
            self.feedback._on_interaction_event(signal.data)
        else:
            self.logger.info("Received generic interaction signal")


class Dispatcher(asyncore.dispatcher):
    def __init__(self, port, feedbackController):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(("", port))
        #self.handle_read = self.handle_read
        self.feedbackController = feedbackController
        
    def writable(self):
        return False

    def handle_connect(self):
        pass
        
    def handle_read(self):
        datagram = self.recv(bcinetwork.BUFFER_SIZE)
        self.feedbackController.on_signal(self.addr, datagram)    


def start_fc(plugin=None, fbpath=None, port=None):
    fc = FeedbackController(plugin, fbpath, port)
    fc.start()

def stop_fc():
    pass


def main():
    
    # Get Options
    description = """Feedback Controller"""
    usage = "%prog [Options]"
    version = """
Copyright (C) 2007-2008 Bastian Venthur <venthur at cs tu-berlin de>

Homepage: http://bbci.de/pyff

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
    parser = OptionParser(usage=usage, version=version, description=description)
    parser.add_option('-l', '--loglevel', type='choice', choices=['critical',
        'error', 'warning', 'info', 'debug', 'notset'], dest='loglevel',
        help='Which loglevel to use for everything but the Feedbacks. Valid loglevels are: critical, error, warning, info, debug and notset. [default: warning]',
        metavar='LEVEL')
    parser.add_option('--fb-loglevel', type='choice', choices=['critical',
        'error', 'warning', 'info', 'debug', 'notset'], dest='fbloglevel',
        help='Which loglevel to use for the Feedbacks. Valid loglevels are: critical, error, warning, info, debug and notset. [default: warning]',
        metavar='LEVEL')
    parser.add_option('-p', '--plugin', dest='plugin',
                      help="Optional Plugin, the Feedback Controller should load.",
                      metavar="MODULE")
    parser.add_option('-a', '--additional-feedback-path', dest='fbpath',
                      help="Additional path to search for Feedbacks.",
                      metavar="DIR")
    parser.add_option('--port', dest='port',
                      help="Set the Parallel port address to use. Windows only. Should be in Hex (eg: 0x378)",
                      metavar="PORTNUM")


    options, args = parser.parse_args()

    # Initialize logging
    str2loglevel = {'critical' : logging.CRITICAL,
                    'error'    : logging.ERROR,
                    'warning'  : logging.WARNING,
                    'info'     : logging.INFO,
                    'debug'    : logging.DEBUG,
                    'notset'   : logging.NOTSET}
    
    loglevel = str2loglevel.get(options.loglevel, logging.WARNING)
    fbloglevel = str2loglevel.get(options.fbloglevel, logging.WARNING)

    logging.basicConfig(level=loglevel, format='[%(threadName)-10s] %(name)-25s: %(levelname)-8s %(message)s')
    logging.info('Logger initialized with level %s.' % options.loglevel)
    logging.getLogger("FB").setLevel(fbloglevel)
    
    # get the rest
    plugin = options.plugin
    fbpath = options.fbpath
    port = None
    if options.port != None:
        port = int(options.port, 16)

    
    try:
        start_fc(plugin, fbpath, port)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Caught keyboard interrupt or system exit; quitting")
        stop_fc()
        sys.exit()
    


if __name__ == '__main__':
    main()
