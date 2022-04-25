#!/usr/bin/python3

from guizero import App, PushButton, Text, Picture, Window
from time import sleep
import time
import glob
import datetime
import sys
import os
import socket
from subprocess import PIPE, STDOUT, Popen, check_output, call
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library


class Moment:
    def __init__(self):
        self.capture_number = self.timestamp()
        self.video_capture_number = self.timestamp()
        self.picture_index = 0
        self.saved_pictures = []
        self.shown_picture = ""
        self.recording = False
        self.config_recordinglocation = "/home/pi/Videos/*"


        GPIO.setwarnings(False)  # Ignore warning for now
        GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            23, GPIO.FALLING, callback=self.processVideo, bouncetime=2500)
        GPIO.add_event_detect(
            24, GPIO.FALLING, callback=self.recordingControl, bouncetime=2500)

        self.app = App(layout="grid", title="Camera Controls",
                       bg="black", width=240, height=240)

        # Configure the Directory for the Videos
        os.system("rm -rf " + self.config_recordinglocation + "*")
        os.system("mkdir -p " + self.config_recordinglocation)

        # Pull all the Network Information
        gw = os.popen("ip -4 route show default").read().split()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((gw[2], 0))
        ipaddr = s.getsockname()[0]
        gateway = gw[2]
        host = socket.gethostname()
        ssid = os.popen("iwgetid -r").read()
        
        debugText = Text(self.app, color="white", grid=[
            0, 0], text="Network Information", size=30)

        hostText = Text(self.app, color="white", grid=[
                     0, 1], text="HOST:" + str(host), size=30)

        ipText = Text(self.app, color="white", grid=[
                     0, 2], text="IP:" + str(ipaddr), size=30)

        gatewayText = Text(self.app, color="white", grid=[
                     0, 3], text="GW:" + str(gateway), size=30)

        ssidText = Text(self.app, color="white", grid=[
                     0, 4], text="SSID:" + str(ssid), size=30)
        
        configText = Text(self.app, color="white", grid=[
            0, 5], text="CONFIG: http://" + str(ipaddr) + ":8080", size=24)


        self.busy = Window(self.app, bg="red",  height=240,
                           width=240, title="busy")

        self.app.tk.attributes("-fullscreen", True)
        self.busy.hide()
        self.app.display()
        sleep(4)
        self.recording = True
        capture_number = self.timestamp()
        command_execute = Popen(
            "libcamera-vid -t 0 --qt-preview --hflip --vflip --autofocus --keypress -o /home/pi/Videos/%03d-"+str(capture_number)+".h264 --segment 10000 width 1920 --height 1080 ", stdout=PIPE, stdin=PIPE, stderr=STDOUT, shell=True, close_fds=True)
        sleep(2)
        Popen("xdotool key alt+F11", shell=True)

    def clear(self):
        self.show_busy()
        os.system("rm -v /home/pi/Downloads/*")
        self.hide_busy()

    def show_busy(self):
        self.busy.show()
        print("busy now")

    def hide_busy(self):
        self.busy.hide()
        print("no longer busy")

    def fullscreen(self):
        self.app.tk.attributes("-fullscreen", True)

    def notfullscreen(self):
        self.app.tk.attributes("-fullscreen", False)

    # Generate timestamp string generating name for photos
    def timestamp(self):
        tstring = datetime.datetime.now()
        #print("Filename generated ...")
        return tstring.strftime("%Y%m%d_%H%M%S")

    def recordingControl(self, channel):
        print("Recording Control called")
        if self.recording == False:
            print("Recording started")
            self.recording = True
            capture_number = self.timestamp()
            command_execute = Popen(
                "libcamera-vid -t 0 --qt-preview --hflip --vflip --autofocus --keypress -o /home/pi/Videos/%03d-"+str(capture_number)+".h264 --segment 10000 width 1920 --height 1080 ", stdout=PIPE, stdin=PIPE, stderr=STDOUT, shell=True, close_fds=True)
            # stdout, stderr = command_execute.communicate()
            sleep(2)
            Popen("xdotool key alt+F11", shell=True)
        else:
            print("Recording stops")
            os.system("pkill libcamera-vid")
            self.recording = False

    def processVideo(self, channel):
        print("Recording stops in order to Process the Video")
        os.system("pkill libcamera-vid")
        self.recording = False
        # TODO: ffmpeg commands to process the video footage

    def picture_left(self):
        if (self.picture_index == 0):
            self.pictures = (len(self.saved_pictures) - 1)
        self.picture_index -= 1
        self.shown_picture = self.saved_pictures[self.picture_index]
        self.picture_gallery = Picture(
            self.gallery, width=360, height=270, image=self.shown_picture, grid=[1, 0])

    def picture_right(self):
        if (self.picture_index == (len(self.saved_pictures) - 1)):
            self.picture_index = 0
        self.picture_index += 1
        self.shown_picture = self.saved_pictures[self.picture_index]
        self.picture_gallery = Picture(
            self.gallery, width=360, height=270, image=self.shown_picture, grid=[1, 0])

    def show_gallery(self):
        self.gallery = Window(self.app, bg="white", height=300,
                              width=460, layout="grid", title="Gallery")
        self.saved_pictures = glob.glob('/home/pi/Downloads/*.jpg')
        self.shown_picture = self.saved_pictures[self.picture_index]
        button_left = PushButton(self.gallery, grid=[
                                 0, 0], width=40, height=50, pady=50, padx=10, image="/home/pi/Moment/icon/left.png", command=self.picture_left)
        self.picture_gallery = Picture(
            self.gallery, width=360, height=270, image=self.shown_picture, grid=[1, 0])
        button_right = PushButton(self.gallery, grid=[
                                  2, 0], width=40, height=50, pady=50, padx=10, image="/home/pi/Moment/icon/right.png", command=self.picture_right)
        self.gallery.show()

    def upload(self):
        self.show_busy()
        Popen(["bash", "/home/pi/Moment/usb_autorun.sh", "--yes"])
        self.hide_busy()


if __name__ == '__main__':
    standalone_app = Moment()
    standalone_app.run()
