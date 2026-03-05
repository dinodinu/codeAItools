#!/usr/bin/env python3
"""
Simple SNMP Trap Sender - No external SNMP libraries
Sends SNMP v2c traps using raw socket and manual BER encoding
"""

import socket
import struct
import time

# SNMP Trap Port
TRAP_PORT = 162

# ASN.1 BER Type Tags
ASN1_SEQUENCE = 0x30
ASN1_INTEGER = 0x02
ASN1_OCTET_STRING = 0x04
ASN1_NULL = 0x05
ASN1_OBJECT_IDENTIFIER = 0x06
ASN1_TIMETICKS = 0x43

# SNMP PDU Types
SNMP_TRAP_V2 = 0xA7


class BEREncoder:
    """Basic Encoding Rules (BER) Encoder for SNMP"""
    
    def __init__(self):
        self.buffer = bytearray()
    
    def encode_length(self, length):
        """Encode BER length field"""
        if length < 128:
            return bytes([length])
        else:
            # Long form
            length_bytes = []
            temp = length
            while temp > 0:
                length_bytes.insert(0, temp & 0xFF)
                temp >>= 8
            return bytes([0x80 | len(length_bytes)] + length_bytes)
    
    def encode_integer(self, value):
        """Encode BER integer"""
        # Convert integer to bytes
        if value == 0:
            value_bytes = [0]
        else:
            value_bytes = []
            temp = abs(value)
            while temp > 0:
                value_bytes.insert(0, temp & 0xFF)
                temp >>= 8
            
            # Add sign byte if necessary for negative numbers
            if value < 0:
                # Two's complement
                for i in range(len(value_bytes)):
                    value_bytes[i] = ~value_bytes[i] & 0xFF
                
                carry = 1
                for i in range(len(value_bytes) - 1, -1, -1):
                    value_bytes[i] += carry
                    if value_bytes[i] > 0xFF:
                        value_bytes[i] &= 0xFF
                    else:
                        carry = 0
                        break
                
                if not (value_bytes[0] & 0x80):
                    value_bytes.insert(0, 0xFF)
            elif value_bytes[0] & 0x80:
                # Positive number with high bit set needs padding
                value_bytes.insert(0, 0x00)
        
        return bytes([ASN1_INTEGER]) + self.encode_length(len(value_bytes)) + bytes(value_bytes)
    
    def encode_octet_string(self, value):
        """Encode BER octet string"""
        if isinstance(value, str):
            value = value.encode('utf-8')
        
        return bytes([ASN1_OCTET_STRING]) + self.encode_length(len(value)) + value
    
    def encode_oid(self, oid):
        """Encode BER Object Identifier"""
        if isinstance(oid, str):
            parts = [int(x) for x in oid.split('.')]
        else:
            parts = oid
        
        if len(parts) < 2:
            raise ValueError("OID must have at least 2 components")
        
        # First byte encodes first two subidentifiers
        oid_bytes = [parts[0] * 40 + parts[1]]
        
        # Encode remaining subidentifiers
        for subid in parts[2:]:
            if subid < 128:
                oid_bytes.append(subid)
            else:
                # Multi-byte encoding
                encoded = []
                temp = subid
                while temp > 0:
                    encoded.insert(0, (temp & 0x7F) | (0x80 if encoded else 0))
                    temp >>= 7
                oid_bytes.extend(encoded)
        
        return bytes([ASN1_OBJECT_IDENTIFIER]) + self.encode_length(len(oid_bytes)) + bytes(oid_bytes)
    
    def encode_null(self):
        """Encode BER NULL"""
        return bytes([ASN1_NULL, 0x00])
    
    def encode_timeticks(self, value):
        """Encode SNMP TimeTicks"""
        value_bytes = []
        if value == 0:
            value_bytes = [0]
        else:
            temp = value
            while temp > 0:
                value_bytes.insert(0, temp & 0xFF)
                temp >>= 8
        
        return bytes([ASN1_TIMETICKS]) + self.encode_length(len(value_bytes)) + bytes(value_bytes)
    
    def encode_sequence(self, data):
        """Encode BER SEQUENCE"""
        return bytes([ASN1_SEQUENCE]) + self.encode_length(len(data)) + data


