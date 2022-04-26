#!/usr/bin/python3

from guizero import App, PushButton, Text, Picture, Window, PushButton
from time import sleep
import glob
import datetime
import sys
import os
import socket
from subprocess import PIPE, STDOUT, Popen, check_output, call
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import threading

class Moment(threading.Thread):
    def __init__(self):
        super().__init__()
        # Move Cursor out the way
        Popen("xdotool mousemove 480 480", shell=True)

        self.capture_number = self.timestamp()
        self.video_capture_number = self.timestamp()
        self.picture_index = 0
        self.saved_pictures = []
        self.shown_picture = ""
        self.recording = False
        self.config_recordinglocation = "/home/pi/Videos/"
        self.app = App(layout="grid", title="Camera Controls",
                       bg="black", width=480, height=480)
        self.busy = Window(self.app, bg="red",  height=240,
                           width=240, title="busy")
        self.app.tk.attributes("-fullscreen", True)
        self.app.tk.config(cursor="none")

        GPIO.setwarnings(False)  # Ignore warning for now
        GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            23, GPIO.FALLING, callback=self.uploadVideo, bouncetime=1000)
        GPIO.add_event_detect(
            24, GPIO.FALLING, callback=self.recordingControl, bouncetime=1000)

    def run(self):
        # Configure the Directory for the Videos
        Popen("rm -rf " + self.config_recordinglocation + "*", shell=True)
        Popen("mkdir -p " + self.config_recordinglocation, shell=True)

        # Pull all the Network Information
        gw = os.popen("ip -4 route show default").read().split()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((gw[2], 0))
        self.ipaddr = s.getsockname()[0]
        self.gateway = gw[2]
        self.host = socket.gethostname()
        self.ssid = os.popen("iwgetid -r").read()
        
        debugText = Text(self.app, color="white", grid=[
            0, 0], text="Network Information", size=40)

        hostText = Text(self.app, color="white", grid=[
            0, 1], text="HOST:" + str(self.host), size=29)

        ipText = Text(self.app, color="white", grid=[
            0, 2], text="IP:" + str(self.ipaddr), size=29)

        gatewayText = Text(self.app, color="white", grid=[
            0, 3], text="GW:" + str(self.gateway), size=29)

        ssidText = Text(self.app, color="white", grid=[
            0, 4], text="SSID:" + str(self.ssid), size=29)
        
        configText = Text(self.app, color="white", grid=[
            0, 5], text="CONFIG:", size=29)

        configTextIP = Text(self.app, color="white", grid=[
            0, 6], text="http://" + str(self.ipaddr) + ":80", size=29)

        self.busy.hide()
        t = threading.Thread(target=self.startVideo)
        t.start()

        self.app.display()

    def startVideo(self):
        self.recording = True
        capture_number = self.timestamp()
        sleep(2)
        Popen(
            "libcamera-vid -t 0 --qt-preview --hflip --vflip --autofocus --keypress -o /home/pi/Videos/%03d-"+str(capture_number)+".h264 --segment 10000 width 1920 --height 1080 ", stdout=PIPE, stdin=PIPE, stderr=STDOUT, shell=True, close_fds=True)
        sleep(1)
        Popen("xdotool key alt+F11", shell=True)

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
        print("[DEBUG]:Filename generated ...")
        return tstring.strftime("%Y%m%d_%H%M%S")

    def recordingControl(self, channel):
        if self.recording == False:
            print("[DEBUG]:Recording started")
            self.startVideo()
        else:
            print("[DEBUG]:Stopping Recording")
            Popen("pkill libcamera-vid", shell=True)
            self.recording = False

    def uploadVideo(self, channel):
        GPIO.remove_event_detect(23)
        GPIO.remove_event_detect(24)
        if self.recording == True:
            print("[DEBUG]:Recording stops in order to Upload the Video")
            Popen("pkill libcamera-vid", shell=True)
            self.recording = False
        else:
            print("[DEBUG]:Uploading Video")
        
        GPIO.add_event_detect(
            23, GPIO.FALLING, callback=self.uploadVideo, bouncetime=1000)
        GPIO.add_event_detect(
            24, GPIO.FALLING, callback=self.recordingControl, bouncetime=1000)

    def processVideo(self, channel):
        if self.recording == True:
            print("[DEBUG]:Recording stops in order to Process the Video")
            Popen("pkill libcamera-vid", shell=True)
            self.recording = False
        else:
            print("[DEBUG]:Processing Video")
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
        self.gallery = Window(self.app, bg="white", height=480,
                              width=480, layout="grid", title="Gallery")
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
    MomentApp = Moment()
    MomentApp.run()
