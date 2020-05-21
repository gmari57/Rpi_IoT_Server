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
from influxdb import InfluxDBClient
import csv





def download_process():
	Download = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh download encrypted-barcodes.csv /home/pi/Documents/embedded_systems/Mixed_scriptd_1_folder/encrypted-barcodes.csv encrypted-barcodes.csv"
	call ([Download], shell=True)
	
	Download = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh download encrypted-Edge_frame.png /home/pi/Documents/embedded_systems/Mixed_scriptd_1_folder/encrypted-Edge_frame.png encrypted-Edge_frame.png"
	call ([Download], shell=True)
	
	Download = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh download encryption_code.txt /home/pi/Documents/embedded_systems/Mixed_scriptd_1_folder/encryption_code.txt encryption_code.txt"
	call ([Download], shell=True)
	print("Download completed")	

def remote_database_upload():
	client2 = InfluxDBClient(host='iotserver.eu.ngrok.io', port=80)  #insert ip(without http) and port (port for ngrok:80)
	client2.create_database('remote_client')
	measurement_name = "barcodes_table_2" 


	with open('decrypted-encrypted-barcodes.csv','r')as f:
		reader=csv.reader(f)
		data=list(reader)


	for i in range(len(data)):
		time_detection_value=data[i][0]
		description_value=data[i][1]


		json_body = [{"measurement": measurement_name,"tags": {"TimeDetection": time_detection_value,"description": description_value},"fields": {"id": 100}}]
		
		client2.write_points(json_body, database='ubu')

		print("Client Library Writen")

		time.sleep(1)

def database_upload():

	client = InfluxDBClient(host='localhost', port=8086)

	with open('decrypted-encrypted-barcodes.csv','r')as f:
		reader=csv.reader(f)
		data=list(reader)
	
		
	client.switch_database('newdb')#action_database=client.switch_database('newdb')

	for i in range(len(data)):
		time_detection=str(data[i][0])
		description=str(data[i][1])

		json_body = [{"measurement": "project_2","tags": {"QrCodeInfo": time_detection,"TimeOfDetection": description},"fields": {"value": 100}}]
		
		client.write_points(json_body)
	print("Database-upload-completed")	

def decrypt(filename, key):
    """
    Given a filename (str) and key (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    # write the original file
    with open("decrypted-"+filename, "wb") as file:
        file.write(decrypted_data)

def dencryption_process():
	with open("encryption_code.txt","r") as encryption_key:
		encryption_code=encryption_key.read().replace('\n','')

	decrypt('encrypted-barcodes.csv', encryption_code)
	decrypt('encrypted-Edge_frame.png', encryption_code)
	
	print("Decryption-completed")

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


	if(string_key=="download"):
		print("Entering "+string_key+" mode")
		download_process()

	if(string_key=="dencryption"):
		print("Entering "+string_key+" mode")
		dencryption_process()	
			

	if(string_key=="database_upload"):
		print("Entering "+string_key+" mode")
		database_upload()			

	if(string_key=="remote_database_upload"):
		print("Entering "+string_key+" mode")
		remote_database_upload()
		print("Remote Database upload Completed")	

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set("pzjwqfpb", "2X52orCEVx4a")
client.connect("m14.cloudmqtt.com", 11945)



client.loop_forever()

