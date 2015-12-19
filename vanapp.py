'''
TabbedPanel
============
'''
from pprint import pprint
import pdb
import json
import threading, thread
import httplib, urllib
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.slider import Slider

Builder.load_string("""
<SpecialSlider>
    orientation: 'vertical'

<SliderWithLabel>
    orientation: 'vertical'
    valign: 'top'
    Label:
        text: root.text
        size_hint: 1, .25
    SpecialSlider:
        id: value

<HomeTab@TabbedPanelItem>
    text: "Home"
    background_down: './home-grey.png'
    BoxLayout:
        SliderWithLabel:
            id: Main Lights
            remote_name: "Main Lights"
            text: "Lights"

<VanTabbedPanel>:
    do_default_tab: False

    HomeTab:
        id: home_tab
""")

class SpecialSlider(Slider):
    from_remote = False
    remote_name = StringProperty()

    def on_value(self, slider, value):
        if not self.from_remote:
            #super(SpecialSlider, self).on_touch_up(touch)
            _name = slider.parent.remote_name
            if _name is not None:
                _app = App.get_running_app()
                _app.device_server.send_device_value(d_name = _name, d_value = int(value))

class SliderWithLabel(BoxLayout):
    # Due to some nastyness with Kivy you can't seem to fetch the actual
    # id of a Widget so we have duplicated its value in remote_name
    remote_name = StringProperty()
    text = StringProperty()

    def update(self, value, minimum = None, maximum = None):
        _value_widget = self.ids['value']
        if _value_widget is not None:
            if minimum is not None and _value_widget.min != minimum:
                _value_widget.min = minimum
            if maximum is not None and _value_widget.max != maximum:
                _value_widget.max = maximum
            if value is not None and _value_widget.value != value:
                _value_widget.from_remote = True
                _value_widget.value = value
                _value_widget.from_remote = False

class VanTabbedPanel(TabbedPanel):
    pass

class VanApp(App):
    def __init__(self):
        self.device_server = DeviceServer(host = 'localhost', port = 9292, app = self)
        self.device_server.start()
        App.__init__(self)

    # TODO support multiple tabs here
    def find_widget_with_name(self, name):
        widget = self.root.ids['home_tab']
        if widget is None:
            return None
        return widget.ids[name]

    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.device_server.stop.set()

    def build(self):
        self.root = VanTabbedPanel()
#        th = TabWithBoxLayout(text="Home")
#        th.content.add_widget(SliderWithLabel(text='Lights'))
#        th.content.add_widget(SliderWithLabel(text='Other'))
#        th.content.add_widget(SliderWithLabel())
#        tp.add_widget(th)
        return self.root

class DeviceServer(threading.Thread):
    stop = threading.Event()
    http_lock = thread.allocate_lock()

    def __init__(self, host, port, app):
        threading.Thread.__init__(self)
        self.device_fetch_interval = 1
        self.app = app
        self.connection = httplib.HTTPConnection(host = host, port = port)

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

if __name__ == '__main__':
    VanApp().run()
