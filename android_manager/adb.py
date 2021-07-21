import subprocess
from os import getenv, environ, listdir
from pathlib import Path
from zipfile import ZipFile
from tempfile import gettempdir
from typing import Optional

import android_manager.log as am_log
import android_manager.exceptions as am_exceptions
import android_manager.device as am_device

logger = am_log.logger


class ADB:
    logger.info("starting ADB connection...")
    PLATFORM_TOOLS = Path.cwd().absolute()
    if PLATFORM_TOOLS.as_posix().endswith("android_manager"):
        PLATFORM_TOOLS = PLATFORM_TOOLS.parent
    PLATFORM_TOOLS = PLATFORM_TOOLS.joinpath("android_manager/platform-tools")

    if getenv("PLATFORM-TOOLS") is None:
        logger.warn(f"platform tools on machine not found, "
                    f"using local platform tools placed in {PLATFORM_TOOLS}")
        environ["PLATFORM-TOOLS"] = PLATFORM_TOOLS.as_posix()
    else:
        PLATFORM_TOOLS = Path(getenv("PLATFORM-TOOLS"))

    ADB_PATH = PLATFORM_TOOLS.joinpath("adb").as_posix()

    __start_server = subprocess.Popen([ADB_PATH, "start-server"], stdout=subprocess.PIPE, text=True)
    __start_server.wait()
    if __start_server.returncode != 0:
        logger.error(am_exceptions.ADBConnectException(f"Error occurred during connection:\n"
                                                       f"{__start_server.stdout.read()}"))
        logger.info("exiting...")
        exit()
    logger.info("ADB connection successful!")

    @staticmethod
    def version():
        logger.info("starting ADB.version()...")
        command = subprocess.Popen(
            [ADB.ADB_PATH, "version"],
            stdout=subprocess.PIPE,
            text=True
        )

        command.wait()
        if command.returncode != 0:
            logger.error(am_exceptions.ADBRuntimeException("Error occurred during ADB.version()"))
            logger.info("exiting...")
            exit()
        logger.info("ADB.version() was successfully finished!")
        return command.stdout.read().strip()

    @staticmethod
    def devices():
        logger.info("starting ADB.devices()...")
        command = subprocess.Popen(
            [ADB.ADB_PATH, "devices"],
            stdout=subprocess.PIPE,
            text=True
        )

        devices = []

        command.wait()
        if command.returncode != 0:
            logger.error(am_exceptions.ADBRuntimeException("Error occurred during ADB.devices()"))
            logger.info("exiting...")

        for line in command.stdout:
            # device line looks like "{serialno}    {state}"
            line = line.strip()
            if line.startswith("* ") or line in ("List of devices attached", ""):
                continue
            line = line.split()
            devices.append({
                "serialno": line[0],
                "state": line[1]
            })
        logger.info("ADB.devices() was successfully finished!")
        return devices

    @staticmethod
    def get_info(device: am_device.Device):
        logger.info(f"starting ADB.get_info(device={device})...")
        keys = [
            "ro.product.manufacturer",
            "ro.product.marketname",
            "ro.product.device",
            "ro.build.version.sdk"
        ]

        info = {}

        for key in keys:
            command = subprocess.Popen(
                [ADB.ADB_PATH, "-s", device.serialno, "shell", "getprop", key],
                stdout=subprocess.PIPE,
                text=True
            )
            command.wait()
            if command.returncode != 0:
                logger.error(am_exceptions.ADBRuntimeException("Error occurred during ADB.get_info()"))
                logger.info("exiting...")
                exit()
            values = command.stdout.read().strip().split(',')
            if len(values) == 1:
                values = values[0]
            else:
                for i in range(len(values)):
                    if values[i] == "true":
                        values[i] = True
                    elif values[i] == "false":
                        values[i] = False
                    elif values[i].isdigit():
                        values[i] = int(values[i])
            info[key] = values
        logger.info(f"ADB.get_info(device={device}) was successfully finished!")
        return info

    @staticmethod
    def install(device: am_device.Device,
                app: str,
                replace: bool = True,
                multiple: bool = False,
                data_cache: Optional[str] = "",
                obb_cache: Optional[str] = ""):
        logger.info(f"starting ADB.install(device={device}, "
                    f"app={app}, replace={replace}, multiple={multiple}, "
                    f"data_cache={data_cache}, obb_cache={obb_cache})...")

        if not Path(app).exists():
            logger.error(am_exceptions.ADBRuntimeException("Apk-file doesn't exists"))
            logger.info("exiting...")
            exit()
        if not app.endswith((".apk", ".apks")):
            logger.error(am_exceptions.ADBRuntimeException("ADB can install only .apk and .apks files"))
            logger.info("exiting...")
            exit()

        if data_cache:
            logger.info("extracting app cache in /sdcard/Android/data...")
            if not Path(data_cache).exists():
                logger.error(am_exceptions.ADBRuntimeException("data cache doesn't exists"))
                logger.info("exiting...")
                exit()
            try:
                archive = ZipFile(data_cache)
                tempdir = Path(gettempdir()).joinpath("android_manager_data_cache")
                archive.extractall(tempdir.as_posix())
                child = list(filter(lambda x: tempdir.joinpath(x).is_dir(), listdir(tempdir.as_posix())))[0]
                child = tempdir.joinpath(child).as_posix()
                ADB.push(device, child, "/sdcard/Android/data")
            except Exception as e:
                logger.error(am_exceptions.ADBRuntimeException("Some error occurred during data cache extraction"))
                logger.error(e)
                logger.info("exiting...")
                exit()
            else:
                logger.info("extracting app cache in /sdcard/Android/data was successfully finished!")

        if obb_cache:
            logger.info("installing app cache in /sdcard/Android/obb...")
            if not Path(obb_cache).exists():
                logger.error(am_exceptions.ADBRuntimeException("data cache doesn't exists"))
                logger.info("exiting...")
                exit()
            try:
                archive = ZipFile(obb_cache)
                tempdir = Path(gettempdir()).joinpath("android_manager_obb_cache")
                archive.extractall(tempdir.as_posix())
                child = list(filter(lambda x: tempdir.joinpath(x).is_dir(), listdir(tempdir.as_posix())))[0]
                child = tempdir.joinpath(child).as_posix()
                ADB.push(device, child, "/sdcard/Android/obb")
            except Exception as e:
                logger.error(am_exceptions.ADBRuntimeException("Some error occurred during obb cache extraction"))
                logger.error(e)
                logger.info("exiting...")
                exit()
            else:
                logger.info("extracting app cache in /sdcard/Android/obb was successfully finished!")

        args = [ADB.ADB_PATH, "-s", device.serialno, "install", app]
        if replace:
            args.insert(-1, "-r")
        if multiple:
            args[0] = "install-multi-package"
        command = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            text=True
        )
        command.wait()
        if command.returncode != 0:
            logger.error(am_exceptions.ADBRuntimeException("Error occurred during ADB.install()"))
            logger.info("exiting...")
            exit()
        logger.info(f"ADB.install(device={device},"
                    f"app={app}, replace={replace}, multiple={multiple},"
                    f"data_cache={data_cache}, obb_cache={obb_cache}) was successfully finished!")

    @staticmethod
    def push(device: am_device.Device, fpath: str, path_to: str):
        logger.info(f"starting ADB.push(device={device},"
                    f" fpath={fpath}, path_to={path_to})...")
        if not Path(fpath).exists():
            logger.error(am_exceptions.ADBRuntimeException("from-file doesn't exists"))
            logger.info("exiting...")
            exit()
        command = subprocess.Popen(
            [ADB.ADB_PATH, "-s", device.serialno, "push", fpath, path_to],
            stdout=subprocess.PIPE,
            text=True
        )
        command.wait()
        if command.returncode != 0:
            logger.error(am_exceptions.ADBRuntimeException("Error occurred during ADB.push()"))
            logger.info("exiting...")
            exit()
        logger.info(f"ADB.push(device={device},"
                    f" fpath={fpath}, path_to={path_to}) was successfully finished!")
