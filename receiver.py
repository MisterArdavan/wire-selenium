from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import time
from datetime import datetime
from wire import login, download_file, get_message_type, get_credentials, get_messages, go_to_chat, log_time, download_image, download_media, get_text, RESTART, QUIT, logout
import os
import argparse
from pathlib import Path

def start_browser(download_dir_path):
	username = get_credentials(0)['receiver'][0]
	password = get_credentials(0)['receiver'][1]

	mime_types = 'application/zip,application/octet-stream,image/jpeg,application/vnd.ms-outlook,text/html,application/pdf,audio/mpeg,text/plain,video/mp4'
	profile = FirefoxProfile()
	profile.set_preference("browser.download.folderList",2)
	profile.set_preference("dom.webnotifications.enabled", False)
	profile.set_preference("browser.download.manager.showWhenStarting",False) 
	profile.set_preference("browser.download.dir", str(download_dir_path.resolve()))
	profile.set_preference("browser.helperApps.neverAsk.saveToDisk", mime_types)

	driver = webdriver.Firefox(profile, executable_path = '../geckodriver')
	login(driver, username, password)
	go_to_chat(driver, get_credentials(0)['sender'][0].upper())
	return driver

def restart_browser(driver, download_dir_path):
	print(f'Got restart message at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
	logout(driver)
	driver.quit()
	driver = start_browser(download_dir_path)
	return driver

def main(traces_dir_path, message_file_start_idx, message_file_end_idx, download_dir_path):
	traces_subdir_path = traces_dir_path / f'{message_file_start_idx:03}_{message_file_end_idx:03}'
	traces_subdir_path.mkdir(parents=True, exist_ok=True)
	download_dir_path.mkdir(parents=True, exist_ok=True)

	driver = start_browser(download_dir_path)

	with open(traces_subdir_path / f'traces_{message_file_start_idx}_{message_file_end_idx}.txt', 'w') as output:
		number_messages = 1 
		count = 0
		while True:
			messages = get_messages(driver)
			message_batch_count = len(messages) > number_messages
			if message_batch_count > 0:
				number_messages = len(messages)
				if message_batch_count > 1:
					print(f'Overflow {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
				for i in range(message_batch_count):
					count += 1
					message = messages[-(i+1)]
					message_type = get_message_type(message)
					print(message_type)
					if (message_type == 'TEXT'):
						log_time(output, 'TEXT')
						if get_text(driver, message) == RESTART:
							driver = restart_browser(driver, download_dir_path)
							print(f'Done restarting at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
							count = 0
							number_messages = 1
							continue
						elif get_text(driver, message) == QUIT:
							print(f'Got quit message at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
							logout(driver)
							print(f'Done quitting at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
							driver.quit()
							return
					elif (message_type == 'IMAGE'):
						download_image(driver, message, download_dir_path)
						log_time(output, 'IMAGE')
					elif (message_type == 'VIDEO'):
						download_media(driver, message, download_dir_path)
						log_time(output, 'VIDEO')
					elif (message_type == 'AUDIO'):
						download_media(driver, message, download_dir_path)
						log_time(output, 'AUDIO')
					elif (message_type == 'FILE'):
						download_file(message, download_dir_path)
						log_time(output, 'FILE')
					print('got a message with count', count, datetime.now(), message_type)

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