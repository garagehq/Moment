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
import subprocess
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library


class Moment:
    def __init__(self):
        self.capture_number = self.timestamp()
        self.video_capture_number = self.timestamp()
        self.picture_index = 0
        self.saved_pictures = []
        self.shown_picture = ""
        self.recording = False

        GPIO.setwarnings(False)  # Ignore warning for now
        GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            23, GPIO.FALLING, callback=self.recordingControl, bouncetime=2500)

        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            24, GPIO.FALLING, callback=self.processVideo, bouncetime=2500)

        self.app = App(layout="grid", title="Camera Controls",
                       bg="black", width=480, height=320)

       
        gw = os.popen("ip -4 route show default").read().split()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((gw[2], 0))
        ipaddr = s.getsockname()[0]
        gateway = gw[2]
        host = socket.gethostname()
        ssid = os.popen("iwgetid -r").read().split()
        

        text0 = Text(self.app, color="white", grid=[1, 0], text="- Moment -")

        button1 = PushButton(self.app, grid=[3, 1], width=110, height=110, pady=35,
                             padx=10, image="/home/pi/Moment/icon/prev.png", command=self.long_preview)
        text1 = Text(self.app, color="white", grid=[
                     3, 2], text="Hostname: " + str(host))

        button2 = PushButton(self.app, grid=[3, 3], width=110, height=110, pady=35,
                             padx=10, image="/home/pi/Moment/icon/gallery.png", command=self.show_gallery)
        text2 = Text(self.app, color="white", grid=[3, 4], text="IP: " + str(ipaddr))

        button3 = PushButton(self.app, grid=[3, 5], width=110, height=110,  pady=35,
                             padx=10, image="/home/pi/Moment/icon/vid.png", command=self.video_capture)
        text2 = Text(self.app, color="white", grid=[3, 6], text="GW: " + str(gateway))

        button4 = PushButton(self.app, grid=[3, 7], width=110, height=110, pady=35,
                             padx=10, image="/home/pi/Moment/icon/lapse.png", command=self.burst)
        text3 = Text(self.app, color="white", grid=[3, 8], text="SSID:" + str(ssid))

        self.busy = Window(self.app, bg="red",  height=175,
                           width=480, title="busy")

        self.app.tk.attributes("-fullscreen", True)
        self.busy.hide()
        os.system("rm -rf /home/pi/Videos/*")
        self.app.display()

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

    def burst(self):
        self.show_busy()
        capture_number = self.timestamp()
        print("Raspistill starts")
        os.system("raspistill -t 10000 -tl 0 --thumb none -n -bm -o /home/pi/Downloads/BR" +
                  str(capture_number) + "%04d.jpg")
        print("Raspistill done")
        self.hide_busy()

    def split_hd_30m(self):
        self.show_busy()
        capture_number = self.timestamp()
        print("Raspivid starts")
        os.system("raspivid -f -t 1800000 -sg 300000  -o /home/pi/Downloads/" +
                  str(capture_number) + "vid%04d.h264")
        print("done")
        self.hide_busy()

    def lapse(self):
        self.show_busy()
        capture_number = self.timestamp()
        print("Raspistill timelapse starts")
        os.system("raspistill -t 3600000 -tl 60000 --thumb none -n -bm -o /home/pi/Downloads/TL" +
                  str(capture_number) + "%04d.jpg")
        print("Raspistill timelapse done")
        self.hide_busy()

    def long_preview(self):
        self.show_busy()
        print("15 second preview")
        os.system("raspistill -f -t 15000")
        self.hide_busy()

    def capture_image(self):
        self.show_busy()
        capture_number = self.timestamp()
        print("Raspistill starts")
        os.system("raspistill -f -o /home/pi/Downloads/" +
                  str(capture_number) + "cam.jpg")
        print("Raspistill done")
        self.hide_busy()

    def recordingControl(self, channel):
        print("Button 23 event callback")
        if self.recording == False:
            self.recording = True
            capture_number = self.timestamp()
            print("Recording starts")
            command_execute = Popen(
                "libcamera-vid -t 0 --qt-preview --hflip --vflip --autofocus --keypress -o /home/pi/Videos/%03d-"+str(capture_number)+".h264 --segment 10000 width 1920 --height 1080 ", stdout=PIPE, stdin=PIPE, stderr=STDOUT, shell=True, close_fds=True)
            # stdout, stderr = command_execute.communicate()
            sleep(2)
            Popen("xdotool key alt+F11", shell=True)
        else:
            os.system("pkill libcamera-vid")
            print("Recording stops")
            self.recording = False

    def processVideo(self, channel):
        print("Button 24 event callback")
        os.system("pkill libcamera-vid")
        self.recording = False
        print("Recording stops")
        # TODO: ffmpeg commands to process the video footage
        print("Process Video")

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

    def video_capture(self):
        self.show_busy()
        capture_number = self.timestamp()
        print("Raspivid starts")
        os.system("raspivid -f -t 30000 -o /home/pi/Downloads/" +
                  str(capture_number) + "vid.h264")
        print("done")
        self.hide_busy()

    def upload(self):
        self.show_busy()
        subprocess.Popen(["bash", "/home/pi/Moment/usb_autorun.sh", "--yes"])
        self.hide_busy()


if __name__ == '__main__':
    standalone_app = Moment()
    standalone_app.run()
