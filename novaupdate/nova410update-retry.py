# nova410update.py - Updater for the u-blox firmware on Hologram Nova R410
# Upgrades to Firmware version L05.08A02.04
#
# Author: Hologram <support@hologram.io>
# 
# Copyright 2019 - Hologram, Inc
#
# LICENSE: Distributed under the terms of the MIT License
#
# u-blox firmware binaries are Copyright u-blox AG (www.u-blox.com)


from Hologram.HologramCloud import HologramCloud, CustomCloud
import logging
import os
import re
import requests
import shutil
import sys
import time
from xmodem import XMODEM
import zipfile

class UpdaterException(Exception):
    pass

class NovaR410Updater(object):

    # The file structure is fairly complicated as it depends on
    # the starting firmware version and then the flash wear leveling
    # state on the modem itself. Once we know the start version
    # then we run through the different files in the package until one
    # works
    files = {
        '0200':(
                ( #package set 0
                    ( #stage 1 possible files
                        '0bb_stg1_pkg1-0m_L56A0200_to_L58A0204.bin',
                        '0bb_stg1_pkg2_4m_L56A0200_to_L58A0204.bin',
                        '0bb_stg1_pkg3_8m_L56A0200_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '0bb_stg2_L56A0200_to_L58A0204.bin',
                    )
                ),
                ( #package set 1
                    ( #stage 1 possible files
                        '1bb_stg1_pkg1_0m_L56A0200_to_L58A0204.bin',
                        '1bb_stg1_pkg2_4m_L56A0200_to_L58A0204.bin',
                        '1bb_stg1_pkg3_8m_L56A0200_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '1bb_stg2_L56A0200_to_L58A0204.bin',
                    )
                ),
                ( #package set 2
                    ( #stage 1 possible files
                        '2bb_stg1_pkg1_0m_L56A0200_to_L58A0204.bin',
                        '2bb_stg1_pkg2_4m_L56A0200_to_L58A0204.bin',
                        '2bb_stg1_pkg3_8m_L56A0200_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '2bb_stg2_L56A0200_to_L58A0204.bin',
                    )
                )
            ),
        '0201':(
                ( #package set 0
                    ( #stage 1 possible files
                        '0bb_stg1_pkg1_0m_L56A0201_to_L58A0204.bin',
                        '0bb_stg1_pkg2_4m_L56A0201_to_L58A0204.bin',
                        '0bb_stg1_pkg3_8m_L56A0201_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '0bb_stg2_L56A0201_to_L58A0204.bin',
                    )
                ),
                ( #package set 1
                    ( #stage 1 possible files
                        '1bb_stg1_pkg1_0m_L56A0201_to_L58A0204.bin',
                        '1bb_stg1_pkg2_4m_L56A0201_to_L58A0204.bin',
                        '1bb_stg1_pkg3_8m_L56A0201_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '1bb_stg2_L56A0201_to_L58A0204.bin',
                    )
                ),
                ( #package set 2
                    ( #stage 1 possible files
                        '2bb_stg1_pkg1_0m_L56A0201_to_L58A0204.bin',
                        '2bb_stg1_pkg2_4m_L56A0201_to_L58A0204.bin',
                        '2bb_stg1_pkg3_8m_L56A0201_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '2bb_stg2_L56A0201_to_L58A0204.bin',
                    )
                )
            )                
        }
    firmware_url = 'https://ublox-firmware.s3.amazonaws.com/'

    def __init__(self):
        self.logger = logging.getLogger('Nova410Updater')
        self.cloud = None

    def prompt_for_confirm(self):
        self.logger.debug('Checking for confirmation')
        prompt = '''
You are about to update the UBlox firmware on your Nova R410 device.
Once you continue past this point do not power off the modem
or stop this utility before it has completed.
Note that this update may change some behavior of the modem
related to profile selection and LED blinking. See hologram
documentation for more information.
The update may take up to 25 minutes to apply
Do you wish to continue? (y/n) '''
        reply = str(input(prompt)).lower().strip()
        if reply == 'y':
            return True
        return False
            

    def download_update_package(self, version):
        # download into ./fwpackage/version and extract
        package = 'L0506A%s-to-L0508A0204'%version
        filename = package + '.zip'
        dir_path = os.path.dirname(os.path.realpath(__file__))
        fwdir = os.path.join(dir_path, 'fw', version)
        if os.path.isdir(fwdir):
            self.logger.debug('Removing existing firmware directory')
            shutil.rmtree(fwdir)
        self.logger.debug('making dir: %s', fwdir)
        os.makedirs(fwdir)

        dl_file = os.path.join(fwdir, filename)
        firmware_url = self.firmware_url + filename
        self.logger.debug('fw url: %s', firmware_url)
        r = requests.get(firmware_url)
        open(dl_file, 'wb').write(r.content)

        with zipfile.ZipFile(dl_file, 'r') as zip_ref:
            zip_ref.extractall(fwdir)
        unzippeddir = os.path.join(fwdir, package)
        return unzippeddir


    def check_modem_type(self):
        self.logger.warning('Confirming modem type')
        modem_type = self.cloud.network.modem.modem_id
        if modem_type == 'SARA-R410M-02B':
            return True
        raise UpdaterException('Unsupported modem type')

    def get_modem_version_digits(self):
        version = self.cloud.network.modem._basic_command('I9')
        self.logger.warning('Got version %s', version)
        res = re.match(r'^L0\.0\.00\.00\.05\.0[68],A\.02\.(\d+)$', version)
        if res is None:
            raise UpdaterException('Invalid version string')
        digits = res.group(1)
        return digits

    def check_modem_version(self):
        self.logger.warning('Checking current modem version')
        digits = self.get_modem_version_digits()
        if digits == '04':
            raise UpdaterException('Already latest version')
        elif digits not in ('00', '01'):
            raise UpdaterException('Unsupported version')
        return '02' + digits

    def init_cloud(self):
        self.cloud = CustomCloud(None, network='cellular')


    def run_update(self, only_checks = False):
        self.init_cloud()
        self.check_modem_type()
        version = self.check_modem_version()
        package_dir = self.download_update_package(version)
        if only_checks:
            self.logger.warning('Stopping before applying')
            return True
        self.apply_update_package(version, package_dir)
        self.logger.warning('Waiting for install to complete and modem to reconnect')
        self.logger.warning('This could take 20 minutes. Do not unplug the modem')
        self.watch_for_stage2_complete()
        self.reprogram_leds()
        self.cloud.network.modem.reset()
        self.logger.warning('Done')
        return True

    def xgetc(self, size, timeout=1):
        return self.cloud.network.modem.serial_port.read(size)

    def xputc(self, data, timeout=1):
        return self.cloud.network.modem.serial_port.write(data)

    def send_file(self, filename):
        self.logger.warning('Sending file %s', filename)
        self.cloud.network.modem.serial_port.write_timeout = 20
        self.cloud.network.modem.command('+UFWUPD', '3', expected='ONGOING', timeout=60)
        time.sleep(5)
        fd = open(filename, 'rb')
        self.logger.warning('Writing file to serial port')
        modem = XMODEM(self.xgetc, self.xputc)
        sent_success = modem.send(fd, retry=25, timeout=90)
        fd.close()
        if not sent_success:
            raise UpdaterException('Failed to send file via xmodem')
        self.logger.debug('Done writing')
        time.sleep(1)
        return True

    def install_loaded_firmware(self):
        res, resp = self.cloud.network.modem.command('+UFWINSTALL', timeout=60)
        if res == 'Error':
            raise UpdaterException('Firmware Install failed')
        time.sleep(1)
        

    def apply_update_package(self, version, package_dir):
        for package in self.files[version]:
            packageok = True
            stagepassed = False
            #stage 1
            for filename in package[0]:
                fw_file = os.path.join(package_dir, filename)
                self.send_file(fw_file)
                self.install_loaded_firmware()
                res = self.check_for_stage1_return_code()
                if res == 'OK':
                    stagepassed = True
                    break
                elif res == 'STAGEFAIL':
                    self.logger.warning('Stage may have worked. Attempting next stage')
                    stagepassed = True
                    break
                elif res == 'PACKFAIL':
                    packageok = False
                    self.logger.warning('Package set failed. Trying next one')
                    break
            if not packageok or not stagepassed:
                continue
            #stage 2
            filename = package[1][0]
            fw_file = os.path.join(package_dir, filename)
            self.send_file(fw_file)
            self.install_loaded_firmware()
            return
        # looped through everything without success
        raise UpdaterException('Was unable to install any update package successfully')


    def check_for_stage1_return_code(self):
        self.logger.warning('Waiting for stage1 return code')
        self.wait_for_modem(61)
        result, response = self.cloud.network.modem.command('+UFWSTATUS?')
        fwstatus = re.match(r'\+UFWSTATUS: (\w+), (\w+), (\w+)', response)
        if not fwstatus:
            raise UpdaterException('Invalid UFWSTATUS response', fwstatus)
        flag, error_code, failure_reason = fwstatus.group(1, 2, 3)
        if flag.upper() == '55436F6D':
            # succeeded
            return 'OK'
        elif flag == '55457272':
            if error_code == '19a':
                if failure_reason == 'ffe3':
                    return 'STAGEFAIL'
                elif failure_reason == 'ffed':
                    return 'PACKFAIL'
                else:
                    raise UpdaterException('Unknown failure reason',
                            failure_reason)
            else:
                raise UpdaterException('Unknown error code', error_code)
        else:
            raise UpdaterException('Unknown flag', flag)


    def reprogram_leds(self):
        self.cloud.network.modem.command('+UGPIOC', '23,10')
        self.cloud.network.modem.command('+UGPIOC', '16,2')

    def wait_for_modem(self, maxtime):
        self.logger.warning('Waiting for modem')
        stop_at = time.time() + maxtime
        while time.time() < stop_at:
            self.cloud = None
            try:
                self.init_cloud()
            except Exception as e:
                time.sleep(30)
                self.logger.warning(
                        'Still waiting for modem to finish install. Do not unplug')
                continue
            break
        if self.cloud is None:
            raise UpdaterException('Failed to detect modem after maximum time')

    def watch_for_stage2_complete(self):
        # We should see the usb and serial ports go away while the install is
        # running so we watch for them to come back up and then run ATI9 to
        # confirm version is updated
        self.logger.info('Waiting for stage 2 install to finish. Could be 22 minutes')
        self.wait_for_modem( (60*22) )
        digits = self.get_modem_version_digits()
        if digits == '04':
            return
        else:
            raise UpdaterException('Got unexpected modem version', digits)


def main():
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(message)s'))
    sh.setLevel(logging.WARNING)
    logger.addHandler(sh)
    fh = logging.FileHandler('novaupdater.log')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    logger.debug('Started')

    upd = NovaR410Updater()
    if not upd.prompt_for_confirm():
        sys.exit(0)
    try:
        upd.run_update()
    except UpdaterException as e:
        logger.error('ERROR: '+str(e))
    else:
        print('Update Complete\n')


if __name__ == '__main__':
    main()





