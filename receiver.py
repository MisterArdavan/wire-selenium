from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import time
from datetime import datetime
from wire import log_control_message_time, login, download_file, get_message_type, get_credentials, get_messages, go_to_chat, log_time, download_image, download_media, get_text, RESTART, QUIT, logout, delete_files
import os
import argparse
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def set_proxy(driver, address, port, usernamex, passwordx):
    proxy_address_xpath = '//*[@id="proxyAddress"]'
    proxy_address_box = driver.find_element_by_xpath(proxy_address_xpath)
    proxy_address_box.send_keys(address)
    proxy_port_xpath = '//*[@id="proxyPort"]'
    proxy_port_box = driver.find_element_by_xpath(proxy_port_xpath)
    proxy_port_box.send_keys(port)
    proxy_username_xpath = '//*[@id="proxyUsername"]'
    proxy_username_box = driver.find_element_by_xpath(proxy_username_xpath)
    proxy_username_box.send_keys(usernamex)
    proxy_pass_xpath = '//*[@id="proxyPassword"]'
    proxy_pass_box = driver.find_element_by_xpath(proxy_pass_xpath)
    proxy_pass_box.send_keys(passwordx)
    save_xpath = '/html/body/div[2]/div[2]/button[4]'
    save_box = driver.find_element_by_xpath(save_xpath)
    save_box.click()

def start_browser(download_dir_path, foxyproxy_path, proxy_server_ip, proxy_server_port, proxy_server_username, proxy_server_password):
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

	if foxyproxy_path is not None:
		driver.install_addon(foxyproxy_path, temporary=None)
		time.sleep(2)
		driver.switch_to.window(driver.window_handles[1])
		driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		# go to the page where you can add the proxies
		xpath_back ="/html/body/div[2]/div[2]/button"
		WebDriverWait(driver, timeout=10).until(EC.element_to_be_clickable((By.XPATH, xpath_back))).click()

		time.sleep(5)
		# add proxy
		add_xpath = "/html/body/div[4]/div/nav/a[1]"
		WebDriverWait(driver, timeout=30).until(EC.element_to_be_clickable((By.XPATH, add_xpath))).click()
			
		# select proxy type (in my case socks5)
		type_xpath = '//*[@id="proxyType"]'
		type_box = driver.find_element_by_xpath(type_xpath)
		type_box.click()
			
		socks5_xpath = '/html/body/div[2]/div[1]/div[2]/div[1]/select/option[3]'
		socks5_box = driver.find_element_by_xpath(socks5_xpath)
		socks5_box.click()
			
		# write the proxy stuff
		set_proxy(driver, proxy_server_ip, proxy_server_port, proxy_server_username,  proxy_server_password)
		change_xpath = '//*[@id="mode"]'
		WebDriverWait(driver, timeout=10).until(EC.element_to_be_clickable((By.XPATH, change_xpath))).click()

		select_xpath = '/html/body/div[4]/div/div/div[1]/select/option[2]'
		WebDriverWait(driver, timeout=10).until(EC.element_to_be_clickable((By.XPATH, select_xpath))).click()
		driver.switch_to.window(driver.window_handles[0])

	login(driver, username, password)
	go_to_chat(driver, get_credentials(0)['sender'][0].upper())
	return driver

def restart_browser(driver, download_dir_path):
	print(f'Got restart message at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
	logout(driver)
	driver.quit()
	driver = start_browser(download_dir_path)
	return driver

def main(traces_dir_path, message_file_start_idx, message_file_end_idx, download_dir_path, foxyproxy_path, proxy_server_ip, proxy_server_port, proxy_server_username, proxy_server_password):
	traces_subdir_path = traces_dir_path / f'{message_file_start_idx:03}_{message_file_end_idx:03}'
	traces_subdir_path.mkdir(parents=True, exist_ok=True)
	download_dir_path.mkdir(parents=True, exist_ok=True)

	driver = start_browser(download_dir_path, foxyproxy_path, proxy_server_ip, proxy_server_port, proxy_server_username, proxy_server_password)

	with open(traces_subdir_path / f'traces_{message_file_start_idx}_{message_file_end_idx}.txt', 'a') as output:
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
						download_file(driver, message)
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
	parser.add_argument(
		'foxyproxy_path',
		metavar='FOXYPROXY_PATH', type=Path,
		help='Path to foxyproxy add-on xpi file'
	)
	parser.add_argument(
		'proxy_server_ip',
		metavar='PROXY_SERVER_IP', type=Path,
		help='IP address of the proxy server'
	)
	parser.add_argument(
		'proxy_server_port',
		metavar='PROXY_SERVER_PORT', type=Path,
		help='Port number of the proxy server'
	)
	parser.add_argument(
		'proxy_server_username',
		metavar='PROXY_SERVER_USERNAME', type=Path,
		help='username of the proxy server'
	)
	parser.add_argument(
		'proxy_server_password',
		metavar='PROXY_SERVER_PASSWORD', type=Path,
		help='password of the proxy server'
	)
	args = parser.parse_args()
	main(**vars(args))