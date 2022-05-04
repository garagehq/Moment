#!/usr/bin/python3

from guizero import App, Text, Window
from time import sleep
import urllib.request
import datetime
from os import popen, path
import socket
from subprocess import PIPE, STDOUT, Popen
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import threading

class Moment(threading.Thread):
    def __init__(self):
        super().__init__()
        print("\n[DEBUG] Time Start", self.timestamp())
        # Move Cursor out the way
        Popen(['xdotool', 'mousemove', '480', '480']).wait()
        # Close any lingering instance of libcamera-vid
        Popen(['pkill', 'libcamera-vid']).wait()
        # Close any lingering instance of arecord
        Popen(['pkill', 'arecord']).wait()

        self.recording = False
        self.start_time = 0
        
        # Load the Config File
        
        # Defaults
        self.config = {
            "audio" : 'False',
            "video": 'True',
            "raw_audio": 'False',
            "framerate": "30",
            "resolution": "1080p",
            "time_segment": 60,
            "recording_location": "/home/pi/Videos/",
            "full_raw_save_location": "/home/pi/Moment_Save/raw/",
            "moment_save_location": "/home/pi/Moment_Save/final/",
            "drive_location": "/home/pi/drive/Garage_Videos/",
            "log_location": "/home/pi/Moment_Save/logs/",
            "log": 'True',
            "orientation": "vertical"
        }
        
        self.resolution = {
            "1080p": {
                "width": "1920",
                "height": "1080"
            },
            "2.7k": {
                "width": "2704",
                "height": "1520"
            },
            "4k": {
                "width": "3840",
                "height": "2160"
            }
        }

        # Check to see if there is a config file, if not, use the defaults
        # TODO: Add a check to see if the config file is valid
        if path.exists("/home/pi/.config/Moment_Config.txt"):
            # load configuation variables
            print("[DEBUG]: Loading Config File")

        self.app = App(layout="grid", title="Camera Controls",
                       bg="black", width=480, height=480)

        # Make application fullscreen and remove the cursor
        self.app.tk.attributes("-fullscreen", True)
        self.app.tk.config(cursor="none")

        # Set up the GPIO pins
        self.gpio_setup()

    def gpio_setup(self):
        print("[DEBUG]:Add Event Detects")
        GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(3, GPIO.IN)
        GPIO.add_event_detect(
            23, GPIO.FALLING, callback=self.upload_moment, bouncetime=2000)
        GPIO.add_event_detect(
            24, GPIO.FALLING, callback=self.process_moment, bouncetime=1000)
        GPIO.add_event_detect(
            3, GPIO.FALLING, callback=self.config_menu, bouncetime=1000)
        print("[DEBUG]:Finish Adding Event Detects")

    def run(self):
        # Configure the Directory for the moments and clear out past unsaved moments
        Popen("rm -rf " + self.config["recording_location"] + "*", shell=True).wait()
        Popen(["mkdir",'-p', self.config["recording_location"]]).wait()
        Popen("rm -rf " + self.config["full_raw_save_location"] + "*", shell=True).wait()
        Popen(["mkdir", '-p', self.config["full_raw_save_location"]]).wait()
        Popen(["mkdir", '-p', self.config["moment_save_location"]]).wait()

        # Pull all the Network Information
        gw = popen("ip -4 route show default").read().split()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((gw[2], 0))
            self.ipaddr = s.getsockname()[0]
            self.gateway = gw[2]
            self.host = socket.gethostname()
            self.ssid = popen("iwgetid -r").read()
        except IndexError:
            self.ipaddr = "192.168.1.1"
            self.gateway = "192.168.1.1"
            self.ssid = "Mobile-AP"
            self.host = socket.gethostname()

        Text(self.app, color="white", grid=[
            0, 0], text="   Network Information", size=34)

        Text(self.app, color="white", grid=[
            0, 1], text="HOST:" + str(self.host), size=26)

        Text(self.app, color="white", grid=[
            0, 2], text="IP:" + str(self.ipaddr), size=26)

        Text(self.app, color="white", grid=[
            0, 3], text="GW:" + str(self.gateway), size=26)

        Text(self.app, color="white", grid=[
            0, 4], text="SSID:" + str(self.ssid.strip("\n")), size=26)

        Text(self.app, color="white", grid=[
            0, 5], text="CONFIG:", size=26)

        Text(self.app, color="white", grid=[
            0, 6], text="http://" + str(self.ipaddr) + ":8080", size=26)

        Text(self.app, color="white", grid=[
            0, 7], text="\n  Press (-) to Upload\n   Press (+) to Save Rec.", size=26)

        Text(self.app, color="white", grid=[
            0, 8], text="        (-)             (+)", size=35)

        t = threading.Thread(target=self.start_recording)
        t.start()

        self.app.display()

    def start_recording(self):
        if self.recording == False:
            self.recording = True
            print("[DEBUG]:Recording started")
            sleep(1.5)
            self.filename = self.timestamp()
            # get current time
            self.start_time = datetime.datetime.now()
            if self.config["audio"] == 'True':
                # Check for Audio USB Devices before starting arecord
                print(
                    "[DEBUG]: Checking Audio Hardware")
                audio_hardware = Popen('arecord  -l | grep "card 1"',stdout=PIPE, stderr=STDOUT, shell=True)
                stdout, stderr = audio_hardware.communicate()
                audio_hardware.wait()
                audio_hardware_string = stdout.rstrip().decode()
                print("[DEBUG:] Audio Device Status =", audio_hardware_string)
                if not audio_hardware_string:
                    print("[DEBUG]: No Audio Recording Device Present, turning audio recording off")
                    self.config["audio"] = 'False'
                else:
                    print("[DEBUG]:Start Audio Recording")
                    Popen("amixer set Capture 100%", shell=True).wait()
                    start_audio_command = "arecord "+ self.config["recording_location"] + str(self.filename) + ".wav"
                    Popen(start_audio_command, shell=True)
            if self.config["video"] == 'True':
                # Check to see if Video Hardware Works
                print(
                    "[DEBUG]: Checking Video Hardware")
                video_hardware = Popen(
                    'vcgencmd get_camera | grep "libcamera interfaces=1"', stdout=PIPE, stderr=STDOUT, shell=True)
                stdout, stderr = video_hardware.communicate()
                video_hardware.wait()
                video_hardware_string = stdout.rstrip().decode()
                print("[DEBUG:] Video Hardware Status =", video_hardware_string)
                if not video_hardware_string:
                    print("[DEBUG]: No Video Recording Hardware Present, turning video recording off")
                    self.config["video"] = 'False'
                else:
                    start_video_command = "libcamera-vid -t 0 --framerate " + self.config["framerate"] + " --qt-preview --hflip --vflip --autofocus -o " + self.config["recording_location"] + \
                        str(self.filename) + ".h264 --width " + \
                        self.resolution[self.config["resolution"]]["width"] + \
                        " --height "+ self.resolution[self.config["resolution"]]["height"]
                    print("[DEBUG]:Start Recording Command: " + start_video_command)
                    Popen(
                        start_video_command,
                        shell=True)
                    sleep(5)
                    Popen(['xdotool', 'key', 'alt+F11'])
            if self.config["video"] == 'False' and self.config["audio"] == 'False':
                print("[DEBUG]: No Moment Recording In Progress, Please Check Hardware")
                Text(self.app, color="red", grid=[
                    0, 7], text="\n  ERROR: Check Recording Hardware\n Or Config", size=22)
        else:
            print("[DEBUG]:Recording already in progress")

    # Generate timestamp string generating name for photos
    def timestamp(self):
        tstring = datetime.datetime.now()
        return tstring.strftime("%Y%m%d_%H%M%S")

    def upload(self):
        while True:
            if GPIO.input(23) == GPIO.LOW:
                sleep(1)
                Text(self.upload_window, color="white", grid=[
                    0, 6], text="Returning to Main Window", size=22)
                self.upload_window.update()
                sleep(2)
                print("[DEBUG]:Exiting Upload Window")
                print("[DEBUG]:Hiding Upload Window")
                self.upload_window.hide()
                sleep(2)
                return

            elif GPIO.input(24) == GPIO.LOW:
                # Check to see if device is connected to the internet
                print("[DEBUG]:Checking for Internet Connection")
                try:
                    response = urllib.request.urlopen('http://www.google.com')
                    print("[DEBUG]:Internet Connection Found")
                except:
                    print("[DEBUG]:No Internet Connection Found")
                    Text(self.upload_window, color="red", grid=[
                        0, 5], text="ERROR:No Internet Connection", size=22)
                    self.upload_window.update()
                    sleep(1)
                    Text(self.upload_window, color="white", grid=[
                        0, 6], text="Connect via config server & try again", size=20)
                    self.upload_window.update()
                    sleep(2)
                    Text(self.upload_window, color="white", grid=[
                        0, 7], text="Returning to Main Window", size=22)
                    self.upload_window.update()
                    sleep(2)
                    print("[DEBUG]:Hiding Upload Window")
                    self.upload_window.hide()

                    if self.recording == True:
                        print("[DEBUG]:Recording stops in order to show Main Menu")
                        self.kill_recording()
                        self.recording = False
                        sleep(4)
                        print("[DEBUG]: Restarting Recording")
                        t = threading.Thread(target=self.start_recording)
                        t.start()
                        sleep(2)
        
                    return

                if self.recording == True:
                    print("[DEBUG]:Recording stops in order to Upload the Moment")
                    self.kill_recording()
                    self.recording = False
                else:
                    print("[DEBUG]:Uploading Moment")

                sleep(1)
                Text(self.upload_window, color="white", grid=[
                    0, 4], text="Upload Started", size=24)
                self.upload_window.update()
                
                # Check to see if drive is mounted
                if path.ismount(self.config["drive_location"]):
                    upload_recording_command = "rsync -avzP --update --append --remove-source-files" + \
                        str(self.config["moment_save_location"]
                            ) + str(self.config["drive_location"])
                    print("[DEBUG]:Upload Moment Command: " +
                        upload_recording_command)
                    upload_recording = Popen(['rsync', '-avzP', '--update', '--append', '--remove-source-files',
                                            self.config["moment_save_location"], self.config["drive_location"]])
                    upload_recording.wait()
                    sleep(2)
                else:
                    print("[DEBUG]:No Drive Mounted, Please Mount Drive")
                    Text(self.upload_window, color="red", grid=[
                        0, 5], text="ERROR:No Drive Mounted", size=22)
                    self.upload_window.update()
                    sleep(1)
                    Text(self.upload_window, color="white", grid=[
                        0, 6], text="Fix via config server and try again", size=20)
                    self.upload_window.update()
                    sleep(1)
                    Text(self.upload_window, color="white", grid=[
                        0, 6], text="Returning to Main Window", size=22)
                    self.upload_window.update()
                    sleep(2)
                    print("[DEBUG]:Hiding Upload Window")
                    self.upload_window.hide()
                    return

                Text(self.upload_window, color="green", grid=[
                    0, 5], text="Upload Finished!", size=24)
                self.upload_window.update()
                sleep(1)
                Text(self.upload_window, color="white", grid=[
                    0, 6], text="Returning to Main Window", size=22)
                self.upload_window.update()
                sleep(2)


                print("[DEBUG]:Hiding Upload Window")
                self.upload_window.hide()
                # At the end, Restart Recording
                print("[DEBUG]: Restarting Recording")
                t = threading.Thread(target=self.start_recording)
                t.start()
                sleep(2)

                return

    def upload_moment(self, channel):
        GPIO.remove_event_detect(23)
        GPIO.remove_event_detect(24)
        print("[DEBUG]:Upload Moment")

        self.upload_window = Window(self.app, bg="black", height=480,
                                   width=480, layout="grid", title="Upload Moment(s)")
        self.upload_window.tk.attributes("-fullscreen", True)
        Text(self.upload_window, color="white", grid=[
            0, 0], text="  Uploading Moment", size=40)
        Text(self.upload_window, color="white", grid=[
            0, 1], text="  [Press (-) to Return]", size=28)
        Text(self.upload_window, color="white", grid=[
            0, 2], text="  [Press (+) to Upload]", size=28)

        self.upload_window.show()
        
        sleep(1)

        self.upload()

        print("[DEBUG]:Reset GPIO Interrupts")
        GPIO.cleanup()
        t = threading.Thread(target=self.gpio_setup)
        t.start()

    def kill_recording(self):
        print("[DEBUG]:Killing Recording...")
        if self.config["video"] == 'True':
            print("[DEBUG]:Killing Video...")
            Popen(['pkill', 'libcamera-vid']).wait()
        if self.config["audio"] == 'True':
            print("[DEBUG]:Killing Audio...")
            Popen(['pkill', 'arecord']).wait()
        return

    # Button Logic If GPIO 23 is pressed, then increase the time counter and if GPIO 24 is pressed, then decrease the time counter but if they both are pressed, then process the Recording
    def process_moment_button_logic(self):
        processFlag = False
        changed = False
        return_hold = 0
        while True:
            if GPIO.input(23) == GPIO.LOW and GPIO.input(24) == GPIO.LOW:
                # Process
                processFlag = True
                sleep(0.2)
                print("[DEBUG]:Begin Processing Recording using ffmpeg")
            elif GPIO.input(24) == GPIO.LOW:
                return_hold = 0
                # get end time
                end_time = datetime.datetime.now()
                # Calculate the difference between the start and end time in minutes
                diff = end_time - self.start_time
                diff_segment = diff.seconds / self.config["time_segment"]
                print("[DEBUG]:Full Recording Duration: " +
                      str(diff_segment) + " minutes")
                # If the difference is greater than the threshold, then process the video
                if diff_segment > self.time_counter:
                    self.time_counter += 1
                    changed = True
                    sleep(0.2)
                    print("[DEBUG]: Time Counter = " + str(self.time_counter))
            elif GPIO.input(23) == 0:
                if self.time_counter != 0:
                    self.time_counter -= 1
                    changed = True
                    return_hold = 0
                    sleep(0.2)
                    print("[DEBUG]: Time Counter = " + str(self.time_counter))
                else:
                    return_hold += 1
                    print("[DEBUG]:Return Hold Counter = ", return_hold)
                    sleep(0.5)
                    if return_hold > 4:
                        print("[DEBUG]:Returning Back to the Main Menu due to Press and Hold")
                        processFlag = True
                        return_hold = 0
            
            sleep(0.3)
            
            if changed == True:
                Text(self.process_window, color="white", grid=[
                        0, 1], text=str(self.time_counter) + " mins", size=29)
                self.process_window.update()
                changed = False

            if processFlag == True:
                if self.time_counter == 0:
                    print("[DEBUG]:Returning to Main Menu")
                    Text(self.process_window, color="white", grid=[
                        0, 3], text="Returning to Main Menu", size=29)
                    self.process_window.update()
                    sleep(2)
                    print("[DEBUG]:Hiding Process Window")
                    self.process_window.hide()
                    return
                
                if self.recording == True:
                    print("[DEBUG]:Recording stops in order to Process the Recordings")
                    self.kill_recording()
                    self.recording = False

                Text(self.process_window, color="white", grid=[
                    0, 3], text="[--PROCESSING--]", size=29)
                self.process_window.update()

                sleep(2)
                
                if self.config["audio"] == 'True' and self.config["video"] == 'False':
                    print("[DEBUG]:Processing Audio Only")
                    print("[DEBUG]:Cutting the .wav using ffmpeg while transcoding to .mp3")
                    cutting_audio = "ffmpeg -v debug -sseof -" + str(self.time_counter * self.config["time_segment"]) + " -i " + str(self.config["recording_location"]) + str(
                        self.filename) + ".wav -vn -ar 44100 -ac 2 -b:a 192k" + str(self.config["moment_save_location"]) + str(self.filename) + ".mp3"
                    print("[DEBUG] Cutting .wav while transcoding to .mp3 Command: " +
                          cutting_audio)
                    split_audio = Popen(
                        ['ffmpeg', '-v', 'debug', '-sseof', '-'+str(self.time_counter * self.config["time_segment"]), '-i', str(self.config["recording_location"]) + str(
                            self.filename) + '.wav', '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', str(self.config["moment_save_location"]) + str(self.filename) + '.mp3'])
                    split_audio.wait()
                    print("[DEBUG]:Audio Moment Processed and move to " +
                          str(self.config["moment_save_location"]) + '.mp3')
                    if self.config["raw_audio"] == 'False':
                        # ffmpeg -i <input_file> -af "highpass=f=200, lowpass=f=3000" <output_file>
                        self.filename += ".adj"
                        process_audio = "ffmpeg -i " + str(self.config["moment_save_location"]) + str(
                            self.filename) + ".mp3" + ' -af "highpass=f=200, lowpass=f=3000" ' + str(self.config["moment_save_location"]) + str(self.filename) + ".mp3"
                        print("[DEBUG] Adjusting Audio Quality: " +
                              process_audio)
                        process_audio = Popen(
                            ['ffmpeg', '-i', str(self.config["moment_save_location"]) + str(self.filename) + ".mp3", '-af', 'highpass=f=200, lowpass=f=3000', str(self.config["moment_save_location"]) + str(self.filename) + ".mp3"])
                        process_audio.wait()
                    Text(self.process_window, color="green", grid=[
                        0, 4], text="-Finished Audio Processing", size=22)
                    self.process_window.update()
                    sleep(1)
                    Text(self.process_window, color="white", grid=[
                        0, 6], text="Returning to Main Window", size=22)
                    Text(self.process_window, color="white", grid=[
                        0, 7], text="and Restarting Recording", size=22)
                    self.process_window.update()

                elif self.config["video"] == 'True':
                    print("[DEBUG]:Processing Video ")
                    print("[DEBUG]:Process .h264 raw video using  into an .mp4")
                    raw_conversation_command = "ffmpeg -v debug -framerate " + str(self.config["framerate"]) + " -i " + str(self.config["recording_location"]) + str(
                        self.filename) + ".h264 -c copy " + str(self.config["full_raw_save_location"]) + str(self.filename) + ".mp4"
                    print("[DEBUG] Process Video Conversion Command: " + raw_conversation_command)
                    create_mp4 = Popen(
                        ['ffmpeg', '-v','debug', '-framerate', str(self.config["framerate"]), '-i', str(self.config["recording_location"]) + str(
                            self.filename) + '.h264', '-c', 'copy', str(self.config["full_raw_save_location"]) + str(self.filename) + '.mp4'])
                    create_mp4.wait()

                    Text(self.process_window, color="green", grid=[
                        0, 4], text="-Finished Raw Video Processing", size=22)
                    self.process_window.update()
                    sleep(1)

                    # TODO: Merge Audio and Video
                    if self.config["audio"] == 'True':
                        print("[DEBUG]:Merging Audio and Video")
                        
                        if self.config["raw_audio"] == 'False':
                            # ffmpeg -i <input_file> -af "highpass=f=200, lowpass=f=3000" <output_file>
                            process_audio = "ffmpeg -i " + str(self.config["recording_location"]) + str(
                                self.filename) + ".mp3" + ' -af "highpass=f=200, lowpass=f=3000" ' + str(self.config["moment_save_location"]) + str(self.filename) + ".mp3"
                            print("[DEBUG] Adjusting Audio Quality: " +
                                process_audio)
                            process_audio = Popen(
                                ['ffmpeg', '-i', str(self.config["moment_save_location"]) + str(self.filename) + ".mp3", '-af', 'highpass=f=200, lowpass=f=3000', str(self.config["moment_save_location"]) + str(self.filename) + ".mp3"])
                            process_audio.wait()
                        else:
                            print("[DEBUG]:Using Raw Audio Quality")
                        

                    print("[DEBUG]:Cutting the Proccessed .mp4 Video using ffmpeg")
                    cutting_processed_video = "ffmpeg -v debug -sseof -" + str(self.time_counter * self.config["time_segment"]) + " -i " + str(self.config["full_raw_save_location"]) + str(
                        self.filename) + ".mp4 -c copy" + str(self.config["moment_save_location"]) + str(self.filename) + ".mp4"
                    print("[DEBUG] Cutting Processed Video Command: " +
                        cutting_processed_video)
                    splitMp4 = Popen(
                        ['ffmpeg', '-v', 'debug', '-sseof', '-'+str(self.time_counter * self.config["time_segment"]), '-i', str(self.config["full_raw_save_location"]) + str(
                            self.filename) + '.mp4', "-c", "copy", str(self.config["moment_save_location"]) + str(self.filename) + '.mp4'])
                    splitMp4.wait()

                    Text(self.process_window, color="green", grid=[
                        0, 5], text="-Finished Video Splitting", size=22)
                    self.process_window.update()
                    sleep(1)

                    print("[DEBUG]:Finished Processing Video, "+
                          str(self.filename)+".mp4 saved to "+self.config["full_raw_save_location"])

                    Text(self.process_window, color="white", grid=[
                        0, 6], text="Returning to Main Window", size=22)
                    Text(self.process_window, color="white", grid=[
                        0, 7], text="and Restarting Recording", size=22)
                    self.process_window.update()

                sleep(2)
                print("[DEBUG]:Hiding Process Window")
                self.process_window.hide()
                # At the end, Restart Recording
                print("[DEBUG]:Restarting Recording")
                t = threading.Thread(target=self.start_recording)
                t.start()
                sleep(2)

                return

    def process_moment(self, channel):
        GPIO.remove_event_detect(23)
        GPIO.remove_event_detect(24)

        # get end time
        end_time = datetime.datetime.now()
        # Calculate the difference between the start and end time in minutes
        diff = end_time - self.start_time
        diff_segment = diff.seconds / self.config["time_segment"]

        print("[DEBUG]:Full Moment Duration: " +
              str(diff_segment) + " minutes")
        # If the difference is greater than the threshold, then process the Moment differently
        if diff_segment > 20:
            self.time_counter = 5
            print("[DEBUG]:Very Long Moment, Defaulting Minute Counter to 5")
        elif diff_segment > 5:
            self.time_counter = 3
            print("[DEBUG]:Long Moment, Defaulting Minute Counter to 3")
        else:
            print("[DEBUG]:Short Moment, Defaulting Minute Counter to 1")
            self.time_counter = 1

        self.process_window = Window(self.app, bg="black", height=480,
                              width=480, layout="grid", title="Process Moment")
        self.process_window.tk.attributes("-fullscreen", True)

        Text(self.process_window, color="white", grid=[
            0, 0], text="Process Moment", size=38)
        Text(self.process_window, color="white", grid=[
            0, 1], text=str(self.time_counter) + " mins", size=29)
        Text(self.process_window, color="white", grid=[
            0, 2], text="[Press Both Buttons to Confirm]", size=24)
        
        self.process_window.show()
        
        sleep(1)

        self.process_moment_button_logic()

        print("[DEBUG]:Reset GPIO Interrupts")
        GPIO.cleanup()
        t = threading.Thread(target=self.gpio_setup)
        t.start()
        
    def config_menu(self):
        print("[DEBUG]:Opening Config Menu")
        sleep(1)


if __name__ == '__main__':
    MomentApp = Moment()
    MomentApp.run()
