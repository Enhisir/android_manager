from pprint import pprint

import android_manager

print("########################")
print(android_manager.ADB.version())
pprint(android_manager.ADB.devices())

print("########################")
my_device = android_manager.Device("<your device serialno, if adb devices more than one>")
my_device.install("<path/to/app>", data_cache="<path/to/data/cache>")

print("########################")
print(my_device.serialno)
pprint(my_device.info)

print("########################")
print(f"name of your device is {my_device.name()}")
my_device.push("<path/of/your/file>", "<path/to>")
