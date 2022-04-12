#!/bin/bash

umount -l /home/pi/drive/Garage_Videos
fusermount -u /home/pi/drive/Garage_Videos
rclone mount MemoryDevice:Garage_Videos/ /home/pi/drive/Garage_Videos
