import thread
from threading import Thread, Event
from httplib import HTTPConnection
import urllib
import json
import time

class DeviceServerProxy(Thread):
    stop = Event()
    http_lock = thread.allocate_lock()

    def __init__(self, host, port, app):
        Thread.__init__(self)
        self.device_fetch_interval = 1
        self.app = app
        self.connection = HTTPConnection(host = host, port = port)

    def fetch_all_devices(self):
        with self.http_lock:
            self.connection.request(method = "GET", url = "/api/remote_data")
            response = self.connection.getresponse()
            #print response.status, response.reason
            self.devices = json.loads(response.read())

    def infinite_loop(self):
        while True:
            if self.stop.is_set():
                # Stop running this thread so the main Python process can exit.
                print "stopping device server thread"
                self.connection.close()
                return
            #print "about to fetch all devices"
            self.fetch_all_devices()
            for device in self.devices:
                widget = self.app.find_widget_with_name(device['name'])
                widget.update(value = device['value'], minimum = device['min'], maximum = device['max'])
                #print(widget)
            #print self.devices
            time.sleep(self.device_fetch_interval)

    def send_device_value(self, d_name, d_value):
        with self.http_lock:
            http_body = urllib.urlencode({'name': d_name, 'value': d_value})
            http_headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            self.connection.request(method = "POST", url = "/api/remote_data", headers = http_headers, body = http_body)
            response = self.connection.getresponse()
            content = response.read()

    def run(self):
        print "running device server thread"
        self.infinite_loop()
