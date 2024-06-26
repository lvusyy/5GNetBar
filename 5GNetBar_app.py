import requests
import xml.etree.ElementTree as ET
import re
from Foundation import NSObject, NSTimer
from AppKit import NSApplication, NSStatusBar, NSMenu, NSMenuItem, NSFont, NSAttributedString, NSColor, \
    NSMutableParagraphStyle, NSFontAttributeName, NSForegroundColorAttributeName, NSBaselineOffsetAttributeName, \
    NSParagraphStyleAttributeName, NSWorkspace,NSPasteboard,NSPasteboardTypeString
import objc
import threading
import json
import time


class AppDelegate(NSObject):
    fetch_error_count = 0

    def applicationDidFinishLaunching_(self, notification):
        self.statusBar = NSStatusBar.systemStatusBar()
        self.statusItemRSRP = self.statusBar.statusItemWithLength_(-1)
        self.statusItemTemp = self.statusBar.statusItemWithLength_(-1)

        self.menuRSRP = NSMenu.alloc().init()
        self.menuTemp = NSMenu.alloc().init()

        self.refreshMenuItemRSRP = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("刷新数据", "refresh:", "")
        self.refreshMenuItemTemp = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("刷新数据", "refresh:", "")
        self.menuRSRP.addItem_(self.refreshMenuItemRSRP)
        self.menuTemp.addItem_(self.refreshMenuItemTemp)

        self.menuRSRP.addItem_(NSMenuItem.separatorItem())
        self.menuTemp.addItem_(NSMenuItem.separatorItem())

        self.quitMenuItemRSRP = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("退出程序", "terminate:", "")
        self.quitMenuItemTemp = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("退出程序", "terminate:", "")
        self.menuRSRP.addItem_(self.quitMenuItemRSRP)
        self.menuTemp.addItem_(self.quitMenuItemTemp)

        self.statusItemRSRP.setMenu_(self.menuRSRP)
        self.statusItemTemp.setMenu_(self.menuTemp)

        self.display_temp = True

        self.refresh_(None)

        self.start_timer()

        # 监听系统睡眠和唤醒通知
        self.notification_center = NSWorkspace.sharedWorkspace().notificationCenter()
        self.notification_center.addObserver_selector_name_object_(
            self, objc.selector(self.will_sleep_, signature='v@:@@'), 'NSWorkspaceWillSleepNotification', None)
        self.notification_center.addObserver_selector_name_object_(
            self, objc.selector(self.did_wake_, signature='v@:@@'), 'NSWorkspaceDidWakeNotification', None)

    def start_timer(self):
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            3.0, self, 'refresh:', None, True)

    def stop_timer(self):
        if self.timer:
            self.timer.invalidate()
            self.timer = None

    def will_sleep_(self, notification, event):
        # 系统进入睡眠时停止定时器
        self.stop_timer()

    def did_wake_(self, notification, event):
        # 系统唤醒时重新启动定时器
        self.start_timer()

    def parse_respose_status(self,response):
        if response.status_code < 400:
            return True
        else:
            return False

    @objc.python_method
    def login_and_get_token(self):
        session = requests.Session()
        timestamp = str(int(time.time() * 1000))

        login_url = "http://192.168.1.1/adminLogin"
        login_params = {
            "callback": f"jsonp{timestamp}",
            "_": str(int(time.time() * 1000)),
            "loginparam": json.dumps({
                "username": "admin",
                "password": "admin"
            })
        }

        print("******** ready to login ********")

        login_response = session.get(login_url, params=login_params, timeout=5,verify=False)
        login_response.raise_for_status()

        login_response_text = login_response.text
        match = re.search(f'jsonp{timestamp}'+r'\("(<blog>.*)</blog>"\)', login_response_text)
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
    def fetch_signal_info(self):
        if self.fetch_error_count > 3 or not hasattr(self, 'token') or time.time() >= self.token_expiry  :
            self.login_and_get_token()

        try:
            signal_info_url = "http://192.168.1.1/jsonp_internet_info?callback=jsonp_callback"
            signal_response = self.session.get(signal_info_url, cookies={'token': self.token},timeout=3 ,verify=False)
            signal_response.raise_for_status()
            if not self.parse_respose_status(signal_response):
                raise Exception("Error in response, msg:{}".format(signal_response.text))
            response_text = signal_response.text
            match = re.search(r'jsonp_callback\((.*)\)', response_text)
            if not match:
                raise ValueError("Invalid JSONP response")

            xml_data = match.group(1).strip('"')
            root = ET.fromstring(xml_data)
            signal_info = {child.tag: child.text for child in root}
            self.fetch_error_count = 0
            return signal_info
        except Exception as e:
            self.fetch_error_count += 1
            print(f"Error fetching signal info: {e}")
            return None

    @objc.python_method
    def fetch_sys_info(self):
        # if not hasattr(self, 'token') or time.time() >= self.token_expiry or self.fetch_error_count > 3:
        #     self.login_and_get_token()

        try:
            sys_info_url = "http://192.168.1.1:8080/api/get/sysinfo"
            sys_response = requests.get(sys_info_url,timeout=3, verify=False)
            sys_response.raise_for_status()
            if not self.parse_respose_status(sys_response):
                raise Exception("Error in response, msg:{}".format(sys_response.text))
            sys_info = sys_response.json()
            if sys_info['Code'] != 0:
                raise Exception(f"Error in response: {sys_info['Error']}")

            return sys_info['Data']
        except Exception as e:
            print(f"Error fetching system info: {e}")
            return None

    @objc.python_method
    def fetch_device_info(self):
        if not hasattr(self, 'token') or time.time() >= self.token_expiry or self.fetch_error_count > 3:
            self.login_and_get_token()

        try:
            timestamp = str(int(time.time() * 1000))
            device_info_url = f"http://192.168.1.1/jsonp_sysinfo?callback=jsonp{timestamp}&_={int(timestamp)+220000}"
            device_response = self.session.get(device_info_url, cookies={'token': self.token},timeout=3, verify=False)
            device_response.raise_for_status()

            if not self.parse_respose_status(device_response):
                raise Exception("Error in response, msg:{}".format(device_response.text))

            response_text = device_response.text
            match = re.search(f'jsonp{timestamp}'+r'\((.*)\)', response_text)
            if not match:
                raise ValueError("Invalid JSONP response")

            xml_data = match.group(1).strip('"')
            root = ET.fromstring(xml_data)
            device_info = {child.tag: child.text for child in root}
            self.fetch_error_count = 0
            return device_info
        except Exception as e:
            self.fetch_error_count += 1
            print(f"Error fetching device info: {e}")
            return None

    def refresh_(self, sender):
        def update_menu():
            signal_info = self.fetch_signal_info()
            sys_info = self.fetch_sys_info()
            device_info = self.fetch_device_info()

            if signal_info and sys_info and device_info:
                self.update_status_items(signal_info, sys_info, device_info)

        threading.Thread(target=update_menu).start()

    @objc.python_method
    def update_status_items(self, signal_info, sys_info, device_info):
        rsrp = int(signal_info['rsrp'])
        rsrq = signal_info['rsrq']
        cpu_temp = sys_info['CPU_TEMP']
        battery_temp = sys_info['POWER_SUPPLY_TEMP']
        cpu_usage = device_info['cpu']
        available_mem = device_info['availablememory']
        total_mem = device_info['totalmemory']

        title_rsrp_rsrq = f"RSRP: {rsrp}\nRSRQ: {rsrq}"
        if self.display_temp:
            title_temp = f"CPU T: {cpu_temp[0] / 1000:.1f}°C\nBAT T: {battery_temp / 10:.1f}°C"
        else:
            title_temp = f"CPU U: {cpu_usage}%\nMEM V: {int(available_mem) / 1024:.0f}M"

        font = NSFont.systemFontOfSize_(7.5)
        self.display_temp = not self.display_temp

        color_rsrp = self.get_color_rsrp(rsrp)
        color_temp = self.get_color_temp(cpu_temp, battery_temp, cpu_usage, available_mem, total_mem)

        attributes_rsrp = self.get_attributes(font, color_rsrp)
        attributes_temp = self.get_attributes(font, color_temp)

        attributedTitleRSRP = NSAttributedString.alloc().initWithString_attributes_(title_rsrp_rsrq, attributes_rsrp)
        attributedTitleTemp = NSAttributedString.alloc().initWithString_attributes_(title_temp, attributes_temp)

        self.performSelectorOnMainThread_withObject_waitUntilDone_('updateMenuItems:', (attributedTitleRSRP, attributedTitleTemp, signal_info, sys_info, device_info), False)

    @objc.python_method
    def get_color_rsrp(self, rsrp):
        if rsrp > -85:
            return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.8, 0.0, 0.8)  # 浅绿色
        elif -85 >= rsrp > -95:
            return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.5, 0.0, 0.9)  # 浅黄色
        else:
            return NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.8)  # 浅红色

    @objc.python_method
    def get_color_temp(self, cpu_temp, battery_temp, cpu_usage, available_mem, total_mem):
        if not self.display_temp:
            if cpu_temp[0] / 1000 < 45 and battery_temp / 10 < 40:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.8, 0.0, 0.8)  # 浅绿色
            elif 55 > cpu_temp[0] / 1000 >= 45 or 42 <= battery_temp / 10 < 55:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.5, 0.0, 0.9)  # 浅黄色
            else:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.8)  # 浅红色
        else:
            if int(cpu_usage) < 30 and int(available_mem) > int(total_mem) * 0.3:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.8, 0.0, 0.8)  # 浅绿色
            elif int(cpu_usage) < 80 and int(available_mem) > int(total_mem) * 0.1:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.5, 0.0, 0.9)  # 浅黄色
            else:
                return NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.8)  # 浅红色

    @objc.python_method
    def get_attributes(self, font, color):
        paragraph_style = NSMutableParagraphStyle.alloc().init()
        paragraph_style.setAlignment_(0)  # 左对齐
        return {
            NSFontAttributeName: font,
            NSForegroundColorAttributeName: color,
            NSBaselineOffsetAttributeName: -2.3,  # 调整基线偏移
            NSParagraphStyleAttributeName: paragraph_style  # 左对齐
        }

    def updateMenuItems_(self, params):
        attributedTitleRSRP, attributedTitleTemp, signal_info, sys_info, device_info = params

        self.statusItemRSRP.setAttributedTitle_(attributedTitleRSRP)
        self.statusItemTemp.setAttributedTitle_(attributedTitleTemp)

        self.menuRSRP.removeAllItems()
        self.menuTemp.removeAllItems()
        self.menuRSRP.addItem_(self.refreshMenuItemRSRP)
        self.menuTemp.addItem_(self.refreshMenuItemTemp)
        self.menuRSRP.addItem_(NSMenuItem.separatorItem())
        self.menuTemp.addItem_(NSMenuItem.separatorItem())

        for key, value in signal_info.items():
            menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{key}: {value}", "copyItem:", "")
            menuItem.setRepresentedObject_(f"{key}: {value}")
            self.menuRSRP.addItem_(menuItem)

        for key, value in sys_info.items():
            menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{key}: {value}", "copyItem:", "")
            menuItem.setRepresentedObject_(f"{key}: {value}")
            self.menuTemp.addItem_(menuItem)

        self.menuTemp.addItem_(NSMenuItem.separatorItem())

        for key, value in device_info.items():
            menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{key}: {value}", "copyItem:", "")
            menuItem.setRepresentedObject_(f"{key}: {value}")
            self.menuTemp.addItem_(menuItem)

        self.menuRSRP.addItem_(NSMenuItem.separatorItem())
        self.menuTemp.addItem_(NSMenuItem.separatorItem())
        self.menuRSRP.addItem_(self.quitMenuItemRSRP)
        self.menuTemp.addItem_(self.quitMenuItemTemp)

    def copyItem_(self, sender):
        pboard = NSPasteboard.generalPasteboard()
        pboard.clearContents()
        pboard.setString_forType_(sender.representedObject(), NSPasteboardTypeString)


if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()