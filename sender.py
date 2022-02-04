import string
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import time
from datetime import datetime
from wire import get_credentials, go_to_chat, login, send_text, send_file, send_picture, logout, RESTART, QUIT
from message.message import Message
from pathlib import Path
import json
import argparse, subprocess, signal

def connect_to_vpn(vpn_conf_path, nordvpn_server):
    if vpn_conf_path is not None:
        command = [
            'sudo',
            'openvpn',
            vpn_conf_path
        ]
    else:
        command = [
            'nordvpn',
            'connect',
            nordvpn_server
        ]
    vpn_process = subprocess.Popen(command)
    print(str(vpn_process.pid))
    time.sleep(20)
    return vpn_process 

def disconnect_vpn(vpn_process, vpn_conf_path):
    if vpn_conf_path is not None:
        pid = vpn_process.pid
        command = [
            'sudo',
            'killall',
            'openvpn',
        ]
    else:
        command = [
            'nordvpn',
            'disconnect'
        ]
    completed_process = subprocess.run(command)
    if completed_process.returncode:
            "VPN process returned with error."
            raise SystemError(f'VPN Process Returned with error. Return code is {completed_process.returncode} for process with pid {pid}.')
    return

def start_browser():
    "starting browser"
    username = get_credentials(0)['sender'][0]
    password = get_credentials(0)['sender'][1]

    profile = FirefoxProfile()
    profile.set_preference("dom.webnotifications.enabled", False)
    driver = webdriver.Firefox(profile, executable_path = '../geckodriver')
    login(driver, username, password)
    go_to_chat(driver, get_credentials(0)['receiver'][0].upper())
    return driver

def restart_browser(driver):
    logout(driver)
    driver.quit()
    driver = start_browser()
    return driver

def restart_vpn(vpn_process, vpn_conf_path, nordvpn_server):
    disconnect_vpn(vpn_process, vpn_conf_path)
    vpn = connect_to_vpn(vpn_conf_path, nordvpn_server)
    return vpn


def main(messages_dir_path, message_content_dir_path, timestamps_dir_path, message_file_start_idx, message_file_end_idx, vpn_conf_path = None, nordvpn_server = None):
    timestamps_subdir_path = timestamps_dir_path / f'{message_file_start_idx:03}_{message_file_end_idx:03}' / 'timestamps'
    timestamps_subdir_path.mkdir(parents=True, exist_ok=False)

    if vpn_conf_path is not None or nordvpn_server is not None:
        vpn_process = connect_to_vpn(vpn_conf_path, nordvpn_server)
    driver = start_browser()

    message_file_paths = sorted(list(messages_dir_path.glob('**/*')))
    for i in range(message_file_start_idx, message_file_end_idx + 1):
        json_path = message_file_paths[i]
        print(f'i is {i}. file: {json_path.name}')
        messages = []
        with open(json_path) as f:
            data = json.load(f)
            for message in data['messages']:
                m = Message(message)
                messages.append(m)
        print(f'Number of messages for file {i} is {len(messages)}')

        for j in range(len(messages)):
            m = messages[j]
            print(f'Message {j+1} with id {m.get_id()} and type {m.get_type()} is being sent.')
            text = "" if m.get_text() is None else m.get_text()
            attachments = m.get_attachments()
            wait_time = m.get_timestamp()/1000
            time.sleep(wait_time)
            t = datetime.now()
            if m.get_type() == 'text':
                send_text(driver, text)
            # elif (attachments[0])[-4:] == '.png':
            #     send_picture(driver, f'{(message_content_dir_path / Path(attachments[0][44:])).resolve()}')
            else:
                send_file(driver, f'{(message_content_dir_path / Path(attachments[0][44:])).resolve()}')
            with open(timestamps_subdir_path / f'timestamps_{json_path.stem}.txt', "a") as myfile:
                myfile.write(f'{t.strftime("%Y-%m-%d %H:%M:%S")} {t.timestamp()} id: {m.get_id()} count: {j+1} {m.get_type()}\n')
        time.sleep(60)
        # clear_memory(driver) TODO
        send_text(driver, RESTART)
        print(f'Sent restart message at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        if vpn_conf_path is not None or nordvpn_server is not None:
            restart_vpn(vpn_process, vpn_conf_path, nordvpn_server)
        driver = restart_browser(driver)
        print(f'Done restarting at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        time.sleep(240)
    send_text(driver, QUIT)
    print(f'Sent quit message at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    time.sleep(10)
    logout(driver)
    time.sleep(10)
    driver.quit()
    print(f'Done quitting at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

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
        metavar='MESSAGE_FILE_END_IDX', type=int,
        help='Ending index for message files to be sent'
    )
    parser.add_argument(
        '--vpn-conf-path',
        metavar='VPN_CONF_PATH', type=Path,
        help='path to openvpn conf file'
    )
    parser.add_argument(
        '--nordvpn-server',
        metavar='OPENVPN_SERVER',
        help='OpenVPN Server Name'
    )

    args = parser.parse_args()
    main(**vars(args))