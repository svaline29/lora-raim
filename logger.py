import meshtastic
import meshtastic.serial_interface
import time
import datetime
import os
import csv
from pubsub import pub

if not os.path.exists('log.csv'):
    with open('log.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'from_id', 'rssi', 'snr', 'portnum'])

def onReceive(packet, interface):
    rssi = packet.get('rxRssi')
    snr = packet.get('rxSnr')

    if rssi is not None:
        timestamp = datetime.datetime.now().isoformat()
        from_id = packet.get('fromId')
        portnum = packet.get('decoded', {}).get('portnum', '')

        print(f"{portnum} | {from_id} | RSSI={rssi} SNR={snr}")

        with open('log.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, from_id, rssi, snr, portnum])

pub.subscribe(onReceive, "meshtastic.receive")
interface = meshtastic.serial_interface.SerialInterface()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    interface.close()