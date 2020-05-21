import paho.mqtt.client as mqtt
import sys
from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import datetime
import imutils
import time
import cv2
import numpy as np
import os
import glob
from flask import Flask
from cryptography.fernet import Fernet
from subprocess import call





def upload_process():
	Upload = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload /home/pi/Documents/embedded_systems/Mixed_scriptd_1_folder/encrypted-barcodes.csv encrypted-barcodes.csv"
	call ([Upload], shell=True)
	
	Upload = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload /home/pi/Documents/embedded_systems/Mixed_scriptd_1_folder/encrypted-Edge_frame.png encrypted-Edge_frame.png"
	call ([Upload], shell=True)
	print("upload completed")	
	
	Upload = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload /home/pi/Documents/embedded_systems/Mixed_scriptd_1_folder/encryption_code.txt encryption_code.txt"
	call ([Upload], shell=True)


def write_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    #print(key)
    with open("encryption-key.key", "wb") as key_file:
        key_file.write(key)


def load_key():
    """
    Loads the key from the current directory named `key.key`
    """
    print("encryption-key-generated")
    return open("encryption-key.key", "rb").read()

def encrypt(filename, key):
    """
    Given a filename (str) and key (bytes), it encrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
    	# read all file data
    	file_data = file.read()
   	# encrypt data
   	encrypted_data = f.encrypt(file_data)
   	# write the encrypted file
   	with open("encrypted-"+filename, "wb") as file:
   		file.write(encrypted_data)
   	print(filename + "encrypted")

def encryption_process():
	write_key()
	encryption_code = load_key()
	encryption_file=open("encryption_code.txt","w")
	encryption_file.write(encryption_code)
	encryption_file.close
	
	encrypt('barcodes.csv', encryption_code)
	encrypt('Edge_frame.png', encryption_code)
	
	print("encryption completed")

def edge_camera(time_value):
	print(time_value)
	# capture frames from a camera
	i=0
	cap = cv2.VideoCapture(0) 
	
	  
	# loop runs if capturing has been initialized 
	while(1): 
	  	
	    # reads frames from a camera 
	    ret, frame = cap.read()
	    i=i+1
	    if(i==time_value):
	    	break
	    # converting BGR to HSV 
	    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
	      
	    # define range of red color in HSV 
	    lower_red = np.array([30,150,50]) 
	    upper_red = np.array([255,255,180]) 
	      
	    # create a red HSV colour boundary and  
	    # threshold HSV image 
	    mask = cv2.inRange(hsv, lower_red, upper_red) 
	  
	    # Bitwise-AND mask and original image 
	    res = cv2.bitwise_and(frame,frame, mask= mask) 
	  
	    # Display an original image 
	    cv2.imshow('Original',frame)
	    cv2.waitKey(1)

	    # finds edges in the input image image and 
	    # marks them in the output map edges 
	    edges = cv2.Canny(frame,100,200) 
	  
	    # Display edges in a frame 
	    cv2.imshow('Edges',edges)
	    cv2.waitKey(1)

	cv2.destroyAllWindows()
	cv2.imwrite("Edge_frame.png",edges)

def barcode_camera(time_value):
	# construct the argument parser and parse the arguments
	print(time_value)
	i=0
	ap = argparse.ArgumentParser()
	ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
		help="path to output CSV file containing barcodes")
	args = vars(ap.parse_args())

	# initialize the video stream and allow the camera sensor to warm up
	print("[INFO] starting video stream...")
	vs = VideoStream(src=0).start()
	#vs = VideoStream(usePiCamera=True).start()
	time.sleep(2.0)
	# open the output CSV file for writing and initialize the set of
	# barcodes found thus far
	csv = open(args["output"], "a")
	found = set()

	# loop over the frames from the video stream
	while True:
		# grab the frame from the threaded video stream and resize it to
		# have a maximum width of 400 pixels
		frame = vs.read()
		i=i+1
		if(i==time_value):
			break
		frame = imutils.resize(frame, width=400)
		cv2.waitKey(1)
		# find the barcodes in the frame and decode each of the barcodes
		barcodes = pyzbar.decode(frame)

			# loop over the detected barcodes
		for barcode in barcodes:
			# extract the bounding box location of the barcode and draw
			# the bounding box surrounding the barcode on the image
			(x, y, w, h) = barcode.rect
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
			# the barcode data is a bytes object so if we want to draw it
			# on our output image we need to convert it to a string first
			barcodeData = barcode.data.decode("utf-8")
			barcodeType = barcode.type
			# draw the barcode data and barcode type on the image
			text = "{} ({})".format(barcodeData, barcodeType)
			cv2.putText(frame, text, (x, y - 10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
			# if the barcode text is currently not in our CSV file, write
			# the timestamp + barcode to disk and update the set
			if barcodeData not in found:
				csv.write("{},{}\n".format(datetime.datetime.now(),
					barcodeData))
				csv.flush()
				found.add(barcodeData)
				# show the output frame
		cv2.imshow("Barcode Scanner", frame)
		cv2.waitKey(1)

	    

		
	print("[INFO] cleaning up...")
	csv.close()
	cv2.destroyAllWindows()
	vs.stop()


# Callback Function on Connection with MQTT Server
def on_connect( client, userdata, flags, rc):
    print ("Connected with Code :" +str(rc))
    # Subscribe Topic from here
    client.subscribe("Test/#")

# Callback Function on Receiving the Subscribed Topic/Message
def on_message( client, userdata, msg):
    # print the message received from the subscribed topic
    #print ( str(msg.payload) )

    process_function(str(msg.payload))

def process_function(message):
	print (message)
	if ("exit" in message):
		print("Entering exit mode")
		sys.exit()

	temp_table=message.split("-")
	#final_string_table=temp_table[1].split("-")


	string_key=temp_table[0]
	time_key=temp_table[1]
	time_key=int(time_key)
	print(string_key)

	if(string_key=="barcode_camera"):
		print("Entering "+string_key+" mode")
		barcode_camera(time_key)


	if(string_key=="edge_camera"):
		print("Entering "+string_key+" mode")
		edge_camera(time_key)

	if(string_key=="encryption"):
		print("Entering "+string_key+" mode")
		encryption_process()	

	if(string_key=="upload"):
		print("Entering "+string_key+" mode")
		upload_process()			




client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set("pzjwqfpb", "2X52orCEVx4a")
client.connect("m14.cloudmqtt.com", 11945)



client.loop_forever()

