'''
TabbedPanel
============
'''
from pprint import pprint
import json
import threading
import httplib
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
<SliderWithLabel>
    orientation: 'vertical'
    valign: 'top'
    Label:
        text: root.text
        size_hint: 1, .25
    Slider:
        id: value
        orientation: 'vertical'

<HomeTab@TabbedPanelItem>
    text: "Home"
    background_down: './home-grey.png'
    BoxLayout:
        SliderWithLabel:
            id: Main Lights
            text: "Lights"
        SliderWithLabel:
            text: "Temp"

<VanTabbedPanel>:
    do_default_tab: False

    HomeTab:
        id: home_tab
""")

class SliderWithLabel(BoxLayout):
    text = StringProperty()

class VanTabbedPanel(TabbedPanel):
    pass

class VanApp(App):
    def __init__(self):
        self.device_server = DeviceServer(host = 'localhost', port = 9292, app = self)
        self.device_server.start()
        App.__init__(self)

    def find_widget_with_name(self, name):
        return self.root.ids['home_tab'].ids[name]

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

    def __init__(self, host, port, app):
        threading.Thread.__init__(self)
        self.device_fetch_interval = 1
        self.app = app
        self.connection = httplib.HTTPConnection(host = host, port = port)

    def fetch_all_devices(self):
        self.connection.request("GET", "/api/remote_data")
        response = self.connection.getresponse()
        print response.status, response.reason
        self.devices = json.loads(response.read())

    def infinite_loop(self):
        while True:
            if self.stop.is_set():
                # Stop running this thread so the main Python process can exit.
                print "stopping device server thread"
                self.connection.close()
                return
            print "about to fetch all devices"
            self.fetch_all_devices()
            for device in self.devices:
                widget = self.app.find_widget_with_name(device['name'])
                print(widget.ids)
                widget.ids['value'].value = device['value']
                print(widget)
            print self.devices
            time.sleep(self.device_fetch_interval)

    def run(self):
        print "running device server thread"
        self.infinite_loop()

if __name__ == '__main__':
    VanApp().run()
