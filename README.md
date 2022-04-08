# moment-recorder-video
Records Significant Moments in Garage's History


1. Connect to Device Access Point
2. Configure Wi-Fi Connection, Configure Web Storage Locaiton via RClone, and Auto Upload Behavior
3. Stream starts getting buffered to disk (up to 8GB of media before it starts recording over itself)
4. If button is pressed, save up to the last 3 minutes of data. Every 3 seconds the user holds the button, increase the save +3 more minutes. IE, 3 minutes of data saved, then 6 minutes of data saved, then 9 minutes, etc.
5. Save the data file as $date-MEMORY.mp4 locally
6. If the upload button is pressed after the save, go ahead and upload the memory to the webstorage location, else - wait till the Auto Upload Behavior that was preconfigured.
