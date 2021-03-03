from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import time
from datetime import datetime
from wire import login, download_file, get_message_type, get_credentials, get_messages, go_to_chat, log_time, download_image, download_media
import os
import argparse
from pathlib import Path

def main(traces_dir_path, message_file_start_idx, message_file_end_idx, download_dir_path):
	traces_subdir_path = traces_dir_path / f'{message_file_start_idx:03}_{message_file_end_idx:03}'
	traces_subdir_path.mkdir(parents=True, exist_ok=False)
	download_dir_path.mkdir(parents=True, exist_ok=True)
	username = get_credentials(0)['receiver'][0]
	password = get_credentials(0)['receiver'][1]

	mime_types = 'application/zip,application/octet-stream,image/jpeg,application/vnd.ms-outlook,text/html,application/pdf,audio/mpeg,text/plain,video/mp4'
	profile = FirefoxProfile()
	profile.set_preference("browser.download.folderList",2)
	profile.set_preference("browser.download.manager.showWhenStarting",False) 
	profile.set_preference("browser.download.dir", str(download_dir_path.resolve()))
	profile.set_preference("browser.helperApps.neverAsk.saveToDisk", mime_types)

	driver = webdriver.Firefox(profile, executable_path = '../geckodriver')

	with open(traces_subdir_path / f'traces_{message_file_start_idx}_{message_file_end_idx}.txt', 'w') as output:
		login(driver, username, password)
		go_to_chat(driver, get_credentials(0)['sender'][0].upper())
		number_messages = 1 
		while True:
			messages = get_messages(driver)
			if len(messages) > number_messages:
				number_messages = len(messages)
				message = messages[-1]
				message_type = get_message_type(message)
				if (message_type == 'TEXT'):
					log_time(output)
				elif (message_type == 'IMAGE'):
					download_image(driver, message, download_dir_path)
					log_time(output)
				elif (message_type == 'VIDEO'):
					download_media(driver, message, download_dir_path)
					log_time(output)
				elif (message_type == 'AUDIO'):
					download_media(driver, message, download_dir_path)
					log_time(output)
				elif (message_type == 'FILE'):
					download_file(message, download_dir_path)
					log_time(output)
				print('got a message', datetime.now(), message_type)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
        description='Receives messages through Wire\'s web app'
    )
	parser.add_argument(
		'traces_dir_path',
		metavar='TRACES_DIR_PATH', type=Path,
		help='Path to directory in which traces will be saved'
    )
	parser.add_argument(
		'message_file_start_idx',
		metavar='MESSAGE_FILE_START_IDX', type=int,
		help='Starting index for message files to be sent'
    )
	parser.add_argument(
		'message_file_end_idx',
		metavar='MESSAGE_FILE_START_IDX', type=int,
		help='Ending index for message files to be sent'
    )
	parser.add_argument(
		'download_dir_path',
		metavar='DOWNLOAD_DIR_PATH', type=Path,
		help='Path to directory for downloading attachments'
	)
	args = parser.parse_args()
	main(**vars(args))