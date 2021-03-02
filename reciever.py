from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import time
from datetime import datetime
from wire import *
import os


username = get_credentials(0)['receiver'][0]
password = get_credentials(0)['receiver'][1]

mime_types = 'application/zip,application/octet-stream,image/jpeg,application/vnd.ms-outlook,text/html,application/pdf"'
profile = FirefoxProfile()
profile.set_preference("browser.download.folderList",2)
profile.set_preference("browser.download.manager.showWhenStarting",False) 
profile.set_preference("browser.download.dir", DOWNLOAD_PATH)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", mime_types)

driver = webdriver.Firefox(profile)

output = open('result.txt', 'w')

login(driver, username, password)
go_to_chat(driver, 'Amir')
number_messages = 1
while True:
	messages = get_messages(driver)
	if len(messages) > number_messages:
		number_messages = len(messages)
		message = messages[-1]
		# print(message.get_attribute('innerHTML'))
		#data-uie-name="file-name"
		message_type = get_message_type(message)
		if (message_type == 'TEXT'):
			log_time(output)
		elif (message_type == 'IMAGE'):
			# download_image(message)
			log_time(output)
		elif (message_type == 'FILE'):
			download_file(message)
			log_time(output)
		print('got a message' ,datetime.now(), message_type)

#style="stroke-dasharray: 16.875, 100;"