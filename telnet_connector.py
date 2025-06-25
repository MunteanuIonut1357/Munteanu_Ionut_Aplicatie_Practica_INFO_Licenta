"""Module used to establish telnet connection and configure devices"""

import telnetlib
import time
from abc import abstractmethod

class TelnetConnector:
    """
    Class that establish telnet connection and contains:
       connect method for the connection
       ssh configure method for devices
       abstract method configure_devices for classes to overwrite
       extract configuration to save device data into txt file
   """


    def __init__(self):
        self.connection=None
        self.conn=None
        self.hostname=None
        self.ssh_con=None
        self.password=None
        self.username=None
        self.device=None
        self.enable=None


    def connect(self,dev):
        """Establishes a Telnet connection to a given device."""

        self.device=dev
        self.conn=dev.connections['telnet']
        self.connection=telnetlib.Telnet(
            host=self.conn.ip.compressed,
            port=self.conn.port
        )
        self.hostname=dev.custom['hostname']
        self.ssh_con=dev.connections['ssh']['credentials']['login']
        self.password=self.ssh_con['password'].plaintext
        self.username=self.ssh_con['username']
        self.enable=dev.credentials['enable'].password.plaintext


    @abstractmethod
    def configure_device(self):
        """Abstract method that must be implemented by subclasses to configure the device."""



    def ssh_function(self):
        """Configures SSH access on the device."""

        self.connection.write(b'ip domain name local\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.connection.write(f'username {self.username} secret {self.password}\r\n'.encode())
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.connection.write(b'crypto key generate rsa\r\n')
        self.connection.expect([b'How many bits in the modulus'], timeout=5)
        time.sleep(0.5)

        self.connection.write(b'1024\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.connection.write(b'ip ssh version 2\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.connection.write(b'line vty 0 4\r\n')
        self.connection.expect([f"{self.hostname}\\(config-line\\)#".encode()])

        self.connection.write(b'login local\r\n')
        self.connection.expect([f"{self.hostname}\\(config-line\\)#".encode()])

        self.connection.write(b'transport input ssh\r\n')
        self.connection.expect([f"{self.hostname}\\(config-line\\)#".encode()])

        self.connection.write(b'exit\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

    def extract_configuration(self):
        """Extracts the running configuration and saves it to a local text file."""


        self.connection.write(b"exit\r\n")
        self.connection.expect([f"{self.hostname}#".encode()])
        self.connection.write(b"terminal length 0\r\n")
        self.connection.expect([f"{self.hostname}#".encode()])

        self.connection.write(b"show running-config\r\n")
        time.sleep(6)
        output = self.connection.read_very_eager()
        config_data = output.decode(errors="ignore")

        with open (f"configs/{self.hostname}_config.txt","w",encoding='utf-8') as file:
            file.write(config_data)


class Router(TelnetConnector):

    """
    Class that handles router configuration.

    Implements `configure_device` to perform:
    - Entering config mode
    - Configuring interface IPs and subinterfaces
    - Setting up HSRP
    - Configuring DHCP pools
    - Enabling EIGRP
    - Enabling SSH access
    """


    def configure_device(self):

        item_dict = self.device.interfaces

        self.connection.write(b"conf t\r\n")

        self.connection.write(f'hostname {self.hostname}\r\n'.encode())
        self.connection.expect([f"{self.hostname}\(config\)#".encode()])


        for value in item_dict.values():

            if '.' in str(value):
                self.connection.write(f"int {str(value).split(' ')[1].replace(',', '')}\r\n".encode())
                self.connection.expect([f"{self.hostname}\(config-subif\)#".encode()])
                self.connection.write(f"encapsulation dot1Q {value.vlan}\r\n".encode())
                self.connection.expect([f"{self.hostname}\(config-subif\)#".encode()])

            else:
                self.connection.write(f"int {str(value).split(' ')[1]}\r\n".encode())
                self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

            self.connection.write(f"ip add {str(value.ipv4).split('/',maxsplit=1)[0]} 255.255.255.0\r\n".encode())
            self.connection.write(b"no shut\r\n")

            if hasattr(value, "helper"):
                self.connection.write(f"ip helper-address {value.helper}\r\n".encode())
                self.connection.expect([f"{self.hostname}\\(config-(if|subif)\\)#".encode()])

            if hasattr(value, 'hsrp'):
                hsrp = value.hsrp
                self.connection.write(f"standby {hsrp['group']} ip {hsrp['virtual_ip']}\r\n".encode())
                self.connection.write(f"standby {hsrp['group']} priority {hsrp['priority']}\r\n".encode())
                self.connection.write(f"standby {hsrp['group']} preempt\r\n".encode())

        if "dhcp" in self.device.custom:
            for pool in self.device.custom["dhcp"]:
                self.connection.write(
                    f"ip dhcp excluded-address {pool['excluded'][0]} {pool['excluded'][1]}\r\n".encode()
                )
                self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

                pool_name = f"VLAN_{pool['network'].split('.')[2]}"
                self.connection.write(f"ip dhcp pool {pool_name}\r\n".encode())
                self.connection.expect([f"{self.hostname}\\(dhcp-config\\)#".encode()])

                self.connection.write(f"network {pool['network']} {pool['mask']}\r\n".encode())
                self.connection.write(f"default-router {pool['default_router']}\r\n".encode())
                self.connection.write(f"dns-server {pool['dns_server']}\r\n".encode())

                self.connection.expect([f"{self.hostname}\\(dhcp-config\\)#".encode()])

        self.connection.write(b'exit\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.connection.write(b"router eigrp 10\r\n")
        self.connection.expect([f"{self.hostname}\(config-router\)#".encode()])
        self.connection.write(b"no auto-summary\r\n")
        self.connection.expect([f"{self.hostname}\(config-router\)#".encode()])

        for value in item_dict.values():
            self.connection.write(
                f"network {('.'.join(str(value.ipv4).split('/',maxsplit=1)[0].split('.')[0:3]) + '.0')}\r\n".encode())

        self.connection.write(b'exit\r\n')

        self.connection.write(b'banner motd #Authorized Access Only#\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.connection.write(b'line console 0\r\n')
        self.connection.expect([f"{self.hostname}\\(config-line\\)#".encode()])
        self.connection.write(f'password {self.enable}\r\n'.encode())
        self.connection.write(b'login\r\n')
        self.connection.write(b'exit\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.ssh_function()

class Switch(TelnetConnector):
    """
    Class that handles switch configuration.

    Implements `configure_device` to perform:
    - Entering config mode
    - Configuring interface IPs
    - Configuring access or trunk mode on interfaces
    - Creating VLANs
    - Enabling Rapid PVST (Spanning Tree)
    - Enabling SSH access
    """


    def configure_device(self):

        vlan_set = set()
        item_dict = self.device.interfaces

        self.connection.write(b'en\r\n')

        self.connection.write(b"conf t\r\n")

        self.connection.write(f'hostname {self.hostname}\r\n'.encode())
        self.connection.expect([f"{self.hostname}\(config\)#".encode()])

        for value in item_dict.values():
            self.connection.write(f"int {str(value).split(' ')[1].replace(',', '')}\r\n".encode())
            self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

            if value.type == 'ethernet':

                if value.mode == 'access':
                    vlan_set.add(value.access)
                    self.connection.write(b"switchport mode access\r\n")
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

                    self.connection.write(f"switchport access vlan {value.access}\r\n".encode())
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

                    self.connection.write(b"switchport port-security\r\n")
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

                    self.connection.write(b"switchport port-security maximum 1\r\n")
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

                    self.connection.write(b"switchport port-security violation restrict\r\n")
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

                    self.connection.write(b"switchport port-security mac-address sticky\r\n")
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

                elif value.mode == 'trunk':
                    vlan_set.update(value.allowed_vlans)
                    concat_vlan = ",".join(map(str, value.allowed_vlans))

                    self.connection.write(b"switchport trunk encapsulation dot1q\r\n")
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

                    self.connection.write(b"switchport mode trunk\r\n")
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

                    self.connection.write(f"switchport trunk allowed vlan {concat_vlan}\r\n".encode())
                    self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])


            elif value.type == 'svi':
                self.connection.write(f"ip add {str(value.ipv4).split('/',maxsplit=1)[0]} 255.255.255.0\r\n".encode())
                self.connection.expect([f"{self.hostname}\(config-if\)#".encode()])

        for vlan in vlan_set:
            self.connection.write(f"vlan {vlan}\r\n".encode())
            self.connection.expect([f"{self.hostname}\(config-vlan\)#".encode()])
            self.connection.write(f"name VLAN{vlan}\r\n".encode())

        self.connection.write(b"exit\r\n")
        self.connection.expect([f"{self.hostname}\(config\)#".encode()])

        self.connection.write(b"spanning-tree mode rapid-pvst\r\n")

        self.connection.write(b'banner motd #Authorized Access Only#\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.connection.write(f'enable secret {self.enable}\r\n'.encode())
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.connection.write(b'line console 0\r\n')
        self.connection.expect([f"{self.hostname}\\(config-line\\)#".encode()])
        self.connection.write(f'password {self.enable}\r\n'.encode())
        self.connection.write(b'login\r\n')
        self.connection.write(b'exit\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])

        self.ssh_function()

        self.connection.write(b'exit\r\n')
        self.connection.expect([f"{self.hostname}\\(config\\)#".encode()])
