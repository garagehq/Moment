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
import sys
import cgi
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

##############################################################################################
# [TODO]: Add an interrupt button(PiSugar) to refocus
# [TODO]: Add an interrupt button(PiSugar) to toggle the main menu dislay
# [TODO]: After Webserver Change, restart the recording
# [TODO]: Battery Percentage on Main Menu
# [TODO]: Create the Custom Enclosure

#
# The following command gets the video preview working as well as orients it correctly and sets the resolution to 1080 HD
# libcamera-vid -t 0 --qt-preview --hflip --vflip --autofocus --keypress -o <FILENAME>.h264  width 1920 --height 1080 & sleep 2 && xdotool key alt+F11
# with keypress enabled, everytime you press "f" and then enter in the stoud, it will refocus the sleep and the xdotool commands are to make sure the video preview is running in fullscreen

# PROCESS VIDEO COMMAND
# ffmpeg -framerate 30 -i <FILE TO CHANGE> -c copy <FILE TO CHANGE>.mp4

# CUTTING COMMAND
# ffmpeg -v debug -sseof -6 -i 000.mp4 000-1.mp4

HOST_NAME = "0.0.0.0"
PORT = 8080
MOMENT_CONFIG_FILE = '/home/pi/.config/Moment/moment.config'
global IP_ADDR

# Default Config File
default_config = {
    "audio": 'True',
    "video": 'True',
    "raw_audio": 'True',
    "framerate": "30",
    "resolution": "1080p",
    "time_segment": 60,
    "recording_location": "/home/pi/Videos/",
    "full_raw_save_location": "/home/pi/Moment_Save/raw/",
    "moment_save_location": "/home/pi/Moment_Save/final/",
    "drive_location": "/home/pi/drive/Garage_Videos/",
    "log_location": "/home/pi/Moment_Save/logs/",
    "log": 'True',
    "orientation": "portrait"
}

# Local Config File
config = {
    "audio" : 'True',
    "video": 'True',
    "raw_audio": 'True',
    "framerate": "30",
    "resolution": "1080p",
    "time_segment": 60,
    "recording_location": "/home/pi/Videos/",
    "full_raw_save_location": "/home/pi/Moment_Save/raw/",
    "moment_save_location": "/home/pi/Moment_Save/final/",
    "drive_location": "/home/pi/drive/Garage_Videos/",
    "log_location": "/home/pi/Moment_Save/logs/",
    "log": 'True',
    "orientation": "portrait"
}
        
