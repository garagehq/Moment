#!/usr/bin/python3

from guizero import App, PushButton, Text, Picture, Window
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
            23, GPIO.FALLING, callback=self.uploadVideo, bouncetime=2500)
        GPIO.add_event_detect(
            24, GPIO.FALLING, callback=self.recordingControl, bouncetime=2500)

    # def run(self):
        # capture_number = self.timestamp()
        self.recording = True


        # Configure the Directory for the Videos
        os.system("rm -rf " + self.config_recordinglocation + "*")
        os.system("mkdir -p " + self.config_recordinglocation)

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
        
        # self.app.display()

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

    def uploadVideo(self, channel):
        GPIO.remove_event_detect(23)
        if self.recording == True:
            print("Recording stops in order to Upload the Video")
            os.system("pkill libcamera-vid")
            self.recording = False
        else:
            print("Uploading Video")
        GPIO.add_event_detect(
            23, GPIO.FALLING, callback=self.uploadVideo, bouncetime=2500)

    def processVideo(self, channel):
        if self.recording == True:
            print("Recording stops in order to Process the Video")
            os.system("pkill libcamera-vid")
            self.recording = False
        else:
            print("Process Video")
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
    MomentApp.recording = True
    
    MomentApp.app.display()

    capture_number = MomentApp.timestamp()
    command_execute = Popen(
        "libcamera-vid -t 0 --qt-preview --hflip --vflip --autofocus --keypress -o /home/pi/Videos/%03d-"+str(capture_number)+".h264 --segment 10000 width 1920 --height 1080 ", stdout=PIPE, stdin=PIPE, stderr=STDOUT, shell=True, close_fds=True)
    # stdout, stderr = command_execute.communicate()
    sleep(2)
    Popen("xdotool key alt+F11", shell=True)

    # MomentApp.run()
    # MomentApp.join()
