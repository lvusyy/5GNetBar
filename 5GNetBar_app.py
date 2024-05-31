import requests
import xml.etree.ElementTree as ET
import re
from Foundation import NSObject, NSTimer
from AppKit import NSApplication, NSStatusBar, NSMenu, NSMenuItem, NSFont, NSAttributedString, NSColor, \
    NSMutableParagraphStyle, NSFontAttributeName, NSForegroundColorAttributeName, NSBaselineOffsetAttributeName, \
    NSParagraphStyleAttributeName
import objc
import threading
import json
import time


class AppDelegate(NSObject):
    def __init__(self):
        self.fetch_error_count = 0

    def applicationDidFinishLaunching_(self, notification):
        self.setupStatusBar()
        self.refresh_(None)
        self.startTimer()

    def setupStatusBar(self):
        self.statusBar = NSStatusBar.systemStatusBar()
        self.statusItemRSRP = self.statusBar.statusItemWithLength_(-1)
        self.statusItemTemp = self.statusBar.statusItemWithLength_(-1)
        self.menuRSRP = NSMenu.alloc().init()
        self.menuTemp = NSMenu.alloc().init()
        self.setupMenuItems()
        self.statusItemRSRP.setMenu_(self.menuRSRP)
        self.statusItemTemp.setMenu_(self.menuTemp)
        self.display_temp = True

    def setupMenuItems(self):
        self.refreshMenuItemRSRP = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Refresh", "refresh:", "")
        self.refreshMenuItemTemp = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Refresh", "refresh:", "")
        self.quitMenuItemRSRP = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "")
        self.quitMenuItemTemp = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "")
        self.menuRSRP.addItem_(self.refreshMenuItemRSRP)
        self.menuTemp.addItem_(self.refreshMenuItemTemp)
        self.menuRSRP.addItem_(NSMenuItem.separatorItem())
        self.menuTemp.addItem_(NSMenuItem.separatorItem())
        self.menuRSRP.addItem_(self.quitMenuItemRSRP)
        self.menuTemp.addItem_(self.quitMenuItemTemp)

    def startTimer(self):
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            3.0, self, 'refresh:', None, True)

    @objc.python_method
    def login_and_get_token(self):
        session = requests.Session()
        login_url = "http://192.168.1.1/adminLogin"
        login_params = {
            "callback": "jsonp1717028694845",
            "_": str(int(time.time() * 1000)),
            "loginparam": json.dumps({
                "username": "admin",
                "password": "admin"
            })
        }
        login_response = session.get(login_url, params=login_params, verify=False)
        login_response.raise_for_status()
        login_response_text = login_response.text
        match = re.search(r'jsonp1717028694845\("(<blog>.*)</blog>"\)', login_response_text)
        if not match:
            raise ValueError("Invalid JSONP response")
        xml_data = match.group(1)
        if "</blog>" not in xml_data:
            xml_data += "</blog>"
        root = ET.fromstring(xml_data)
        token = root.find('token').text
        if not token:
            raise Exception("Token not found in response")
        self.session = session
        self.token = token
        self.token_expiry = time.time() + 1800
        self.fetch_error_count = 0

    @objc.python_method
    def fetch_data(self, url, params=None, use_session=True):
        try:
            if not hasattr(self, 'token') or time.time() >= self.token_expiry and self.fetch_error_count > 3:
                self.login_and_get_token()
            if use_session:
                response = self.session.get(url, params=params, cookies={'token': self.token}, verify=False)
            else:
                response = requests.get(url, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.fetch_error_count += 1
            print(f"Error fetching data: {e}")
            return None

    @objc.python_method
    def parse_jsonp_response(self, response_text, callback):
        match = re.search(rf'{callback}\((.*)\)', response_text)
        if not match:
            self.fetch_error_count += 1
            raise ValueError("Invalid JSONP response")
        xml_data = match.group(1).strip('"')
        root = ET.fromstring(xml_data)
        return root

    @objc.python_method
    def fetch_signal_info(self):
        response_text = self.fetch_data("http://192.168.1.1/jsonp_internet_info?callback=jsonp_callback")
        if response_text:
            root = self.parse_jsonp_response(response_text, 'jsonp_callback')
            signal_info = {
                'iccid': root.find('iccid').text,
                'band': root.find('band').text,
                'operatorName': root.find('operatorName').text,
                'mcc': root.find('mcc').text,
                'mnc': root.find('mnc').text,
                'earfcn': root.find('earfcn').text,
                'rsrp': root.find('rsrp').text,
                'rssi': root.find('rssi').text,
                'rsrq': root.find('rsrq').text,
                'cellid': root.find('cellid').text,
                'pci': root.find('pci').text,
                'networkType': root.find('networkType').text,
                'imei': root.find('imei').text
            }
            self.fetch_error_count = 0
            return signal_info
        return None

    @objc.python_method
    def fetch_sys_info(self):
        response_text = self.fetch_data("http://192.168.1.1:8080/api/get/sysinfo", use_session=False)
        if response_text:
            sys_info = json.loads(response_text)
            if sys_info['Code'] != 0:
                self.fetch_error_count += 1
                raise Exception(f"Error in response: {sys_info['Error']}")
            self.fetch_error_count = 0
            return sys_info['Data']
        return None

    @objc.python_method
    def fetch_device_info(self):
        response_text = self.fetch_data("http://192.168.1.1/jsonp_sysinfo?callback=jsonp1717038353463&_=1717038388949")
        if response_text:
            root = self.parse_jsonp_response(response_text, 'jsonp1717038353463')
            device_info = {
                'cpu': root.find('cpu').text,
                'availablememory': root.find('availablememory').text,
                'totalmemory': root.find('totalmemory').text
            }
            self.fetch_error_count = 0
            return device_info
        return None

    def refresh_(self, sender):
        def update_menu():
            signal_info = self.fetch_signal_info()
            sys_info = self.fetch_sys_info()
            device_info = self.fetch_device_info()
            if signal_info and sys_info and device_info:
                self.display_temp = not self.display_temp
                self.performSelectorOnMainThread_withObject_waitUntilDone_('updateMenuItems:', (
                    signal_info, sys_info, device_info), False)

        threading.Thread(target=update_menu).start()

    def updateMenuItems_(self, params):
        signal_info, sys_info, device_info = params
        rsrp = int(signal_info['rsrp'])
        rsrq = signal_info['rsrq']
        cpu_temp = sys_info['CPU_TEMP']
        battery_temp = sys_info['POWER_SUPPLY_TEMP']
        cpu_usage = device_info['cpu']
        available_mem = device_info['availablememory']
        total_mem = device_info['totalmemory']

        title_rsrp_rsrq = f"RSRP: {rsrp}\nRSRQ: {rsrq}"
        if self.display_temp:
            title_temp = f"CPU T: {cpu_temp[0] / 1000:.1f}°C\nBAT  T: {battery_temp / 10:.1f}°C"
        else:
            title_temp = f"CPU U: {cpu_usage}%\nMEM V: {int(available_mem) / 1024:.0f}M"

        color_rsrp = self.get_color(rsrp, -85, -95)
        if self.display_temp:
            color_temp = self.get_color((cpu_temp[0] / 1000, battery_temp / 10), (45, 40), (55, 42))
        else:
            color_temp = self.get_color((int(cpu_usage), int(total_mem) - int(available_mem)), (30, int(total_mem) * 0.7), (80, int(total_mem) * 0.9))

        attributes_rsrp = self.get_attributes(color_rsrp)
        attributes_temp = self.get_attributes(color_temp)
        attributedTitleRSRP = NSAttributedString.alloc().initWithString_attributes_(title_rsrp_rsrq, attributes_rsrp)
        attributedTitleTemp = NSAttributedString.alloc().initWithString_attributes_(title_temp, attributes_temp)

        self.statusItemRSRP.setAttributedTitle_(attributedTitleRSRP)
        self.statusItemTemp.setAttributedTitle_(attributedTitleTemp)

        self.menuRSRP.removeAllItems()
        self.menuTemp.removeAllItems()
        self.menuRSRP.addItem_(self.refreshMenuItemRSRP)
        self.menuTemp.addItem_(self.refreshMenuItemTemp)
        self.menuRSRP.addItem_(NSMenuItem.separatorItem())
        self.menuTemp.addItem_(NSMenuItem.separatorItem())
        self.addMenuItems(self.menuRSRP, signal_info)
        self.addMenuItems(self.menuTemp, sys_info)
        self.addMenuItems(self.menuTemp, device_info)
        self.menuRSRP.addItem_(NSMenuItem.separatorItem())
        self.menuTemp.addItem_(NSMenuItem.separatorItem())
        self.menuRSRP.addItem_(self.quitMenuItemRSRP)
        self.menuTemp.addItem_(self.quitMenuItemTemp)

    def get_color(self, value, green_threshold, yellow_threshold):
        if isinstance(value, tuple):
            if all(v < t for v, t in zip(value, green_threshold)):
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.8, 0.0, 0.8)
            elif all(v < t for v, t in zip(value, yellow_threshold)):
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.5, 0.0, 0.9)
            else:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.8)
        else:
            if value > green_threshold:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.8, 0.0, 0.8)
            elif value > yellow_threshold:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.5, 0.0, 0.9)
            else:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.8)

    def get_attributes(self, color):
        font = NSFont.systemFontOfSize_(7.5)
        paragraph_style = NSMutableParagraphStyle.alloc().init()
        paragraph_style.setAlignment_(0)
        return {
            NSFontAttributeName: font,
            NSForegroundColorAttributeName: color,
            NSBaselineOffsetAttributeName: -2.3,
            NSParagraphStyleAttributeName: paragraph_style
        }

    def addMenuItems(self, menu, data):
        for key, value in data.items():
            menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{key}: {value}", None, "")
            menu.addItem_(menuItem)


if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()