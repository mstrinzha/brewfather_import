# brewfather_import
Plugin for CraftBeerPi. Plugin imports mash steps from BrewFather.app

## Installation:
Open a terminal window on Raspberry Pi and type:

```
cd craftbeerpi3
git clone https://github.com/mstrinzha/brewfather_import.git modules/plugins/brewfather_import
sudo apt-get install python-openssl
sudo pip install -r modules/plugins/brewfather_import/requirements.txt
```
Restart CraftBeerPi, open link in your favorite browser
```
https://<raspberrypi_ip>:5001/
```
and add selfsigned sertificate to trusted.

Open BrewFather.app, enable Custom Endpoint and set URL:
```
https://<raspberrypi_ip>:5001/brewfather_import/v1
```

Enjoy.