# Resolution Dictionary
resolution = {
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

def read_file(path):
    """function to read a dictionary file"""
    try:
        with open(path) as f:
            file = f.read()
            data = json.loads(file)
            f.close()
    except Exception as e:
        data = e

    return data


def save_file(path, data):
    """function to save data to a dictionary file"""
    try:
        with open(path, 'w') as f:
            json.dump(data, f)
            f.close()
    except Exception as e:
        data = e
    return data


class PythonServer(SimpleHTTPRequestHandler):
    """Python HTTP Server that handles GET and POST requests"""

    def do_GET(self):
        global IP_ADDR
        if self.path == '/':
            moment_config = read_file(MOMENT_CONFIG_FILE)
            print("moment_config : ", moment_config)
            if moment_config['resolution'] == '1080p':
                resolution_html = '<br><label for="resolution">Resolution:</label> <select id="resolution" name="resolution" size="1"> <option value="1080p" selected>1080p</option> <option value="2.7k">2.7k</option> <option value="4k">4k</option> </select><br>'
            elif moment_config['resolution'] == '2.7k':
                resolution_html = '<br><label for="resolution">Resolution:</label> <select id="resolution" name="resolution" size="1"> <option value="1080p">1080p</option> <option value="2.7k" selected>2.7k</option> <option value="4k">4k</option> </select><br>'
            elif moment_config['resolution'] == '4k':
                resolution_html = '<br><label for="resolution">Resolution:</label> <select id="resolution" name="resolution" size="1"> <option value="1080p">1080p</option> <option value="2.7k">2.7k</option> <option value="4k" selected>4k</option> </select><br>'
            if moment_config['orientation'] == 'portrait':
                orientation_html = '<br><label for="orientation">Video Orientation:</label> <select id="orientation" name="orientation" size="1"> <option value="portrait" selected>Portrait</option> <option value="landscape">Landscape</option> </select><br>'
            elif moment_config['orientation'] == 'landscape':
                orientation_html = '<br><label for="orientation">Video Orientation:</label> <select id="orientation" name="orientation" size="1"> <option value="portrait">Portrait</option> <option value="landscape" selected>Landscape</option> </select><br>'
            html_file = '<!DOCTYPE html><html> <body> <h2>Simple Python HTTP Server Form</h2> <form method="POST", enctype="multipart/form-data" action="/success"> <label for="audio">Audio:</label><br><input type="text" name="audio" value="' + \
                str(moment_config['audio']) + '"><br><label for="video">Video:</label><br><input type="text" name="video" value="' + \
                str(moment_config['video']) + '"><br><label for="raw_audio">Raw Audio:</label><br><input type="text" name="raw_audio" value="' + \
                str(moment_config['raw_audio']) + '"><br><label for="time_segment">Time Segment(seconds to break up video):</label><br><input type="text" name="time_segment" value="' + \
                str(moment_config['time_segment']) + '"><br><label for="framerate">Framerate:</label><br><input type="text" name="framerate" value="' + \
                moment_config['framerate'] + '">' + \
                resolution_html + orientation_html + '<input type="submit" value="Submit"> </form><div><h2>Links:</h2> <a href="https://drive.google.com/drive/u/0/folders/1nMJ7mOO1B0X4He8TgJxdbnIvUouT5YlB" target="_blank">View Garage Moments</a><br><a href="http://' + \
                IP_ADDR + ':80">Configure Moment Wifi.</a><br><a href="http://' + \
                IP_ADDR + ':5572">Configure RClone via WebUI.</a><br><form method="POST", enctype="multipart/form-data" action="/factory-reset"><input type="submit" value="Factory Reset"></form></div></body></html>'
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(bytes(html_file, "utf-8"))

    def do_POST(self):
        if self.path == '/success':

            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')

            if ctype == 'multipart/form-data':
                error = False
                moment_config = read_file(MOMENT_CONFIG_FILE)
                fields = cgi.parse_multipart(self.rfile, pdict)
                audio = fields.get("audio")[0]
                video = fields.get("video")[0]
                raw_audio = fields.get("raw_audio")[0]
                framerate = fields.get("framerate")[0]
                resolution = fields.get("resolution")[0]
                orientation = fields.get("orientation")[0]
                time_segment = fields.get("time_segment")[0]
                moment_config = read_file(MOMENT_CONFIG_FILE)
                # check to see if booleans is either 'True' or 'False'
                errorText = ""
                if audio == 'True' or audio == 'False':
                    # change boolean from string to boolean
                    moment_config['audio'] = audio
                    config['audio'] = audio
                else:
                    error = True
                    errorText += "<b>Audio must be either True or False.</b><br>"
                if video == 'True' or video == 'False':
                    moment_config['video'] = video
                    config['video'] = video
                else:
                    error = True
                    errorText += "<b>Video must be either True or False.</b><br>"
                if raw_audio == 'True' or raw_audio == 'False':
                    moment_config['raw_audio'] = raw_audio
                    config['raw_audio'] = raw_audio
                else:
                    error = True
                    errorText += "<b>Raw Audio must be either True or False.</b><br>"
                if resolution == '1080p' or resolution == '2.7k' or resolution == '4k':
                    moment_config['resolution'] = resolution
                    config['resolution'] = resolution
                else:
                    error = True
                    errorText += "<b>Resolution must be either 1080p, 2.7k or 4k.</b><br>"
                if orientation == 'portrait' or orientation == 'landscape':
                    moment_config['orientation'] = orientation
                    config['orientation'] = orientation
                else:
                    error = True
                    errorText += "<b>Video Recording orientation must be either portrait or landscape.</b><br>"
                # check to see if framerate is a number if not set to 30
                if framerate.isdigit() and int(framerate) > 20 and int(framerate) < 120:
                    moment_config['framerate'] = str(framerate)
                    config['framerate'] = str(framerate)
                else:
                    error = True
                    errorText += "<b>Framerate must be either a number over 20 and below 120.</b><br>"
                if time_segment.isdigit() and int(time_segment) > 0 and int(time_segment) < 300:
                    moment_config['time_segment'] = int(time_segment)
                    config['time_segment'] = int(time_segment)
                else:
                    error = True
                    errorText += "<b>Time segment (seconds to segment up video) must be either a number over 0 and below 300.</b><br>"
                save_file(MOMENT_CONFIG_FILE, moment_config)
                
                if error == False:
                    html = f"<html><head></head><body><h1>Moment config successfully recorded Updated. Please Reboot Device in Order to use new config.</h1></body></html>"
                    # restart the recording process
                    
                else:
                    html = f"<html><head></head><body><h1>Error, please try again.</h1>" + \
                        errorText + '<br><div><a href="http://' + IP_ADDR + \
                        ':'+str(PORT)+'">Back</a></div><br></body></html>'

                self.send_response(200, "OK")
                self.end_headers()
                self.wfile.write(bytes(html, "utf-8"))
        if self.path == '/factory-reset':
            error = False
            moment_config = read_file(MOMENT_CONFIG_FILE)
            moment_config['audio'] = default_config['audio']
            moment_config['video'] = default_config['video']
            moment_config['raw_audio'] = default_config['raw_audio']
            moment_config['resolution'] = default_config['resolution']
            moment_config['orientation'] = default_config['orientation']
            moment_config['time_segment'] = default_config['time_segment']
            moment_config['framerate'] = default_config['framerate']
            
            config['audio'] = default_config['audio']
            config['video'] = default_config['video']
            config['raw_audio'] = default_config['raw_audio']
            config['resolution'] = default_config['resolution']
            config['orientation'] = default_config['orientation']
            config['time_segment'] = default_config['time_segment']
            config['framerate'] = default_config['framerate']

            save_file(MOMENT_CONFIG_FILE, moment_config)
            html = f'<html><head></head><body><h1>Config Reset to Default Settings.</h1><br><div><a href="http://' + IP_ADDR + \
                        ':'+str(PORT)+'">Back</a></div><br></body></html>'
            # restart the recording process with the new config
            
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(bytes(html, "utf-8"))
            
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
        
        # Check to see if there is a config file, if not, use the defaults
        if path.exists(MOMENT_CONFIG_FILE):
            # load configuation variables
            print("[DEBUG]: Loading Config File")
            moment_config = read_file(MOMENT_CONFIG_FILE)
            print("[DEBUG]:moment_config : ", moment_config)
            
            if(moment_config != config):
                print("[DEBUG]:Config File is different from default")
                if(moment_config["video"] != config["video"]):
                    if moment_config['video'] == 'True' or moment_config['video'] == 'False':
                        config["video"] = moment_config["video"]
                    else:
                        print("[DEBUG]:Config Video is not set to True or False")
                if(moment_config["audio"] != config["audio"]):
                    if moment_config['audio'] == 'True' or moment_config['audio'] == 'False':
                        config["audio"] = moment_config["audio"]
                    else:
                        print("[DEBUG]:Config Audio is not set to True or False")
                if(moment_config["raw_audio"] != config["raw_audio"]):
                    if moment_config['raw_audio'] == 'True' or moment_config['raw_audio'] == 'False':
                        config["raw_audio"] = moment_config["raw_audio"]
                    else:
                        print("[DEBUG]:Config Raw Audio is not set to True or False")
                if(moment_config["framerate"] != config["framerate"]):
                    if moment_config['framerate'].isdigit() and int(moment_config['framerate']) > 20 and int(moment_config['framerate'] < 120):
                        config["framerate"] = moment_config["framerate"]
                    else:
                        print("[DEBUG]:Config Framerate is not set to a number over 20 and below 120")
                if(moment_config["resolution"] != config["resolution"]):
                    if moment_config["resolution"] == '1080p' or moment_config["resolution"] == '2.7k' or moment_config["resolution"] == '4k':
                        config["resolution"] = moment_config["resolution"]
                    else:
                        print("[DEBUG]:Config Resolution is not set to 1080p, 2.7k or 4k")
                if(moment_config["orientation"] != config["orientation"]):
                    if moment_config["orientation"] == 'portrait' or moment_config["orientation"] == 'landscape':
                        config["orientation"] = moment_config["orientation"]
                    else:
                        print("[DEBUG]:Config Orientation is not set to portrait or landscape")
                if(moment_config["time_segment"] != config["time_segment"]):
                    if moment_config["time_segment"].isdigit() and int(moment_config["time_segment"]) > 10 and int(moment_config["time_segment"]) < 300:
                        config["time_segment"] = moment_config["time_segment"]
                    else:
                        print("[DEBUG]:Config Time Segment is not set to a number over 10")
                print("[DEBUG]:Default Variables have been updated")

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

    def initialize_main_menu(self):
        global IP_ADDR
        # Pull all the Network Information
        gw = popen("ip -4 route show default").read().split()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((gw[2], 0))
            IP_ADDR = str(s.getsockname()[0])
            self.gateway = gw[2]
            self.host = socket.gethostname()
            self.ssid = popen("iwgetid -r").read()
        except IndexError:
            IP_ADDR = "192.168.1.1"
            self.gateway = "192.168.1.1"
            self.ssid = "Mobile-AP"
            self.host = socket.gethostname()
                  
        Text(self.app, color="white", grid=[
            0, 0], text="   Network Information", size=34)

        Text(self.app, color="white", grid=[
            0, 1], text="HOST:" + str(self.host), size=26)

        Text(self.app, color="white", grid=[
            0, 2], text="IP:" + IP_ADDR, size=26)

        Text(self.app, color="white", grid=[
            0, 3], text="GW:" + str(self.gateway), size=26)

        Text(self.app, color="white", grid=[
            0, 4], text="SSID:" + str(self.ssid.strip("\n")), size=26)

        Text(self.app, color="white", grid=[
            0, 5], text="CONFIG:", size=26)

        Text(self.app, color="white", grid=[
            0, 6], text="http://" + IP_ADDR + ":" + str(PORT), size=26)

        Text(self.app, color="white", grid=[
            0, 7], text="\n  Press (-) to Upload\n   Press (+) to Save Rec.", size=26)

        Text(self.app, color="white", grid=[
            0, 8], text="        (-)             (+)", size=35)
        
    def run(self):
        # Configure the Directory for the moments and clear out past unsaved moments
        Popen("rm -rf " + config["recording_location"] + "*", shell=True).wait()
        Popen(["mkdir",'-p', config["recording_location"]]).wait()
        Popen("rm -rf " + config["full_raw_save_location"] + "*", shell=True).wait()
        Popen(["mkdir", '-p', config["full_raw_save_location"]]).wait()
        Popen(["mkdir", '-p', config["moment_save_location"]]).wait()

        self.initialize_main_menu()
        
        recorder_thread = threading.Thread(target=self.start_recording)
        recorder_thread.start()
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()

        self.app.display()
      
    def start_server(self):
        server = HTTPServer((HOST_NAME, PORT), PythonServer)
        print(f"Config Server Started at http://{HOST_NAME}:{PORT}")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
            print("Server stopped successfully")
            sys.exit(0)

    def start_recording(self):
        if self.recording == False:
            self.recording = True
            print("[DEBUG]:Recording started")
            sleep(1.5)
            self.filename = self.timestamp()
            # get current time
            self.start_time = datetime.datetime.now()
            if config["audio"] == 'True':
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
                    config["audio"] = 'False'
                else:
                    print("[DEBUG]:Start Audio Recording")
                    Popen("amixer set Capture 100%", shell=True).wait()
                    start_audio_command = "arecord "+ config["recording_location"] + str(self.filename) + ".wav"
                    Popen(start_audio_command, shell=True)
            if config["video"] == 'True':
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
                    config["video"] = 'False'
                else:
                    if config['orientation'] == 'portrait':
                        start_video_command = "libcamera-vid -t 0 --framerate " + config["framerate"] + " --qt-preview --hflip --vflip --autofocus -o " + config["recording_location"] + \
                            str(self.filename) + ".h264 --width " + \
                            resolution[config["resolution"]]["height"] + \
                            " --height "+ resolution[config["resolution"]]["width"]
                    elif config['orientation'] == 'landscape':
                        start_video_command = "libcamera-vid -t 0 --framerate " + config["framerate"] + " --qt-preview --autofocus -o " + config["recording_location"] + \
                            str(self.filename) + ".h264 --width " + \
                            resolution[config["resolution"]]["width"] + \
                            " --height " + \
                            resolution[config["resolution"]]["height"]
                    print("[DEBUG]:Start Recording Command: " + start_video_command)
                    Popen(
                        start_video_command,
                        shell=True)
                    sleep(5)
                    Popen(['xdotool', 'key', 'alt+F11'])
            if config["video"] == 'False' and config["audio"] == 'False':
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
                if path.ismount(config["drive_location"]):
                    upload_recording_command = "rsync -avzP --update --append --remove-source-files" + \
                        str(config["moment_save_location"]
                            ) + str(config["drive_location"])
                    print("[DEBUG]:Upload Moment Command: " +
                        upload_recording_command)
                    upload_recording = Popen(['rsync', '-avzP', '--update', '--append', '--remove-source-files',
                                            config["moment_save_location"], config["drive_location"]])
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
        if config["video"] == 'True':
            print("[DEBUG]:Killing Video...")
            Popen(['pkill', 'libcamera-vid']).wait()
        if config["audio"] == 'True':
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
                diff_segment = diff.seconds / config["time_segment"]
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
                    0, 3], text="[--PROCESSING--]", size=27)
                self.process_window.update()

                sleep(2)
                
                if config["audio"] == 'True' and config["video"] == 'False':
                    print("[DEBUG]:Processing Audio Only")
                    print("[DEBUG]:Cutting the .wav using ffmpeg while transcoding to .mp3")
                    cutting_audio = "ffmpeg -v debug -sseof -" + str(self.time_counter * config["time_segment"]) + " -i " + str(config["recording_location"]) + str(
                        self.filename) + ".wav -vn -ar 44100 -ac 2 -b:a 192k" + str(config["moment_save_location"]) + str(self.filename) + ".mp3"
                    print("[DEBUG] Cutting .wav while transcoding to .mp3 Command: " +
                          cutting_audio)
                    split_audio = Popen(
                        ['ffmpeg', '-v', 'debug', '-sseof', '-'+str(self.time_counter * config["time_segment"]), '-i', str(config["recording_location"]) + str(
                            self.filename) + '.wav', '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', str(config["moment_save_location"]) + str(self.filename) + '.mp3'])
                    split_audio.wait()
                    print("[DEBUG]:Audio Moment Processed and move to " +
                          str(config["moment_save_location"]) + '.mp3')
                    if config["raw_audio"] == 'False':
                        # ffmpeg -i <input_file> -af "highpass=f=200, lowpass=f=3000" <output_file>
                        self.filename += ".adj"
                        process_audio = "ffmpeg -i " + str(config["moment_save_location"]) + str(
                            self.filename) + ".mp3" + ' -af "highpass=f=200, lowpass=f=3000" ' + str(config["moment_save_location"]) + str(self.filename) + ".mp3"
                        print("[DEBUG] Adjusting Audio Quality: " +
                              process_audio)
                        process_audio = Popen(
                            ['ffmpeg', '-i', str(config["moment_save_location"]) + str(self.filename) + ".mp3", '-af', 'highpass=f=200, lowpass=f=3000', str(config["moment_save_location"]) + str(self.filename) + ".mp3"])
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

                elif config["video"] == 'True':
                    print("[DEBUG]:Processing Video ")
                    print("[DEBUG]:Process .h264 raw video using  into an .mp4")
                    raw_conversation_command = "ffmpeg -v debug -framerate " + str(config["framerate"]) + " -i " + str(config["recording_location"]) + str(
                        self.filename) + ".h264 -c copy " + str(config["full_raw_save_location"]) + str(self.filename) + ".mp4"
                    print("[DEBUG] Process Video Conversion Command: " + raw_conversation_command)
                    create_mp4 = Popen(
                        ['ffmpeg', '-v','debug', '-framerate', str(config["framerate"]), '-i', str(config["recording_location"]) + str(
                            self.filename) + '.h264', '-c', 'copy', str(config["full_raw_save_location"]) + str(self.filename) + '.mp4'])
                    create_mp4.wait()

                    Text(self.process_window, color="green", grid=[
                        0, 4], text="-Finished Raw Video Processing", size=22)
                    self.process_window.update()
                    sleep(1)

                    if config["audio"] == 'True':
                        print("[DEBUG]:Merging Audio and Video")
                        print(
                            "[DEBUG]:Transcoding the .wav using ffmpeg to .mp3")
                        transcoding_audio = "ffmpeg -v debug" + " -i " + str(config["recording_location"]) + str(
                            self.filename) + ".wav -vn -ar 44100 -ac 2 -b:a 192k" + str(config["recording_location"]) + str(self.filename) + ".mp3"
                        print("[DEBUG] Transcoding the .wav using ffmpeg to .mp3" +
                              transcoding_audio)
                        if config["raw_audio"] == 'False':
                            transcoding_audio = Popen(
                                ['ffmpeg', '-v', 'debug', '-i', str(config["recording_location"]) + str(
                                    self.filename) + '.wav', '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', str(config["recording_location"]) + str(self.filename) + '.mp3'])
                            transcoding_audio.wait()
                            print("[DEBUG]:Audio Moment Transcoded moved to " +
                              str(config["recording_location"]) + '.mp3')
                        else:
                            transcoding_audio = Popen(
                                ['ffmpeg', '-v', 'debug', '-i', str(config["recording_location"]) + str(
                                    self.filename) + '.wav', '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', str(config["full_raw_save_location"]) + str(self.filename) + '.mp3'])
                            transcoding_audio.wait()
                            print("[DEBUG]:Audio Moment Transcoded moved to " +
                                  str(config["full_raw_save_location"]) + '.mp3')
                        Text(self.process_window, color="green", grid=[
                            0, 5], text=" -Finished Audio Transcoding", size=22)
                        self.process_window.update()

                        if config["raw_audio"] == 'False':
                            # ffmpeg -i <input_file> -af "highpass=f=200, lowpass=f=3000" <output_file>
                            process_audio = "ffmpeg -i " + str(config["recording_location"]) + str(
                                self.filename) + ".mp3" + ' -af "highpass=f=200, lowpass=f=3000" ' + str(config["full_raw_save_location"]) + str(self.filename) + ".mp3"
                            print("[DEBUG] Adjusting Audio Quality: " +
                                process_audio)
                            process_audio = Popen(
                                ['ffmpeg', '-i', str(config["recording_location"]) + str(self.filename) + ".mp3", '-af', 'highpass=f=200, lowpass=f=3000', str(config["full_raw_save_location"]) + str(self.filename) + ".mp3"])
                            process_audio.wait()
                            Text(self.process_window, color="green", grid=[
                                0, 5], text=" -Finished HQ Audio Processing", size=22)
                            self.process_window.update()
                        # ffmpeg -ss 10 -t 6 -i input.mp3 output.mp3
                        # Clip Audio
                        clip_audio = "ffmpeg -ss 0:00:05 -i " + str(config["recording_location"]) + str(
                                self.filename) + ".mp3"  + str(config["full_raw_save_location"]) + str(self.filename) + "-clipped.mp3"
                        print("[DEBUG] Adjusting Audio Quality: " +
                            clip_audio)
                        clip_audio = Popen(
                            ['ffmpeg', '-ss', '0:00:05', '-i', str(config["full_raw_save_location"]) + str(self.filename) + ".mp3",  str(config["full_raw_save_location"]) + str(self.filename) + "-clipped.mp3"])
                        clip_audio.wait()
                        Text(self.process_window, color="green", grid=[
                            0, 6], text=" -Clipped Audio", size=22)
                        self.process_window.update()
                        # Merge Audio and Video
                        # ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac output.mp4
                        merge_audio_video = "ffmpeg -i " + str(config["full_raw_save_location"]) + str(self.filename) + ".mp4" + "-i " + str(
                            config["full_raw_save_location"]) + str(self.filename) + "-clipped.mp3" + " -c:v copy -c:a aac " + str(config["full_raw_save_location"]) + str(self.filename) + "-merged.mp4"
                        print("[DEBUG] Merging Audio and Video: " +
                              merge_audio_video)
                        merge_audio_video = Popen(['ffmpeg', '-i', str(config["full_raw_save_location"]) + str(self.filename) + ".mp4", '-ss', '0:00:00', '-i', str(
                            config["full_raw_save_location"]) + str(self.filename) + "-clipped.mp3", '-c:v', 'copy', '-c:a', 'aac', str(config["full_raw_save_location"]) + str(self.filename) + '-merged.mp4'])
                        merge_audio_video.wait()
                        self.filename += "-merged"
                        print("[DEBUG] Merged Audio and Video")
                        Text(self.process_window, color="green", grid=[
                            0, 7], text="-Finished Merging Audio+Video", size=22)
                        self.process_window.update()
                        sleep(1)

                    print("[DEBUG]:Cutting the Proccessed .mp4 Video using ffmpeg")
                    cutting_processed_video = "ffmpeg -v debug -sseof -" + str(self.time_counter * config["time_segment"]) + " -i " + str(config["full_raw_save_location"]) + str(
                        self.filename) + ".mp4 -c copy" + str(config["moment_save_location"]) + str(self.filename) + ".mp4"
                    print("[DEBUG] Cutting Processed Video Command: " +
                        cutting_processed_video)
                    splitMp4 = Popen(
                        ['ffmpeg', '-v', 'debug', '-sseof', '-'+str(self.time_counter * config["time_segment"]), '-i', str(config["full_raw_save_location"]) + str(
                            self.filename) + '.mp4', "-c", "copy", str(config["moment_save_location"]) + str(self.filename) + '.mp4'])
                    splitMp4.wait()

                    Text(self.process_window, color="green", grid=[
                        0, 8], text="-Finished Video Splitting", size=22)
                    self.process_window.update()
                    sleep(1)

                    print("[DEBUG]:Finished Processing Video, "+
                          str(self.filename)+".mp4 saved to "+config["full_raw_save_location"])

                    Text(self.process_window, color="white", grid=[
                        0, 9], text="Returning to Main Window", size=22)
                    Text(self.process_window, color="white", grid=[
                        0, 10], text="and Restarting Recording", size=22)
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
        diff_segment = diff.seconds / config["time_segment"]

        print("[DEBUG]:Full Moment Duration: " +
              str(diff_segment) + " time_segment")
        # If the difference is greater than the threshold, then process the Moment differently
        if diff_segment > 20:
            self.time_counter = 5
            print("[DEBUG]:Very Long Moment, Defaulting Time Counter to 5")
        elif diff_segment > 5:
            self.time_counter = 3
            print("[DEBUG]:Long Moment, Defaulting Time Counter to 3")
        else:
            print("[DEBUG]:Short Moment, Defaulting Time Counter to 1")
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
