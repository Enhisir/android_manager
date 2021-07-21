from typing import Optional
import android_manager


class Device:

    __serialno: str
    __info: str

    def __init__(self, serialno: Optional[str] = None):
        device = android_manager.ADB.devices()

        if not device:
            raise android_manager.ADBConnectException("ADB device not found")
        elif len(device) > 1:
            if serialno is None:
                raise android_manager.ADBConnectException("Number of devices is more than 1. Please, give me the serialno")
            found = False
            for i in device:
                if i["serialno"] == serialno:
                    if i["state"] in ("offline", "fastboot"):
                        raise android_manager.ADBConnectException("Please, turn your device into debug mode")
                    found = False
                    break
            if not found:
                raise android_manager.ADBConnectException(f"ADB device with serialno={serialno} not found")
        else:
            your_device = device[0]
            if serialno is None:
                if your_device["state"] in ("offline", "fastboot"):
                    raise android_manager.ADBConnectException("Please, turn your device into debug mode")
                serialno = your_device["serialno"]
            elif your_device["serialno"] != serialno:
                raise android_manager.ADBConnectException(f"ADB device with serialno={serialno} not found")
        self.__serialno = serialno

        self.__info = android_manager.ADB.get_info(self)

    def __repr__(self):
        return f"Device(serialno={self.__serialno})"

    @property
    def serialno(self):
        return self.__serialno

    @property
    def info(self):
        return self.__info.copy()

    def name(self):
        return f"{self.__info['ro.product.manufacturer']} {self.__info['ro.product.marketname']}"

    def install(self, app, replace=True, multiple=False, data_cache="", obb_cache=""):
        return android_manager.ADB.install(self, app,
                                           replace=replace,
                                           multiple=multiple,
                                           data_cache=data_cache,
                                           obb_cache=obb_cache)

    def push(self, path_from, path_to):
        return android_manager.ADB.push(self, path_from, path_to)