def build_snmp_v2c_trap(community, trap_oid, varbinds, request_id=12345):
    """
    Build an SNMP v2c trap packet
    
    Args:
        community: Community string (e.g., "public")
        trap_oid: Trap OID (e.g., "1.3.6.1.4.1.99999.1")
        varbinds: List of tuples (oid, type, value)
                  type can be: 'int', 'string', 'oid', 'timeticks', 'null'
    """
    encoder = BEREncoder()
    
    # Build Variable Bindings
    varbind_list = bytearray()
    
    # sysUpTime (mandatory first varbind for v2c trap)
    uptime_varbind = (
        encoder.encode_sequence(
            encoder.encode_oid("1.3.6.1.2.1.1.3.0") +
            encoder.encode_timeticks(int(time.time() * 100))
        )
    )
    varbind_list.extend(uptime_varbind)
    
    # snmpTrapOID (mandatory second varbind for v2c trap)
    trapoid_varbind = (
        encoder.encode_sequence(
            encoder.encode_oid("1.3.6.1.6.3.1.1.4.1.0") +
            encoder.encode_oid(trap_oid)
        )
    )
    varbind_list.extend(trapoid_varbind)
    
    # Additional varbinds
    for oid, vtype, value in varbinds:
        if vtype == 'int':
            encoded_value = encoder.encode_integer(value)
        elif vtype == 'string':
            encoded_value = encoder.encode_octet_string(value)
        elif vtype == 'oid':
            encoded_value = encoder.encode_oid(value)
        elif vtype == 'timeticks':
            encoded_value = encoder.encode_timeticks(value)
        elif vtype == 'null':
            encoded_value = encoder.encode_null()
        else:
            raise ValueError(f"Unknown type: {vtype}")
        
        varbind = encoder.encode_sequence(
            encoder.encode_oid(oid) + encoded_value
        )
        varbind_list.extend(varbind)
    
    # Build PDU
    pdu = (
        encoder.encode_integer(request_id) +      # Request ID
        encoder.encode_integer(0) +                # Error Status
        encoder.encode_integer(0) +                # Error Index
        encoder.encode_sequence(bytes(varbind_list))  # VarBindList
    )
    
    # Build PDU with trap type tag
    trap_pdu = bytes([SNMP_TRAP_V2]) + encoder.encode_length(len(pdu)) + pdu
    
    # Build SNMP Message
    message = (
        encoder.encode_integer(1) +                # Version (1 = v2c)
        encoder.encode_octet_string(community) +   # Community
        trap_pdu                                   # PDU
    )
    
    # Wrap in SEQUENCE
    return encoder.encode_sequence(message)


def send_trap(host, port=TRAP_PORT, community="public"):
    """Send sample SNMP v2c traps"""
    
    print(f"Sending SNMP v2c traps to {host}:{port}")
    print(f"Community: {community}\n")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Example 1: Simple trap with string value
    print("[1] Sending trap: System Alert")
    trap1 = build_snmp_v2c_trap(
        community=community,
        trap_oid="1.3.6.1.4.1.99999.1.1",  # Enterprise-specific OID
        varbinds=[
            ("1.3.6.1.4.1.99999.2.1", "string", "System temperature high"),
            ("1.3.6.1.4.1.99999.2.2", "int", 85),
        ],
        request_id=1001
    )
    sock.sendto(trap1, (host, port))
    time.sleep(1)
    
    # Example 2: Trap with multiple data types
    print("[2] Sending trap: Interface Status")
    trap2 = build_snmp_v2c_trap(
        community=community,
        trap_oid="1.3.6.1.6.3.1.1.5.3",  # Standard linkDown trap
        varbinds=[
            ("1.3.6.1.2.1.2.2.1.1", "int", 2),  # ifIndex
            ("1.3.6.1.2.1.2.2.1.2", "string", "eth0"),  # ifDescr
            ("1.3.6.1.2.1.2.2.1.7", "int", 2),  # ifAdminStatus (down)
        ],
        request_id=1002
    )
    sock.sendto(trap2, (host, port))
    time.sleep(1)
    
    # Example 3: Custom enterprise trap
    print("[3] Sending trap: Application Event")
    trap3 = build_snmp_v2c_trap(
        community=community,
        trap_oid="1.3.6.1.4.1.99999.1.2",
        varbinds=[
            ("1.3.6.1.4.1.99999.3.1", "string", "Application XYZ"),
            ("1.3.6.1.4.1.99999.3.2", "string", "Service restarted"),
            ("1.3.6.1.4.1.99999.3.3", "int", 3),  # Restart count
            ("1.3.6.1.4.1.99999.3.4", "string", "Server-01"),
        ],
        request_id=1003
    )
    sock.sendto(trap3, (host, port))
    
    print(f"\n✓ Sent 3 traps successfully")
    sock.close()


if __name__ == "__main__":
    import sys
    
    host = "localhost"
    port = TRAP_PORT
    community = "public"
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Invalid port: {sys.argv[2]}")
            sys.exit(1)
    if len(sys.argv) > 3:
        community = sys.argv[3]
    
    print("\nSNMP v2c Trap Sender")
    print("=" * 50)
    send_trap(host, port, community)
