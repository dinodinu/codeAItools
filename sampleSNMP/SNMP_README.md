# SNMP Trap Parser (No External Libraries)

Pure Python implementation of SNMP trap receiver and sender using manual BER encoding/decoding.
No SNMP libraries required - only uses built-in Python socket module.

## Files

- **snmp_trap_parser.py**: Listens for and parses SNMP v1 and v2c traps
- **snmp_trap_sender.py**: Sends test SNMP v2c traps

## Usage

### Start the Trap Listener

```bash
# Listen on default port 162 (requires sudo/root)
sudo python3 snmp_trap_parser.py

# Or use a non-privileged port (1024+)
python3 snmp_trap_parser.py 1162
```

### Send Test Traps

In another terminal:

```bash
# Send to localhost on default port 162
python3 snmp_trap_sender.py

# Send to specific host and port
python3 snmp_trap_sender.py 192.168.1.100 162

# Send with custom community string
python3 snmp_trap_sender.py localhost 162 mycommunity
```

## Testing Locally

**Terminal 1 (Listener):**
```bash
python3 snmp_trap_parser.py 1162
```

**Terminal 2 (Sender):**
```bash
python3 snmp_trap_sender.py localhost 1162
```

## How It Works

### BER Encoding/Decoding

SNMP uses ASN.1 Basic Encoding Rules (BER) format:
- Each value has: Tag + Length + Value
- Tags identify data types (INTEGER, OCTET STRING, OID, etc.)
- Lengths can be short form (<128 bytes) or long form

### Parser Features

✓ Decodes SNMP v1 and v2c traps
✓ Parses all common SNMP data types:
  - INTEGER
  - OCTET STRING
  - OBJECT IDENTIFIER (OID)
  - NULL
  - IpAddress
  - TimeTicks
  - Counter32
  - Gauge32

### Sender Features

✓ Builds SNMP v2c trap packets from scratch
✓ Supports multiple data types
✓ Includes mandatory trap varbinds (sysUpTime, snmpTrapOID)

## Example Output

```
SNMP Trap Listener started on port 1162
Waiting for traps... (Press Ctrl+C to stop)

Received 156 bytes from 127.0.0.1:54321
======================================================================
SNMP Trap Received at 2026-02-16 14:30:45
======================================================================
SNMP Version: v2c
Community: public
PDU Type: SNMPv2 Trap
Request ID: 1001
Error Status: 0
Error Index: 0

Variable Bindings:
----------------------------------------------------------------------
  [1] 1.3.6.1.2.1.1.3.0
       Type: TimeTicks, Value: 172589300
  [2] 1.3.6.1.6.3.1.1.4.1.0
       Type: OID, Value: 1.3.6.1.4.1.99999.1.1
  [3] 1.3.6.1.4.1.99999.2.1
       Type: OCTET STRING, Value: System temperature high
  [4] 1.3.6.1.4.1.99999.2.2
       Type: INTEGER, Value: 85
======================================================================
```

## Customizing

### Send Custom Traps

Edit `snmp_trap_sender.py` and add your own traps:

```python
trap = build_snmp_v2c_trap(
    community="public",
    trap_oid="1.3.6.1.4.1.YOUR_ENTERPRISE.1",
    varbinds=[
        ("1.3.6.1.4.1.YOUR_ENTERPRISE.2.1", "string", "Your message"),
        ("1.3.6.1.4.1.YOUR_ENTERPRISE.2.2", "int", 42),
    ],
    request_id=2000
)
sock.sendto(trap, (host, port))
```

### Receive from Real Devices

Configure your network devices to send traps to your listener's IP and port.
Make sure the community string matches.

## Notes

- Port 162 requires root/sudo privileges
- Use ports above 1024 for testing without privileges
- Parser supports both SNMPv1 and SNMPv2c traps
- Sender currently only creates SNMPv2c traps
- No external dependencies needed

## License

Public domain - use freely
