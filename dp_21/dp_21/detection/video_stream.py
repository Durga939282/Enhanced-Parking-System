import cv2
from threading import Thread
import queue

class VideoStream:
    def __init__(self, url):
        self.stream = cv2.VideoCapture(url)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.queue = queue.Queue(maxsize=2)
        self.stopped = False
        
    def start(self):
        thread = Thread(target=self.update, args=())
        thread.daemon = True
        thread.start()
        return self
        
    def update(self):
        while True:
            if self.stopped:
                return
            if self.queue.full():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    pass
            ret, frame = self.stream.read()
            if not ret:
                self.stop()
                return
            self.queue.put(frame)
                
    def read(self):
        return self.queue.get()
        
    def stop(self):
        self.stopped = True
        self.stream.release()

    # Add your existing VideoStream methods here 