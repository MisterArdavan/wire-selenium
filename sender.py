from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import time
from datetime import datetime
from wire import get_credentials, go_to_chat, login, send_text, send_file, send_picture, logout
from message.message import Message
from pathlib import Path
import json
import argparse

def main(messages_dir_path, message_content_dir_path, timestamps_dir_path, message_file_start_idx, message_file_end_idx):
    timestamps_subdir_path = timestamps_dir_path / f'{message_file_start_idx:03}_{message_file_end_idx:03}'
    timestamps_subdir_path.mkdir(parents=True, exist_ok=False)

    username = get_credentials(0)['sender'][0]
    password = get_credentials(0)['sender'][1]

    profile = FirefoxProfile()
    profile.set_preference("dom.webnotifications.enabled", False)
    driver = webdriver.Firefox(profile, executable_path = '../geckodriver')
    login(driver, username, password)
    go_to_chat(driver, get_credentials(0)['receiver'][0].upper())

    message_file_paths = sorted(list(messages_dir_path.glob('**/*')))
    for i in range(message_file_start_idx, message_file_end_idx + 1):
        json_path = message_file_paths[i]
        print(f'i is {i} file: {json_path.name}')
        messages = []
        with open(json_path) as f:
            data = json.load(f)
            for message in data['messages']:
                m = Message(message)
                messages.append(m)
        print(f'Number of messages for file {i} is {len(messages)}')

        for j in range(len(messages)):
            if j > 0:
                continue
            m = messages[j]
            print(f'Message {j} with id {m.get_id()} is being sent.')
            text = "" if m.get_text() is None else m.get_text()
            attachments = m.get_attachments()
            wait_time = 4#m.get_timestamp()/1000
            time.sleep(wait_time)
            t = datetime.now()
            if m.get_type() == 'text':
                send_text(driver, text)
            elif (attachments[0])[-4:] == '.png':
                send_picture(driver, f'{(message_content_dir_path / Path(attachments[0][44:])).resolve()}')
            else:
                send_file(driver, f'{(message_content_dir_path / Path(attachments[0][44:])).resolve()}')
            with open(timestamps_subdir_path / f'timestamps_{json_path.stem}.txt', "a") as myfile:
                myfile.write(t.strftime("%Y-%m-%d %H:%M:%S") + ' ' + str(t.timestamp()) + ' ' + str(m.get_id()) + '\n')
        time.sleep(60)
    logout(driver)
    driver.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Reads and sends messages through Wire web app'
    )
    parser.add_argument(
        'messages_dir_path',
        metavar='MESSAGES_DIR_PATH', type=Path,
        help='path to json messsage files directory'
    )
    parser.add_argument(
        'message_content_dir_path',
        metavar='MESSAGES_CONTENT_PATH', type=Path,
        help='path to message content files directory'
    )
    parser.add_argument(
        'timestamps_dir_path',
        metavar='TIMESTAMPS_DIR_PATH', type=Path,
        help='path to directory in which timestamps will be saved'
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
    args = parser.parse_args()
    main(**vars(args))