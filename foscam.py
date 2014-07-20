from urllib.request import urlopen
from queue import Queue
from threading import Thread

class Foscam:
    """ Foscam class to read images from the foscam IP camera
    """
    def __init__(self, ip):
        # resolution: 8=320x244, 32=640x488
        self.hostIP = ip
        self.running = True
        self.irOnOff (False)

    def irOnOff (self, onOff):
        self.decoderCtrl (95 if onOff else 94)

    def decoderCtrl (self, cmd):
        url = "http://%s/decoder_control.cgi?command=%d&user=operator&pwd=" % (self.hostIP, cmd)
        fh = urlopen (url)
        fh.read ()
        
    def getImage (self, resol=8):    
        """
        resolution 4: 160x120, 8: 320x244, 16: 352x288, 32: 640x488
        Returns the lastest image from camera and the BW version
        """
        # Convert to B&W image
        url = "http://%s/snapshot.cgi?resolution=%d&user=guest&pwd=" % (self.hostIP, resol)
        fh = urlopen (url)
        return fh.read ()

    def getStream (self, rate, resol=8):
        """
        This is a generator.
        rate: 0=30fps, 1=15fps, 2=12fps, 5=9fps, 10=5fps, 15=1fps at resolution=4 (160x120 px)\n",
        Reads a stream of jpeg images
        This is a multi-body HTTP response.
        First element is a marker, followed by a few headers (content-type, content-length).
        Then the body data.
        Then repeat.
        """
        url = "http://%s/videostream.cgi?rate=%d&resolution=%d&user=guest&pwd=" % (self.hostIP, rate, resol)
        fh = urlopen (url)
        while self.running:
            marker = fh.readline ()
            contentType = fh.readline ()
            contentLength = fh.readline ()
            dummy = fh.readline()
            parts = contentLength.strip().split()
            buf = fh.read (int(parts[1]))
            dummy = fh.readline()
            yield buf
        
    def stop(self):
        self.running = False

    def loop(self):
        queue = self.queue
        for img in self.stream:
            if queue.full():
                queue.get()
            queue.put_nowait(img)

    def getQueue(self, rate, resol):
        """
        Creates queue and starts a thread to read images.
        Puts images into queue.
        Returns queue
        """
        self.queue = Queue(2)
        self.stream = self.getStream(rate, resol)
        thr = Thread(target=self.loop)
        thr.daemon = True
        thr.start()
        return self.queue


