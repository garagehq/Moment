#!/bin/bash

# install rclone
curl https://rclone.org/install.sh | sudo bash

# Fix the udev rules
sudo cp 99-usb-autorun.rules /etc/udev/rules.d/
sudo install -m 644 *.service /etc/systemd/system/ 
install -m 777 *.sh /usr/local/bin
sudo udevadm control --reload && udevadm trigger
sudo systemctl start rclone-automount
sudo systemctl enable rclone-automount

# install raspberry wifi config
cd /home/pi
git clone https://github.com/sabhiram/raspberry-wifi-conf.git
cd raspberry-wifi-conf
# install npm and node
curl -sL https://deb.nodesource.com/setup_14.x | sudo bash -
sudo apt-get install -y nodejs
sudo npm install bower -g
npm update
bower install
sudo npm run-script provision
sudo npm start
mkdir /home/pi/drive/
mkdir /home/pi/drive/Garage_Videos

# set up raspberry wifi config app as a service
sudo cp assets/init.d/raspberry-wifi-conf /etc/init.d/raspberry-wifi-conf 
sudo chmod +x /etc/init.d/raspberry-wifi-conf  
sudo update-rc.d raspberry-wifi-conf defaults
sudo systemctl unmask hostapd # by default the hostapd is masked so we need to unmask it
sudo systemctl enable hostapd
sudo systemctl start hostapd

# edit rc.local to add the following lines before the exit 0
# cd /home/pi/raspberry-wifi-conf
# sudo /usr/bin/node server.js < /dev/null &

# add libcamera and Arducam to the system
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh
./install_pivariety_pkgs.sh -p libcamera_dev
./install_pivariety_pkgs.sh -p libcamera_apps
./install_pivariety_pkgs.sh -p imx519_kernel_driver
git clone https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver.git

# Open /boot/config.txt and add "dtoverlay=vc4-fkms-v3d" under [all] and then save and reboot

# Install miniTFT display
https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/1-3-240x240-kernel-module-install
# ^remember to change a line in the libts installation to include installing libts-dev, i.e.: sudo apt install libts-dev
# this means I am going to have to fork the repo and make the change inline and add all the instructions

sudo reboot now