#!/bin/bash
# All Packages are pinned to the 2022-04-04 Kernel Release

sudo apt-get install -y git vim xdotool

# HOLD/PIN THE KERNEL IMAGES
sudo apt-mark hold libraspberrypi-bin libraspberrypi-dev libraspberrypi-doc libraspberrypi0
sudo apt-mark hold raspberrypi-bootloader raspberrypi-kernel raspberrypi-kernel-headers

# Upgrade all other packages
sudo apt update -y && sudo apt upgrade -y

# change hostname
sudo hostnamectl set-hostname moment

# Installing miniTFT display
echo "[DEBUG]:Install miniTFT display:"
cd ~
sudo pip3 install --upgrade adafruit-python-shell click
git clone https://github.com/NickEngmann/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts
sudo python3 adafruit-pitft.py --display=st7789_240x240 --rotation=1 --install-type=fbcp

# Adding libcamera and Arducam to the system
echo "Adding `libcamera` and Arducam to the system:"
cd ~
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh
./install_pivariety_pkgs.sh -p libcamera_dev
./install_pivariety_pkgs.sh -p libcamera_apps
./install_pivariety_pkgs.sh -p imx519_kernel_driver
git clone https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver.git

# Install Rclone
echo "[DEBUG]:Install Rclone:"
curl https://rclone.org/install.sh | sudo bash
mkdir -p /home/pi/drive/Garage_Videos

# Install rclone-webui-react
cd ~
git clone https://github.com/rclone/rclone-webui-react.git
cd rclone-webui-react/
npm install

# [TODO!]still need to configure rclone (which could be done via the web-interface?)
# rclone config

# Remember to name it "MemoryDevice" also remember to not change the root directory of the mount point
sudo install -m 644 *.service /etc/systemd/system/ 
sudo systemctl start rclone-automount
sudo systemctl enable rclone-automount
sudo systemctl start rclone-webui
sudo systemctl enable rclone-webui

# Fix the udev rules
echo "[DEBUG]:Fix the udev rules:"
sudo cp 99-usb-autorun.rules /etc/udev/rules.d/
sudo install -m 777 *.sh /usr/local/bin
sudo udevadm control --reload && udevadm trigger

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
# Commands do this are the following:

# ```
# sudo vi /etc/rc.local
# add below line 50
# cd /home/pi/raspberry-wifi-conf
# sudo /usr/bin/node server.js < /dev/null &
# ```

# change adafruit-pitft to not signal for reboot

# Install packages related to the Moment python executable
echo "[DEBUG]:Install packages related to the Moment python executable:"
mkdir -p /home/pi/Moment/icon
cp -rf icon /home/pi/Moment
echo  "[DEBUG]:Installing Pip Requirements"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install --upgrade Pillow
# Install Moment Config
echo "[DEBUG]:Install Moment Config:"
sudo mkdir -p /home/pi/.config/Moment
sudo cp -rf config/moment.config /home/pi/.config/Moment/
echo  "[DEBUG]:Installing MomentCamera AutoStart service"
sudo install Moment.py /usr/bin/
sudo mkdir -p /home/pi/.config/autostart
sudo install -m 644 *.desktop /home/pi/.config/autostart/
sudo cp Moment.desktop ~/Desktop/
sudo sed -i -e '$i \start_x=1\ngpu_mem=128\n' /boot/config.txt

# Overclock the Raspberry Pi Zero 2 W
sudo sed -i -e '$i \#Overclock 1200\narm_freq=1200\n' /boot/config.txt

# Reboot
echo "[SUCCESS]: Installation Finished, Rebooting Now..."
sleep 5
sudo reboot now

