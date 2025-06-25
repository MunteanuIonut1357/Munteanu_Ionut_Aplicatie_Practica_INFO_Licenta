"""main function used for managing the functionality"""

import telnetlib
import time

from pyats import aetest
from pyats.topology import loader

from telnet_connector import Router, Switch

tb=loader.load("test_bedu.yaml")
dev = tb.devices

class ConnectivityVerifier:
    """Class that manages connection between Pc's and Routers"""

    def __init__(self):
        self.total_connectivity=0
        self.working_connectivity=0
        self.connection=None


    def main_conn(self):
        """Function used to call for dhcp on pc's"""

        for pc in dev.values():
            if pc.type == 'PC':

                ip = pc.connections.telnet.ip
                port = pc.connections.telnet.port
                self.connection = telnetlib.Telnet(
                    host=ip.compressed,
                    port=port
                )
                self.connection.write(b'dhcp\r\n')
                self.connection.expect([b'DORA IP'], timeout=10)

                for device in dev.values():
                    self.test_ping(device,pc)

        total_connection_percentage= self.working_connectivity / self.total_connectivity * 100

        print(f"Connectivity is at {total_connection_percentage:.2f} percent!")

    def test_ping(self,device,pc):
        """Method used to test connectivity between Pc's and Routers"""

        if device.type == 'router':
            print(f"\nNow pinging {device.name} from {pc.name}\n")
            for interface in device.interfaces.values():
                ip_to_ping = interface.ipv4
                self.connection.write(f'ping {ip_to_ping}\r\n'.encode())
                time.sleep(6)

                output = self.connection.read_very_eager().decode(errors="ignore")

                lines = output.strip().split('\n')
                last_lines = lines[-5:]

                found = False
                for line in last_lines:
                    if 'bytes from' in line.lower():
                        found = True

                if found:
                    print(f"Ping to interface {interface.name} works")
                    self.working_connectivity += 1
                else:
                    print(f"Ping from {pc.name} to {interface.name} doesn't work")
                    self.connection.write(b'\x03')
                    self.connection.read_until(f"{pc.name}>".encode(), timeout=5)

                self.total_connectivity += 1



class TestClass(aetest.Testcase):
    """Class that test if the code runs in optimal condition"""

    @aetest.test
    def main_config(self) -> None:

        """
        Loops through all the devices that are in testbed (almost)
        If a device supports telnet it will use TelnetConnector
        If a device supports ssh it will use SSHConnector
        """
        while True:
            print("\nMenu for topology configuration:\n"
                  "0.Exit\n"
                  "1.Configure all of the devices\n"
                  "2.Test connectivity between PC's and Routers\n"
                  )

            while True:
                try:
                    option = int(input("Choose one option: "))
                    break
                except (UnboundLocalError, ValueError) as e:
                    print(f"Option not valid!\nError: {e}")

            match option:
                case 0:
                    break
                case 1:

                    for item in dev.values():

                        if 'telnet' in item.connections:

                            if item.type=='router':
                                connector=Router()
                                connector.connect(item)
                                connector.configure_device()
                                connector.extract_configuration()
                                print(f"Device {item.name} configured successfully")

                            elif item.type=='switch':
                                connector=Switch()
                                connector.connect(item)
                                connector.configure_device()
                                connector.extract_configuration()
                                print(f"Device {item.name} configured successfully")

                            else:
                                print(f"Device {item.name} not supported")


                        time.sleep(3)
                case 2:
                    conn_obj=ConnectivityVerifier()
                    conn_obj.main_conn()


if __name__ == '__main__':
    aetest.main()
