#!/usr/bin/python3

from guizero import App, Text, Window
from time import sleep
import glob
import datetime
import sys
import os
import socket
from subprocess import PIPE, STDOUT, Popen, check_output, call
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import threading
import signal

class Moment(threading.Thread):
    def __init__(self):
        super().__init__()
        print("[DEBUG] Time Start", self.timestamp())
        # Move Cursor out the way
        Popen("xdotool mousemove 480 480", shell=True)
        # Close any lingering instance of libcamera-vid
        Popen("pkill libcamera-vid", shell=True)

        self.recording = False
        self.startTime = 0
        self.endTime = 0
        
        # Load the Config File
        self.config_audio = False
        self.config_video = True
        self.config_framerate = "30"
        self.config_timesegment = 60
        self.config_recordinglocation = "/home/pi/Videos/"
        self.config_fullRawSaveLocation = "/home/pi/Moment_Save/raw/"
        self.config_momentSaveLocation = "/home/pi/Moment_Save/final/"
        self.config_drivelocation = "/home/pi/drive/Garage_Videos/"
        self.config_loglocation = " /home/pi/Moment.log"
        self.config_logcommand = " 2>&1 " + self.config_loglocation
        self.config_log = True

        self.app = App(layout="grid", title="Camera Controls",
                       bg="black", width=480, height=480)

        # Make application fullscreen and remove the cursor
        self.app.tk.attributes("-fullscreen", True)
        self.app.tk.config(cursor="none")

        # Set up the GPIO pins
        self.gpio_setup()

    def gpio_setup(self):
        print("[DEBUG]:Add Event Detects")
        GPIO.setwarnings(False)  # Ignore warning for now
        GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            23, GPIO.FALLING, callback=self.uploadMoment, bouncetime=2000)
        GPIO.add_event_detect(
            24, GPIO.FALLING, callback=self.processMoment, bouncetime=1000)
        print("[DEBUG]:Finish Adding Event Detects")

    def run(self):
        # Configure the Directory for the Videos
        Popen("rm -rf " + self.config_recordinglocation + "*", shell=True)
        Popen("mkdir -p " + self.config_recordinglocation, shell=True)
        Popen("mkdir -p " + self.config_fullRawSaveLocation, shell=True)
        Popen("mkdir -p " + self.config_momentSaveLocation, shell=True)

        # Pull all the Network Information
        gw = os.popen("ip -4 route show default").read().split()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((gw[2], 0))
            self.ipaddr = s.getsockname()[0]
            self.gateway = gw[2]
            self.host = socket.gethostname()
            self.ssid = os.popen("iwgetid -r").read()
        except IndexError:
            self.ipaddr = "192.168.1.1"
            self.gateway = "192.168.1.1"
            self.ssid = "Mobile-AP"
            self.host = socket.gethostname()

        debugText = Text(self.app, color="white", grid=[
            0, 0], text="Network Information", size=38)

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

        t = threading.Thread(target=self.startRecording)
        t.start()

        self.app.display()

    def startRecording(self):
        if self.recording == False:
            self.recording = True
            print("[DEBUG]:Recording started")
            sleep(1.5)
            self.filename = self.timestamp()
            # get current time
            self.startTime = datetime.datetime.now()
            start_recording_command = "libcamera-vid -t 0 --qt-preview --hflip --vflip --autofocus -o " + self.config_recordinglocation + str(self.filename) + ".h264 --width 1920 --height 1080 "
            print("[DEBUG]:Start Recording Command: " + start_recording_command)
            Popen(
                start_recording_command,
                shell=True)
            sleep(4)
            Popen("DISPLAY=:0 xdotool key alt+F11", shell=True)
        else:
            print("[DEBUG]:Recording already in progress")

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
        return tstring.strftime("%Y%m%d_%H%M%S")

    def upload(self):
        while True:
            if GPIO.input(23) == GPIO.LOW:
                sleep(1)
                self.helpText = Text(self.uploadWindow, color="white", grid=[
                    0, 6], text="Returning to Main Window", size=22)
                self.uploadWindow.update()
                sleep(2)
                print("[DEBUG]:Exiting Upload Window")
                print("[DEBUG]:Hiding Upload Window")
                self.uploadWindow.hide()
                
                sleep(2)

                return

            elif GPIO.input(24) == GPIO.LOW:
                if self.recording == True:
                    print("[DEBUG]:Recording stops in order to Upload the Video")
                    Popen("pkill libcamera-vid", shell=True)
                    self.recording = False
                else:
                    print("[DEBUG]:Uploading Video")
                sleep(1)
                self.helpText = Text(self.uploadWindow, color="white", grid=[
                    0, 4], text="Upload Started", size=24)
                self.uploadWindow.update()
                upload_recording_command = "cp -rf" + self.config_momentSaveLocation + \
                    "* " + self.config_drivelocation
                print("[DEBUG]:Upload Video Command: " +
                      upload_recording_command)
                #upload_recording = Popen(
                #    ['sudo','cp', '-rf', self.config_momentSaveLocation + "*-final.mp4", self.config_drivelocation])
                upload_recording = Popen(['rsync', '-avz', '--progress', '--partial',
                                         self.config_momentSaveLocation, self.config_drivelocation])
                # rsync -avz --progress --partial self.config_momentSaveLocation+*-final.mp4 self.config_drivelocation
                upload_recording.wait()
                sleep(2)

                self.helpText = Text(self.uploadWindow, color="white", grid=[
                    0, 5], text="Upload Finished!", size=24)
                self.uploadWindow.update()
                sleep(1)
                self.helpText = Text(self.uploadWindow, color="white", grid=[
                    0, 6], text="Returning to Main Window", size=22)
                self.uploadWindow.update()
                sleep(2)

                # remove_video_command = "rm -rf " + self.config_momentSaveLocation + "*"
                # print("[DEBUG]:Remove Video Command: " + remove_video_command)
                # remove_video = Popen(remove_video_command, shell=True)
                # remove_video.wait()

                print("[DEBUG]:Hiding Upload Window")
                self.uploadWindow.hide()
                # At the end, Restart Recording
                print("[DEBUG]: Restarting Recording")
                t = threading.Thread(target=self.startRecording)
                t.start()
                sleep(2)

                return

    def uploadMoment(self, channel):
        GPIO.remove_event_detect(23)
        GPIO.remove_event_detect(24)
        print("[DEBUG]:Upload Moment")

        self.uploadWindow = Window(self.app, bg="black", height=480,
                                    width=480, layout="grid", title="Upload Video(s)")
        self.uploadWindow.tk.attributes("-fullscreen", True)
        tileText = Text(self.uploadWindow, color="white", grid=[
            0, 0], text="  Uploading Video", size=40)
        self.helpText = Text(self.uploadWindow, color="white", grid=[
            0, 1], text="  [Press - to return]", size=28)
        self.helpText = Text(self.uploadWindow, color="white", grid=[
            0, 2], text="  [Press + to Upload]", size=28)

        self.uploadWindow.show()
        
        sleep(1)

        self.upload()

        print("[DEBUG]:Reset GPIO Interrupts")
        GPIO.cleanup()
        t = threading.Thread(target=self.gpio_setup)
        t.start()


    def buttonLogic(self):
        # Button Logic If GPIO 23 is pressed, then increase the minute counter and if GPIO 24 is pressed, then decrease the minute counter but if they both are pressed, then process the video
        processFlag = False
        changed = False
        while True:
            if GPIO.input(23) == GPIO.LOW and GPIO.input(24) == GPIO.LOW:
                # Process
                processFlag = True
                sleep(0.2)
                print("[DEBUG]:Begin Processing Video using ffmpeg")
            elif GPIO.input(24) == GPIO.LOW:
                # get end time
                self.endTime = datetime.datetime.now()
                # Calculate the difference between the start and end time in minutes
                self.diff = self.endTime - self.startTime
                self.diff_segment = self.diff.seconds / self.config_timesegment
                print("[DEBUG]:Full Video Duration: " +
                      str(self.diff_segment) + " minutes")
                # If the difference is greater than the threshold, then process the video
                if self.diff_segment > self.time_counter:
                    self.time_counter += 1
                    changed = True
                    sleep(0.2)
                    print("[DEBUG]: Time Counter = " + str(self.time_counter))
            elif GPIO.input(23) == 0:
                if self.time_counter != GPIO.LOW:
                    self.time_counter -= 1
                    changed = True
                    sleep(0.2)
                    print("[DEBUG]: Time Counter = " + str(self.time_counter))
            if changed == True:
                self.minText = Text(self.processWindow, color="white", grid=[
                        0, 1], text=str(self.time_counter) + " mins", size=29)
                self.processWindow.update()
                changed = False
        
            sleep(0.2)

            if processFlag == True:
                if self.time_counter == 0:
                    print("[DEBUG]:Returning to Main Menu")
                    self.helpText = Text(self.processWindow, color="white", grid=[
                        0, 2], text="Returning to Main Menu", size=29)
                    self.processWindow.update()
                    sleep(2)
                    print("[DEBUG]:Hiding Process Window")
                    self.processWindow.hide()
                    return
                
                if self.config_audio == True and self.config_video == False:
                    print("[DEBUG]:Processing Audio Only")
                    # TODO: Add Audio Only Logic
                elif self.config_video == True:
                    if self.recording == True:
                        print("[DEBUG]:Recording stops in order to Process the Video")
                        Popen("pkill libcamera-vid", shell=True)
                        self.recording = False
                    else:
                        print("[DEBUG]:Processing Video")

                    self.helpText = Text(self.processWindow, color="white", grid=[
                        0, 3], text="[--PROCESSING--]", size=29)
                    self.processWindow.update()

                    sleep(2)

                    print("[DEBUG]:Process .h264 raw video using  into an .mp4")
                    Popen(
                        "echo $(date) [DEBUG]:Process .h264 raw video using  into an .mp4", shell=True)
                    raw_conversation_command = "ffmpeg -v debug -framerate " + str(self.config_framerate) + " -i " + str(self.config_recordinglocation) + str(
                        self.filename) + ".h264 -c copy " + str(self.config_fullRawSaveLocation) + str(self.filename) + ".mp4"
                    print("[DEBUG] Process Video Conversion Command: " + raw_conversation_command)
                    # createMp4 = Popen(raw_conversation_command,
                    #     shell=True)
                    createMp4 = Popen(
                        ['ffmpeg', '-v','debug', '-framerate', str(self.config_framerate), '-i', str(self.config_recordinglocation) + str(
                            self.filename) + '.h264', '-c', 'copy', str(self.config_fullRawSaveLocation) + str(self.filename) + '.mp4'])
                    createMp4.wait()

                    # sleep(30)
                    
                    self.helpText = Text(self.processWindow, color="white", grid=[
                        0, 4], text="-Finished Raw Video Processing", size=22)
                    self.processWindow.update()
                    sleep(1)

                    # TODO: Merge Audio and Video
                    if self.config_audio == True:
                        print("[DEBUG]:Merging Audio and Video")

                    print("[DEBUG]:Cutting the Proccessed .mp4 Video using ffmpeg")
                    Popen(
                        "echo $(date) [DEBUG]:Cutting the Proccessed .mp4 Video using ffmpeg", shell=True)
                    cutting_processed_video = "ffmpeg -v debug -sseof -" + str(self.time_counter * self.config_timesegment) + " -i " + str(self.config_fullRawSaveLocation) + str(
                        self.filename) + ".mp4 -c copy" + str(self.config_momentSaveLocation) + str(self.filename) + ".mp4"
                    print("[DEBUG] Cutting Processed Video Command: " +
                        cutting_processed_video)
                    # splitMp4 = Popen(cutting_processed_video,
                        # shell=True)
                    splitMp4 = Popen(
                        ['ffmpeg', '-v', 'debug', '-sseof', '-'+str(self.time_counter * self.config_timesegment), '-i', str(self.config_fullRawSaveLocation) + str(
                            self.filename) + '.mp4', "-c", "copy", str(self.config_momentSaveLocation) + str(self.filename) + '.mp4'])
                    splitMp4.wait()

                    # sleep(30)

                    self.helpText = Text(self.processWindow, color="white", grid=[
                        0, 5], text="-Finished Video Splitting", size=22)
                    self.processWindow.update()
                    sleep(1)

                    print("[DEBUG]:Finished Processing Video, "+
                          str(self.filename)+"-final.mp4 saved to "+self.config_fullRawSaveLocation)
                    Popen(
                        "echo $(date) [DEBUG]:Finished Processing Video, " +
                        str(self.filename)+"-final.mp4 saved to "+self.config_fullRawSaveLocation, shell=True)

                    self.helpText = Text(self.processWindow, color="white", grid=[
                        0, 6], text="Returning to Main Window", size=22)
                    self.helpText = Text(self.processWindow, color="white", grid=[
                        0, 7], text="and Restarting Recording", size=22)
                    self.processWindow.update()

                    sleep(2)
                    print("[DEBUG]:Hiding Process Window")
                    self.processWindow.hide()
                    # At the end, Restart Recording
                    print("[DEBUG]: Restarting Recording")
                    t = threading.Thread(target=self.startRecording)
                    t.start()
                    sleep(2)
                return

    def processMoment(self, channel):
        GPIO.remove_event_detect(23)
        GPIO.remove_event_detect(24)

        # get end time
        self.endTime = datetime.datetime.now()
        # Calculate the difference between the start and end time in minutes
        self.diff = self.endTime - self.startTime
        self.diff_segment = self.diff.seconds / self.config_timesegment

        print("[DEBUG]:Full Video Duration: " +
              str(self.diff_segment) + " minutes")
        # If the difference is greater than the threshold, then process the video differently
        if self.diff_segment > 20:
            self.time_counter = 5
            print("[DEBUG]:Very Long Video, Defaulting Minute Counter to 5")
        elif self.diff_segment > 5:
            self.time_counter = 3
            print("[DEBUG]:Long Video, Defaulting Minute Counter to 3")
        else:
            print("[DEBUG]:Short Video, Defaulting Minute Counter to 1")
            self.time_counter = 1

        self.processWindow = Window(self.app, bg="black", height=480,
                              width=480, layout="grid", title="Process Recording")
        self.processWindow.tk.attributes("-fullscreen", True)

        tileText = Text(self.processWindow, color="white", grid=[
            0, 0], text="Process Recording", size=38)
        self.minText = Text(self.processWindow, color="white", grid=[
            0, 1], text=str(self.time_counter) + " mins", size=29)
        self.helpText = Text(self.processWindow, color="white", grid=[
            0, 2], text="[Press Both Buttons to Confirm]", size=24)
        
        self.processWindow.show()
        
        sleep(1)

        self.buttonLogic()

        print("[DEBUG]:Reset GPIO Interrupts")
        GPIO.cleanup()
        t = threading.Thread(target=self.gpio_setup)
        t.start()


if __name__ == '__main__':
    MomentApp = Moment()
    MomentApp.run()
