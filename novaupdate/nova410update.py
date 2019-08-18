# Updater for Nova R410
# Upgrades to Firmware version L05.08A02.04

from Hologram.HologramCloud import HologramCloud
import logging
import os
import re
import sys
import urllib.request
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
                        '0bb_stg1_pkg1_0m_L56A0200_to_L58A0204.bin',
                        '0bb_stg1_pkg2_4m_L56A0200_to_L58A0204.bin ',
                        '0bb_stg1_pkg3_8m_L56A0200_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '0bb_stg2_L56A0200_to_L58A0204.bin',
                    )
                ),
                ( #package set 1
                    ( #stage 1 possible files
                        '1bb_stg1_pkg1_0m_L56A0200_to_L58A0204.bin',
                        '1bb_stg1_pkg2_4m_L56A0200_to_L58A0204.bin ',
                        '1bb_stg1_pkg3_8m_L56A0200_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '1bb_stg2_L56A0200_to_L58A0204.bin',
                    )
                ),
                ( #package set 2
                    ( #stage 1 possible files
                        '2bb_stg1_pkg1_0m_L56A0200_to_L58A0204.bin',
                        '2bb_stg1_pkg2_4m_L56A0200_to_L58A0204.bin ',
                        '2bb_stg1_pkg3_8m_L56A0200_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '2bb_stg2_L56A0200_to_L58A0204.bin',
                    )
                )
            )
        '0201':(
                ( #package set 0
                    ( #stage 1 possible files
                        '0bb_stg1_pkg1_0m_L56A0201_to_L58A0204.bin',
                        '0bb_stg1_pkg2_4m_L56A0201_to_L58A0204.bin ',
                        '0bb_stg1_pkg3_8m_L56A0201_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '0bb_stg2_L56A0201_to_L58A0204.bin',
                    )
                ),
                ( #package set 1
                    ( #stage 1 possible files
                        '1bb_stg1_pkg1_0m_L56A0201_to_L58A0204.bin',
                        '1bb_stg1_pkg2_4m_L56A0201_to_L58A0204.bin ',
                        '1bb_stg1_pkg3_8m_L56A0201_to_L58A0204.bin'
                    ),
                    ( #stage 2
                        '1bb_stg2_L56A0201_to_L58A0204.bin',
                    )
                ),
                ( #package set 2
                    ( #stage 1 possible files
                        '2bb_stg1_pkg1_0m_L56A0201_to_L58A0204.bin',
                        '2bb_stg1_pkg2_4m_L56A0201_to_L58A0204.bin ',
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
        self.logger = logging.getLogger(__name__)
        self.cloud = None

    def prompt_for_confirm(self):
        prompt = '''
        You are about to update the UBlox firmware on your Nova R410 device.
        Once you continue past this point do not power off the modem
        or stop this utility before it has completed.
        Note that this update may change some behavior of the modem
        related to profile selection and LED blinking. See hologram
        documentation for more information.
        The update may take up to 20 minutes to apply
        Do you wish to continue? (y/n)
        '''
        reply = str(raw_input(prompt)).lower().strip()
        if reply == 'y':
            return True
        return False
            

    def download_update_package(self, version):
        # download into ./fwpackage/version and extract
        filename = 'L0506A%s-to-L0508A0204.zip'%version
        dir_path = os.path.dirname(os.path.realpath(__file__))
        fwdir = os.path.join(dir_path, version)
        os.mkdir(fwdir)

        dl_file = os.path.join(fwdir, filename)
        firmware_url = self.firmware_url + '/' + filename
        urllib.request.urlretrieve(firmware_url, dl_file)

        unzippeddir = os.path.join(fwdir, 'fw')
        with zipfile.ZipFile(dl_file, 'r') as zip_ref:
            zip_ref.extractall(unzippeddir)
        return unzippeddir


    def check_modem_type(self):
        self.logger.info('Confirming modem type')
        modem_type = self.cloud.network.modem.modem_id
        if modem_type == 'SARA-R410M-02B':
            return True
        raise UpdaterException('Unsupported modem type')

    def get_modem_version_digits(self):
        version = self.cloud.network.modem._basic_command('ATI9')
        self.logger.info('Got version %s', version)
        res = re.match(r'^L0\.0\.00\.00\.05\.06,A\.02\.(\d+)$', version)
        if res is None:
            raise UpdaterException('Invalid version string')
        digits = res.group(1)
        return digits

    def check_modem_version(self):
        self.logger.info('Checking current modem version')
        digits = self.get_modem_version_digits()
        if digits == '04':
            raise UpdaterException('Already latest version')
        elif digits not in ('00', '01'):
            raise UpdaterException('Unsupported version')
        return '02' + digits

    def init_cloud(self):
        self.cloud = CustomCloud(None, network='cellular')


    def run_update(self, only_checks):
        self.init_cloud()
        self.check_modem_type():
        version = check_modem_version()
        if not self.prompt_for_confirm():
            return False
        package_dir = self.download_update_package(version)
        self.apply_update_package(version, package_dir)
        self.reprogram_leds()
        self.logger.info('Done')


    def send_file(self, filename):
        self.logger.info('Sending file %s', filename)
        self.cloud.network.modem.command('+UFWUPD', expected='ONGOING', timeout=1)
        fd = open(filename, 'rb')
        self.cloud.network.modem.serial_port.write(fd.read())
        self.cloud.network.modem.serial_port.flush()
        resp = self.cloud.network.modem.serial_port.read()
        self.logger.info('Response was: %s', resp)
        if resp[:-2] == 'OK':
            return True
        return False

    def install_loaded_firmware(self):
        self.cloud.network.modem.set('+UFWINSTALL')


    def apply_update_package(self, version, package_dir):
        for package in self.files[version]:
            packageok = True
            #stage 1
            for filename in package[0]:
                self.send_file(filename)
                self.install_loaded_firmware()
                res = self.check_for_stage1_return_code()
                if res == 'OK':
                    break
                elif res == 'STAGEFAIL':
                    continue
                elif res == 'PACKFAIL':
                    packageok = False
                    break
            if not packageok:
                continue
            #stage 2
            filename = package[1][0]
            self.send_file(filename)
            self.install_loaded_firmware()
            self.watch_for_stage2_complete()


    def check_for_stage1_return_code(self):
        self.logger.info('Waiting for stage1 return code')
        self.cloud.network.modem.serial_port.timeout = 60
        while True:
            r = self.cloud.network.modem.serial_port.readline()
            if not r:
                continue
            r = r.rstrip('\r\n')
            self.logger.debug('Read from port: %s', r)
            fwstatus = re.match(r'+UFWSTATUS: (\w+), (\w+), (\w)', r)
            if not fwstatus:
                continue
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
                        raise UpdaterException('Unknown failure reason %s',
                                failure_reason)
                else:
                    raise UpdaterException('Unknown error code %s', error_code)
            else:
                raise UpdaterException('Unknown flag %s', flag)


    def reprogram_leds(self):
        self.cloud.network.modem.command('+UGPIOC', '23,10')
        self.cloud.network.modem.command('+UGPIOC', '16,2')

    def wait_for_modem(self):
        while True:
            self.cloud = None
            try:
                self.init_cloud()
            except NetworkError as e:
                time.sleep(10)
                continue
            break

    def watch_for_stage2_complete(self):
        # We should see the usb and serial ports go away while the install is
        # running so we watch for them to come back up and then run ATI9 to
        # confirm version is updated
        self.wait_for_modem()
        digits = self.get_modem_version_digits()
        if digits == '04':
            return
        else:
            raise UpdaterException('Got unexpected modem version %s', digits)


def main():
    logger = logging.getLogger('')
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(message)s'))
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)
    fh = logging.FileHandler('novaupdater.log')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    upd = NovaR410Updater()
    if not upd.prompt_for_confirm():
        sys.exit(0)
    upd.run_update()
    print('Update Complete\n')


if __name__ == '__main__':
    main()





