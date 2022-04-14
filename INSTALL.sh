#!/bin/bash

# Install Rclone
echo "[DEBUG]:Install Rclone:"
curl https://rclone.org/install.sh | sudo bash
mkdir -p /home/pi/drive/Garage_Videos

# [TODO!]still need to configure rclone (which could be done via the web-interface?)
# rclone config

# Fix the udev rules
echo "[DEBUG]:Fix the udev rules:"
sudo cp 99-usb-autorun.rules /etc/udev/rules.d/
sudo install -m 644 *.service /etc/systemd/system/ 
install -m 777 *.sh /usr/local/bin
sudo udevadm control --reload && udevadm trigger
sudo systemctl start rclone-automount
sudo systemctl enable rclone-automount

#  Install Raspberry-Wifi-Config
echo "[DEBUG]:Install Raspberry-Wifi-Config:"
cd /home/pi
git clone https://github.com/NickEngmann/raspberry-wifi-conf.git
cd raspberry-wifi-conf

# Install npm and node as well as Raspberry-Wifi-Config dependencies
echo "[DEBUG]:Install npm and node as well as Raspberry-Wifi-Config dependencies:"
curl -sL https://deb.nodesource.com/setup_14.x | sudo bash -
sudo apt-get install -y nodejs
sudo npm install bower -g
npm update
bower install
sudo npm run-script provision
sudo npm start

# Set up Raspberry-Wifi-Config app as a service
echo "[DEBUG]:Set up Raspberry-Wifi-Config app as a service:"
sudo cp assets/init.d/raspberry-wifi-conf /etc/init.d/raspberry-wifi-conf 
sudo chmod +x /etc/init.d/raspberry-wifi-conf  
sudo update-rc.d raspberry-wifi-conf defaults
sudo systemctl unmask hostapd # by default the hostapd is masked so we need to unmask it
sudo systemctl enable hostapd
sudo systemctl start hostapd

# [TODO!] Edit rc.local to add the following lines before the exit 0
# cd /home/pi/raspberry-wifi-conf
# sudo /usr/bin/node server.js < /dev/null &

# Adding libcamera and Arducam to the system
echo "Adding `libcamera` and Arducam to the system:"
cd ~
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh
./install_pivariety_pkgs.sh -p libcamera_dev
./install_pivariety_pkgs.sh -p libcamera_apps
./install_pivariety_pkgs.sh -p imx519_kernel_driver
git clone https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver.git

# Open /boot/config.txt and add "dtoverlay=vc4-fkms-v3d" under [all] and then save and reboot
sudo sed -i -e '$i \dtoverlay=vc4-fkms-v3d\n' /boot/config.txt

# Installing miniTFT display
echo "[DEBUG]:Install miniTFT display:"
cd ~
sudo pip3 install --upgrade adafruit-python-shell click
sudo apt-get install -y git
git clone https://github.com/NickEngmann/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts
sudo python3 adafruit-pitft.py --display=st7789_240x240 --rotation=1 --install-type=fbcp

# Install packages related to the Moment python executable
echo "[DEBUG]:Install packages related to the Moment python executable:"
mkdir -p /home/pi/moment/icon
cp -rf icon /home/pi/moment
echo  "[DEBUG]:Installing Pip Requirements"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install --upgrade Pillow
echo  "[DEBUG]:Installing MomentCamera AutoStart service"
sudo install Moment.py /usr/bin/
sudo mkdir -p /home/pi/.config/autostart
sudo install -m 644 *.desktop /home/pi/.config/autostart/
sudo sed -i -e '$i \start_x=1\ngpu_mem=128\n' /boot/config.txt

# Reboot
echo "[SUCCESS]: Installation Finished, Rebooting Now..."
sleep 5
sudo reboot now