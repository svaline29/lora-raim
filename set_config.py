import meshtastic
import meshtastic.serial_interface

interface = meshtastic.serial_interface.SerialInterface()
node = interface.localNode

# Print current value
print(f"Before: {node.localConfig.position.position_broadcast_secs}")

# Set it
node.localConfig.position.position_broadcast_secs = 30
node.localConfig.position.gps_update_interval = 15
node.localConfig.position.position_broadcast_smart_enabled = False
node.writeConfig("position")