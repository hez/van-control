'''
TabbedPanel
============
'''
# Python
from pprint import pprint
import pdb

from kivy.app import App
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty
from kivy.config import ConfigParser

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.settings import Settings
from kivy.uix.slider import Slider

# Local libraries
from device_server_proxy import DeviceServerProxy

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
        App.__init__(self)
        self.config = ConfigParser()
        self.config.read('van.ini')
        self.device_server = DeviceServerProxy(
            host = self.config.get("server", "host"),
            port = self.config.getint("server", "port"),
            app = self)
        self.device_server.start()

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
        self.settings = Settings()
#        th = TabWithBoxLayout(text="Home")
#        th.content.add_widget(SliderWithLabel(text='Lights'))
#        th.content.add_widget(SliderWithLabel(text='Other'))
#        th.content.add_widget(SliderWithLabel())
#        tp.add_widget(th)
        return self.root

if __name__ == '__main__':
    VanApp().run()
