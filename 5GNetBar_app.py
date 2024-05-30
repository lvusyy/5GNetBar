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


#pip install requests
#pip install pyobjc

##
# 注意 pyinstaller 在全局环境中的冲突问题
##
class AppDelegate(NSObject):
    def __init__(self):
        self.fetch_error_count = None

    def applicationDidFinishLaunching_(self, notification):
        # 创建状态栏图标
        self.statusBar = NSStatusBar.systemStatusBar()
        self.statusItemRSRP = self.statusBar.statusItemWithLength_(-1)  # 使用 -1 表示可变长度
        self.statusItemTemp = self.statusBar.statusItemWithLength_(-1)  # 使用 -1 表示可变长度

        # 创建菜单
        self.menuRSRP = NSMenu.alloc().init()
        self.menuTemp = NSMenu.alloc().init()

        # 添加菜单项
        self.refreshMenuItemRSRP = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Refresh", "refresh:", "")
        self.refreshMenuItemTemp = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Refresh", "refresh:", "")
        self.menuRSRP.addItem_(self.refreshMenuItemRSRP)
        self.menuTemp.addItem_(self.refreshMenuItemTemp)

        self.menuRSRP.addItem_(NSMenuItem.separatorItem())
        self.menuTemp.addItem_(NSMenuItem.separatorItem())

        self.quitMenuItemRSRP = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "")
        self.quitMenuItemTemp = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "")
        self.menuRSRP.addItem_(self.quitMenuItemRSRP)
        self.menuTemp.addItem_(self.quitMenuItemTemp)

        # 绑定菜单
        self.statusItemRSRP.setMenu_(self.menuRSRP)
        self.statusItemTemp.setMenu_(self.menuTemp)

        self.display_temp = True  # 初始显示温度信息

        # 初次刷新
        self.refresh_(None)

        # 每3秒自动刷新一次
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
        if login_response.status_code != 200:
            raise Exception("Login failed")
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
        self.token_expiry = time.time() + 1800  # 假设 token 有效期为 30 分钟
        self.fetch_error_count = 0

    @objc.python_method
    def fetch_signal_info(self):
        try:
            if not hasattr(self, 'token') or time.time() >= self.token_expiry and self.fetch_error_count > 3:
                self.login_and_get_token()
            signal_info_url = "http://192.168.1.1/jsonp_internet_info?callback=jsonp_callback"
            signal_response = self.session.get(signal_info_url, cookies={'token': self.token}, verify=False)
            if signal_response.status_code != 200:
                raise Exception("Failed to fetch signal info")
            response_text = signal_response.text
            match = re.search(r'jsonp_callback\((.*)\)', response_text)
            if not match:
                raise ValueError("Invalid JSONP response")
            xml_data = match.group(1).strip('"')
            root = ET.fromstring(xml_data)
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
        except Exception as e:
            self.fetch_error_count = getattr(self, 'fetch_error_count', 0) + 1
            print(f"Error fetching signal info: {e}")
            return None

    @objc.python_method
    def fetch_sys_info(self):
        try:
            if not hasattr(self, 'token') or time.time() >= self.token_expiry and self.fetch_error_count > 3:
                self.login_and_get_token()
            sys_info_url = "http://192.168.1.1:8080/api/get/sysinfo"
            sys_response = requests.get(sys_info_url, verify=False)
            if sys_response.status_code != 200:
                self.fetch_error_count = getattr(self, 'fetch_error_count', 0) + 1
                raise Exception("Failed to fetch system info")
            sys_info = sys_response.json()
            if sys_info['Code'] != 0:
                getattr(self, 'fetch_error_count', 0) + 1
                raise Exception(f"Error in response: {sys_info['Error']}")
            self.fetch_error_count = 0
            return sys_info['Data']
        except Exception as e:
            self.fetch_error_count = getattr(self, 'fetch_error_count', 0) + 1
            print(f"Error fetching system info: {e}")
            return None

    @objc.python_method
    def fetch_device_info(self):
        try:
            if not hasattr(self, 'token') or time.time() >= self.token_expiry and self.fetch_error_count > 3:
                self.login_and_get_token()
            device_info_url = "http://192.168.1.1/jsonp_sysinfo?callback=jsonp1717038353463&_=1717038388949"
            device_response = self.session.get(device_info_url, cookies={'token': self.token}, verify=False)
            if device_response.status_code != 200:
                raise Exception("Failed to fetch device info")
            response_text = device_response.text
            match = re.search(r'jsonp1717038353463\((.*)\)', response_text)
            if not match:
                raise ValueError("Invalid JSONP response")
            xml_data = match.group(1).strip('"')
            root = ET.fromstring(xml_data)
            device_info = {
                'cpu': root.find('cpu').text,
                'availablememory': root.find('availablememory').text,
                'totalmemory': root.find('totalmemory').text
            }
            self.fetch_error_count = 0
            return device_info
        except Exception as e:
            self.fetch_error_count = getattr(self, 'fetch_error_count', 0) + 1
            print(f"Error fetching device info: {e}")
            return None

    def refresh_(self, sender):
        def update_menu():
            signal_info = self.fetch_signal_info()
            sys_info = self.fetch_sys_info()
            device_info = self.fetch_device_info()
            if signal_info and sys_info and device_info:
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
                font = NSFont.systemFontOfSize_(7.5)

                self.display_temp = not self.display_temp  # 切换显示内容

                if rsrp > -85:
                    color_rsrp = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.8, 0.0, 0.8)  # 浅绿色
                elif -85 >= rsrp > -95:
                    color_rsrp = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.5, 0.0, 0.9)  # 浅黄色
                else:
                    color_rsrp = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.8)  # 浅红色

                if not self.display_temp:
                    if cpu_temp[0] / 1000 < 45 and battery_temp / 10 < 40:
                        color_temp = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.8, 0.0, 0.8)  # 浅绿色
                    elif 55 > cpu_temp[0] / 1000 >= 45 > battery_temp / 10 >= 42:
                        color_temp = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.5, 0.0, 0.9)  # 浅黄色
                    else:
                        color_temp = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.8)  # 浅红色
                else:
                    if int(cpu_usage) < 30 and int(available_mem) > int(total_mem) * 0.3:
                        color_temp = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.8, 0.0, 0.8)  # 浅绿色
                    elif int(cpu_usage) < 80 and int(available_mem) > int(total_mem) * 0.1:
                        color_temp = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.5, 0.0, 0.9)  # 浅黄色
                    else:
                        color_temp = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.8)  # 浅红色

                paragraph_style = NSMutableParagraphStyle.alloc().init()
                paragraph_style.setAlignment_(0)  # 左对齐

                attributes_rsrp = {
                    NSFontAttributeName: font,
                    NSForegroundColorAttributeName: color_rsrp,
                    NSBaselineOffsetAttributeName: -2.3,  # 调整基线偏移
                    NSParagraphStyleAttributeName: paragraph_style  # 左对齐
                }
                attributes_temp = {
                    NSFontAttributeName: font,
                    NSForegroundColorAttributeName: color_temp,
                    NSBaselineOffsetAttributeName: -2.3,  # 调整基线偏移
                    NSParagraphStyleAttributeName: paragraph_style  # 左对齐
                }
                attributedTitleRSRP = NSAttributedString.alloc().initWithString_attributes_(title_rsrp_rsrq,
                                                                                            attributes_rsrp)
                attributedTitleTemp = NSAttributedString.alloc().initWithString_attributes_(title_temp, attributes_temp)

                self.performSelectorOnMainThread_withObject_waitUntilDone_('updateMenuItems:', (
                attributedTitleRSRP, attributedTitleTemp, signal_info, sys_info, device_info), False)

        threading.Thread(target=update_menu).start()

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
            menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{key}: {value}", None, "")
            self.menuRSRP.addItem_(menuItem)
        for key, value in sys_info.items():
            menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{key}: {value}", None, "")
            self.menuTemp.addItem_(menuItem)
        for key, value in device_info.items():
            menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{key}: {value}", None, "")
            self.menuTemp.addItem_(menuItem)
        self.menuRSRP.addItem_(NSMenuItem.separatorItem())
        self.menuTemp.addItem_(NSMenuItem.separatorItem())
        self.menuRSRP.addItem_(self.quitMenuItemRSRP)
        self.menuTemp.addItem_(self.quitMenuItemTemp)


if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()