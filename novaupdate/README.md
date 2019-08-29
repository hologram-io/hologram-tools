# Hologram Nova R410 Firmware Updater

This script will update the firmware on the ublox R410 module on the Hologram Nova.

To use:
1) Clone this repository to a Raspberry Pi or other Linux machine with the Hologram Nova SDK installed. `git clone https://github.com/hologram-io/hologram-tools.git`
2) cd into novaupdate directory
3) `sudo pip install -r requirements.txt`
4) `sudo python nova410update.py`

Then just follow the prompts and let it run. It may take up to 25 minutes to complete.

## Notes
-   This update will change the behavior of some cellular network commands like  `AT+URAT`  and  `AT+UMNOPROF`. See Appendix B.5 in the ublox Sara-R4 AT command manual for more information.
-   This update will change the behavior of the red LED on the Nova. (It will slowly blink now when on the network with a Hologram SIM instead of staying solid)

## Troubleshooting
After running the update, some boards may repeatedly shutdown after about a minute when a SIM is inserted and it is connected to the network. This procedure resolves it:
1) Connect to modem serial port using terminal program of your choice
2) Run these commands:
```
AT+CFUN=0
AT+UMNOPROF=2
AT+CFUN=15
```
Wait for board to restart and let it sit for a few seconds then reconnect and run:
```
AT+CFUN=0
AT+UMNOPROF=0
AT+CFUN=15
```

## Questions?
Post on the [Hologram Forum](community.hologram.io)

