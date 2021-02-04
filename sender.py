from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import time
from datetime import datetime
from wire import *


USERNAME = '***REMOVED***'
PASSWORD = '***REMOVED***'

profile = FirefoxProfile()
profile.set_preference("dom.webnotifications.enabled", False);

driver = webdriver.Firefox(profile)

login(driver, USERNAME, PASSWORD)
go_to_chat(driver, 'SPIN01')

send_text(driver, 'hello ' + datetime.now().strftime("%H:%M:%S"))

send_picture(driver, '/home/amigh/Documents/wire/test-assets/image.jpg')
send_file(driver, '/home/amigh/Documents/wire/test-assets/file.jpg')
send_file(driver, '/home/amigh/Documents/wire/test-assets/20MB.zip')


# time.sleep(5)
# logout(driver)
# driver.close()