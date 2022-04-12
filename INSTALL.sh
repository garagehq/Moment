#!/bin/bash
curl https://rclone.org/install.sh | sudo bash
mkdir /home/pi/drive/
mkdir /home/pi/drive/Garage_Videos
# Fix the udev rules
sudo cp 99-usb-autorun.rules /etc/udev/rules.d/
sudo install -m 644 *.service /etc/systemd/system/ 
install -m 777 *.sh /usr/local/bin
sudo udevadm control --reload && udevadm trigger
sudo systemctl start rclone-automount
sudo systemctl enable rclone-automount