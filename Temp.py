#!/usr/bin/python

# Google Spreadsheet DHT Sensor Data-logging Example

# Depends on the 'gspread' and 'oauth2client' package being installed.  If you
# have pip installed execute:
#   sudo pip install gspread oauth2client

# Also it's _very important_ on the Raspberry Pi to install the python-openssl
# package because the version of Python is a bit old and can fail with Google's
# new OAuth2 based authentication.  Run the following command to install the
# the package:
#   sudo apt-get update
#   sudo apt-get install python-openssl

# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
import sys
import time
import datetime
from Tkinter import *
import tkFont
import smtplib

import Adafruit_DHT
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# The receiving email. This can be changed in real time from the GUI, but it always resets to this at boot.
_EMAIL = 'test@gmail.com'

# At this moment, the sender has to be gmail, otherwise SMTP-settings have to be changed
_SENDER = 'TIEA345lampotila@gmail.com'
_SENDERPASS = '*****'

# Type of sensor, can be Adafruit_DHT.DHT11, Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
DHT_TYPE = Adafruit_DHT.DHT11

# Example of sensor connected to Raspberry Pi pin 23
DHT_PIN  = 22

# Tkinter stuff
win = Tk()
myFont = tkFont.Font(family = 'Helvetica', size = 36, weight = 'bold')

# Google Docs OAuth credential JSON file.  Note that the process for authenticating
# with Google docs has changed as of ~April 2015.  You _must_ use OAuth2 to log
# in and authenticate with the gspread library.  Unfortunately this process is much
# more complicated than the old process.  You _must_ carefully follow the steps on
# this page to create a new OAuth service in your Google developer console:
#   http://gspread.readthedocs.org/en/latest/oauth2.html
#
# Once you've followed the steps above you should have downloaded a .json file with
# your OAuth2 credentials.  This file has a name like SpreadsheetData-<gibberish>.json.
# Place that file in the same directory as this python script.
#
# Now one last _very important_ step before updating the spreadsheet will work.
# Go to your spreadsheet in Google Spreadsheet and share it to the email address
# inside the 'client_email' setting in the SpreadsheetData-*.json file.  For example
# if the client_email setting inside the .json file has an email address like:
#   149345334675-md0qff5f0kib41meu20f7d1habos3qcu@developer.gserviceaccount.com
# Then use the File -> Share... command in the spreadsheet to share it with read
# and write acess to the email address above.  If you don't do this step then the
# updates to the sheet will fail!
GDOCS_OAUTH_JSON       = 'jsonKey.json'

# Google Docs spreadsheet name.
GDOCS_SPREADSHEET_NAME = 'IOT-Thermometer'

# How long to wait (in seconds) between measurements. (1800 = 30min)
FREQUENCY_SECONDS      = 1800


def login_open_sheet(oauth_key_file, spreadsheet):
    """Connect to Google Docs spreadsheet and return the first worksheet."""
    try:
        scope =  ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file, scope)
        gc = gspread.authorize(credentials)
        worksheet = gc.open(spreadsheet).sheet1
        return worksheet
    except Exception as ex:
        print('Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!')
        print('Google sheet login failed with error:', ex)
        sys.exit(1)


print('Press Ctrl-C to quit.')
worksheet = None

email = _EMAIL
sender = _SENDER

#Send an email to designated email
def sendEmail(temp):
	global email
	smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
	smtpObj.ehlo()
	smtpObj.starttls()
	smtpObj.login(_SENDER, _SENDERPASS)
        
	smtpObj.sendmail(_SENDER, email,'Subject: Temperature: {:.9f}'.format(temp))
	smtpObj.quit()
	print("Sent email!")
	

def exitProgram():
	print("Exit Button pressed")
	win.quit()
e1 = None

def changeEmail():
	top = Toplevel()
	top.title("Email")

	Label(top, text="Email").grid(row=0)
	e1 = Entry(top)
	e1.grid(row=0, column=1)

	Button(top, text="Close", command=top.destroy).grid(row=1, column=0)
	Button(top, text="Apply", command= lambda: change(e1)).grid(row=1, column=1)

def change(e1):
	global email
	eString = e1.get()
	
	email = eString
	print("Changed email to " + email)

worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)

def checkTemp():
    print("Checking temperature...")
    # Login if necessary.
    global worksheet
    # Attempt to get sensor reading.
    humidity, temp = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)

    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).
    if humidity is None or temp is None:
        win.after(FREQUENCY_SECONDS, checkTemp)
        return

    print('Temperature: {0:0.1f} C'.format(temp))
    print('Humidity:    {0:0.1f} %'.format(humidity))

    # Append the data in the spreadsheet, including a timestamp
    try:
        worksheet.append_row((datetime.datetime.now(), temp, humidity))
    except:
        # Error appending data, most likely because credentials are stale.
        # Trying login again.
        print('Append error, logging in again')
        worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
        win.after(FREQUENCY_SECONDS, checkTemp)
        return

    # Wait 30 seconds before continuing
    print('Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME))
    win.after(FREQUENCY_SECONDS, checkTemp)
    tempLabel.config(text="Temp: " + str(temp))
    #tempLabel.pack()

    if temp > 25:
         print("Sending email...")
         sendEmail(temp)

win.after(FREQUENCY_SECONDS, checkTemp)

win.title("Temp/Hum meter")
win.geometry('480x320')

exitButton  = Button(win, text = "Exit", font = myFont, command = exitProgram, height =1 , width = 5) 
exitButton.pack(side = BOTTOM)

tempLabel = Label(win, text="Undefined", font = myFont)
tempLabel.pack()

emailButton = Button(win, text = "Change email", font = myFont, command = changeEmail, height = 1, width =12 )
emailButton.pack()

win.mainloop()
