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