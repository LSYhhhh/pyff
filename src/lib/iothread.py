
from threading import Thread

class IOThread(Thread):
    """A thread that reads and writes a pipe.
    
    This thread reads and writes the given end of a pipe. You should not use
    this class directly but derive it and overwrite it's 
    
      process_object(obj)
      
    method to do something useful with the data the thread received from the
    pipe.
    
    Before you join() this thread you must call stop() to quit the internal
    loop which polls the pipe.
    """
    
    
    def __init__(self, pipeEnd, timeout=1):
        """
        Initialize the IOThread.
        
        @param pipeEnd: the end of the pipe where the thread should read/write. 
        @param timeout: seconds to wait if there is something to read. 
        """
        Thread.__init__(self)
        self.pipeEnd = pipeEnd
        self.timeout = timeout
        self.stopping = False
        

    def stop(self):
        """Stop the thread.
        
        This method must be called before join()-ing it.
        """
        self.stopping = True
        

    def run(self):
        """The thread's activity."""
        while not self.stopping:
            try:
                if self.pipeEnd.poll(self.timeout):
                    obj = self.pipeEnd.recv()
                    self.process_object(obj)
            except EOFError:
                # Nothing left to receive or other End was closed
                pass
    
    
    def send(self, obj):
        """Puts an object in the pipe and returns."""
        self.pipeEnd.send(obj)


    def process_object(self, obj):
        """Process the object received from the pipe.
        
        This method does nothing, you should implement it in a derived class.
        """
        pass


class MyIOThread(IOThread):
    def process_object(self, obj):
        print "Received: ", obj

if __name__ == "__main__":
    from processing import Pipe
    myEnd, otherEnd = Pipe()
    ioThread = MyIOThread(otherEnd)
    
    print "Starting Thread...",
    ioThread.start()
    print "done."
    
    print "Sending stuff...:"
    myEnd.send("foo")
    myEnd.send("bar")
    print "Done."
    
    print "The other way...:",
    ioThread.send("foo2")
    ioThread.send("bar2")
    print "done."
    
    print "See if we can read...:"
    print myEnd.recv()
    print myEnd.recv()
    print "done."
    
    print "Joining thread...",
    ioThread.stop()
    ioThread.join()
    print "done."