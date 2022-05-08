# Moment
Captures Just the significant Moments in Time you want, without the need for laborous editing

Requirement:
Pinned to the 04-07-2022 Kernel Version of RaspiOS
https://downloads.raspberrypi.org/raspios_full_armhf/images/raspios_full_armhf-2022-04-07/

1. Connect to Device Access Point
2. Configure Wi-Fi Connection, Configure Web Storage Locaiton via RClone, and Auto Upload Behavior
3. Stream starts getting buffered to disk (up to 8GB of media before it starts recording over itself)
4. If button is pressed, save up to the last 3 minutes of data. Every 3 seconds the user holds the button, increase the save +3 more minutes. IE, 3 minutes of data saved, then 6 minutes of data saved, then 9 minutes, etc.
5. Save the data file as $date-MEMORY.mp4 locally
6. If the upload button is pressed after the save, go ahead and upload the memory to the webstorage location, else - wait till the Auto Upload Behavior that was preconfigured.

## Hardware Requirements

1. Raspberry Pi Zero 2
2. PiJuice Power Bank
3. USB OTG Cable
4. LCD/TFT Raspberry Pi HAT Screen with Buttons
5. Raspberry Pi Cam2 or ArduCam 16MP + Autofocus

## Workflow

### For the Configuration Steps:

1. Configure the AP Point utilize either [raspberry-wifi-conf](https://github.com/sabhiram/raspberry-wifi-conf) or [raspberry-pi-turnkey](https://github.com/schollz/raspberry-pi-turnkey)
2. Configure RClone utilize [RClone GUI](https://github.com/rclone/rclone-webui-react) for RClone Configuration Setup. 

### For the Memory Recording Step:

We will be segmenting the livestream into 5 second chunks, and then using [ffmpeg](https://superuser.com/questions/521113/join-mp4-files-in-linux) or libcamera to concatinate the video files when necessary. If the filesize of the overall folder of files is over 8GB in total, then we start to delete the files at the beginning as we save new footage. Since we are utilizing a Raspberry Pi Zero 2 as the hardware base - we can utilize one of the two cores to do the recording and the other core can handle the image processing. Every 5 seconds is when the image processing would "happen" with a hard interrupt when the buttons are pressed.

### Usage

RClone is found at the following URL:
http://<MomentDeviceIP>:5572
Username: "gui"
Password: "moment"

## References

[1. ffmeg video concatination](https://superuser.com/questions/521113/join-mp4-files-in-linux)

[2. Rclone Web GUI](https://github.com/rclone/rclone-webui-react)

[3. Raspberry-wifi-conf](https://github.com/sabhiram/raspberry-wifi-conf)

[4. Raspberry-pi-turnkey](https://github.com/schollz/raspberry-pi-turnkey)

[5. libcamera](https://github.com/kbingham/libcamera)

