
import Feedback

import time

class BenchmarkFeedback(Feedback.Feedback):
    
    def on_init(self):
        self.data = []
    
    def on_control_event(self, data):
        my_t = time.time()
        t = data["tuple"]
        self.data.append((t[0], t[1], my_t))
