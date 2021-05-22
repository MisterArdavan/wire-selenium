from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import time
from datetime import datetime
from wire import log_control_message_time, login, download_file, get_message_type, get_credentials, get_messages, go_to_chat, log_time, download_image, download_media, get_text, RESTART, QUIT, logout, delete_files
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
			message_batch_count = len(messages) - number_messages
			if message_batch_count > 0:
				number_messages = len(messages)
				if message_batch_count > 1:
					print(f'Overflow {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
				for i in range(message_batch_count):
					message = messages[-(i+1)]
					message_type = get_message_type(message)
					if (message_type == 'TEXT'):
						t = datetime.now()
						text = get_text(driver, message)
						if text == RESTART:
							log_control_message_time(output, 'START_RESTART', count, t)
							driver = restart_browser(driver, download_dir_path)
							delete_files(download_dir_path)	
							t = datetime.now()
							print(f'Done restarting at {t}')
							log_control_message_time(output, 'DONE_RESTART', count, t)
							count = 0
							number_messages = 1
							messages = get_messages(driver)
							continue
						elif text == QUIT:
							print(f'Got quit message at {t}')
							log_control_message_time(output, 'START_QUIT', count, t)
							logout(driver)
							driver.quit()
							t = datetime.now()
							print(f'Done quitting at {t}')
							log_control_message_time(output, 'DONE_QUIT', count, t)
							return
						else:
							count += 1
							log_time(output, 'TEXT', count)
					elif (message_type == 'IMAGE'):
						count += 1
						download_image(driver, message)
						log_time(output, 'IMAGE', count)
					elif (message_type == 'VIDEO'):
						count += 1
						download_media(driver, message)
						log_time(output, 'VIDEO', count)
					elif (message_type == 'AUDIO'):
						count += 1
						download_media(driver, message)
						log_time(output, 'AUDIO', count)
					elif (message_type == 'FILE'):
						count += 1
						download_file(message)
						log_time(output, 'FILE', count)
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
		metavar='MESSAGE_FILE_END_IDX', type=int,
		help='Ending index for message files to be sent'
    )
	parser.add_argument(
		'download_dir_path',
		metavar='DOWNLOAD_DIR_PATH', type=Path,
		help='Path to directory for downloading attachments'
	)
	args = parser.parse_args()
	main(**vars(args))