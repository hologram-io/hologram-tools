# konekt-tools
The client-side tools you need to help build your next cellular-connected product

## ktunnel
`ktunnel` gives you easy port-forward access to your cellular-connected devices behind the Konekt firewall, without the need to set up VPN infrastructure. 

Why is this better than simply opening up ports to the public Internet? Simple: for security reasons, and so that bots cannot chew through your cellular data.

### Installation

1. Download the `konekt-tools` package (you may do so by clicking the `Download ZIP` button in GitHub).
2. Unzip and browse to the `konekt-ktunnel` directory.
3. Run `setup.py` (from your console, you can do this by running `python setup.py`).
4. Dependencies should be installed automatically.

### Usage

By default, you should be able to run the `ktunnel` command after installation and have it prompt you for the proper arguments. Running `ktunnel -h` will display help on how to use the command in more advanced ways.

When running `ktunnel` without any arguments (interactive prompting mode), you may identify a device either by entering the number located on your SIM card or by leaving the SIM card number field blank and then entering the numerical Device ID (available via API). By default, unless specified as an argument, `ktunnel` listens on localhost Port 9999 for connections, and tunnels connections through the Konekt Firewall in a secure and encrypted way. Once past the Konekt Firewall, data is sent to the destination device and device port specified by the user.

** On first run, `ktunnel` will generate a private/public key pair for authentication purposes, then exit. You will need to copy the displayed public key and paste that in the Dashboard to grant access to your devices at: https://dashboard.konekt.io **

(The `ktunnel-keygen` tool does not need to be used, but may optionally be used for more advanced control over the key generation process.)

## For more information
Questions? Chat about them at: https://community.konekt.io
