from bluepy.btle import Scanner, DefaultDelegate
from checksum import calcChecksum
from time import sleep
from data_logger import write_to_db
from datetime import timedelta, datetime

# define minimal interval between two values
MIN_AGE = timedelta(minutes=3)

# define CO2 upper level
MAX_CO2 = 5000

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        self.last_entry = datetime.now()
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewData:
            if dev.addr == 'd0:5f:b8:03:7d:3a':
                device_data = dev.getScanData()
                self.parseUUID(device_data[1][2])    


    
    def parseUUID(self, uuid_str:str):
        """
        Index         :        7   11 13   15     19 21   23  25                  39
                               |    |  |    |      |  |    |  |                   |
        Example string: 4c000215 0190 1b   27   03c9 27   a0  a0  0000000 000000 2d       ffe0ffe1 c5
        Labels        : Ibeacon  co2  temp.temp pres.pres hum.hum ------- ------ checksum other_stuff
        """
        co2 = int(uuid_str[8:12], 16)
        temp_1 = int(uuid_str[12:14], 16)
        temp_2 = int(uuid_str[14:16], 16)
        temp = temp_1 + (temp_2 / 100.0)
        pres_1 = int(uuid_str[16:20], 16)
        pres_2 = int(uuid_str[20:22], 16)
        pres = pres_1 + (pres_2 / 100.0)
        hum_1 = int(uuid_str[22:24], 16)
        hum_2 = int(uuid_str[24:26], 16)
        hum = hum_1 + (hum_2 / 100.0)
        r_check_1 = int(uuid_str[38:39], 16)
        r_check_2 = int(uuid_str[39:40], 16)
        l_check_1, l_check_2 = calcChecksum(uuid_str[8:26])
        checksum = True if (r_check_1 == l_check_1 and r_check_2 == l_check_2) else False
        print('Co2: {}, Temp: {}, Presure: {}, hum: {} checksum: {}' \
            .format(co2, temp, pres, hum, checksum))
        if checksum and (datetime.now() - self.last_entry > MIN_AGE) and co2 < MAX_CO2:
            write_to_db(co2, temp, pres, hum)
            self.last_entry=datetime.now()
        
    

scanner = Scanner().withDelegate(ScanDelegate())
if __name__ == '__main__':
    try:
        while True:
            scanner.scan()
            sleep(10)
    except KeyboardInterrupt:
        print("Exiting....")
