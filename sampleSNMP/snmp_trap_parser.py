#!/usr/bin/env python3
"""
Simple SNMP Trap Parser - No external SNMP libraries
Parses SNMP v1 and v2c traps using raw socket and manual BER decoding
"""

import socket
import struct
from datetime import datetime

# SNMP Trap Port
TRAP_PORT = 162

# ASN.1 BER Type Tags
ASN1_SEQUENCE = 0x30
ASN1_INTEGER = 0x02
ASN1_OCTET_STRING = 0x04
ASN1_NULL = 0x05
ASN1_OBJECT_IDENTIFIER = 0x06
ASN1_IPADDRESS = 0x40
ASN1_COUNTER32 = 0x41
ASN1_GAUGE32 = 0x42
ASN1_TIMETICKS = 0x43
ASN1_OPAQUE = 0x44
ASN1_COUNTER64 = 0x46

# SNMP PDU Types
SNMP_GET_REQUEST = 0xA0
SNMP_GET_NEXT_REQUEST = 0xA1
SNMP_GET_RESPONSE = 0xA2
SNMP_SET_REQUEST = 0xA3
SNMP_TRAP_V1 = 0xA4
SNMP_GET_BULK_REQUEST = 0xA5
SNMP_INFORM_REQUEST = 0xA6
SNMP_TRAP_V2 = 0xA7
SNMP_REPORT = 0xA8


class BERDecoder:
    """Basic Encoding Rules (BER) Decoder for SNMP"""
    
    def __init__(self, data):
        self.data = data
        self.pos = 0
    
    def decode_length(self):
        """Decode BER length field"""
        length = self.data[self.pos]
        self.pos += 1
        
        if length & 0x80:  # Long form
            num_octets = length & 0x7F
            length = 0
            for _ in range(num_octets):
                length = (length << 8) | self.data[self.pos]
                self.pos += 1
        
        return length
    
    def decode_integer(self):
        """Decode BER integer"""
        tag = self.data[self.pos]
        self.pos += 1
        
        if tag != ASN1_INTEGER:
            raise ValueError(f"Expected INTEGER tag, got 0x{tag:02x}")
        
        length = self.decode_length()
        value = 0
        
        # Handle signed integers
        is_negative = self.data[self.pos] & 0x80
        
        for i in range(length):
            value = (value << 8) | self.data[self.pos]
            self.pos += 1
        
        # Convert to signed if necessary
        if is_negative:
            value -= (1 << (length * 8))
        
        return value
    
    def decode_octet_string(self):
        """Decode BER octet string"""
        tag = self.data[self.pos]
        self.pos += 1
        
        if tag != ASN1_OCTET_STRING:
            raise ValueError(f"Expected OCTET STRING tag, got 0x{tag:02x}")
        
        length = self.decode_length()
        value = self.data[self.pos:self.pos + length]
        self.pos += length
        
        try:
            return value.decode('utf-8')
        except:
            return value.hex()
    
    def decode_oid(self):
        """Decode BER Object Identifier"""
        tag = self.data[self.pos]
        self.pos += 1
        
        if tag != ASN1_OBJECT_IDENTIFIER:
            raise ValueError(f"Expected OID tag, got 0x{tag:02x}")
        
        length = self.decode_length()
        end_pos = self.pos + length
        
        if length == 0:
            return "0.0"
        
        # First byte encodes first two subidentifiers
        first_byte = self.data[self.pos]
        self.pos += 1
        
        oid = [first_byte // 40, first_byte % 40]
        
        # Decode remaining subidentifiers
        while self.pos < end_pos:
            subid = 0
            while True:
                byte = self.data[self.pos]
                self.pos += 1
                subid = (subid << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
            oid.append(subid)
        
        return '.'.join(map(str, oid))
    
    def decode_null(self):
        """Decode BER NULL"""
        tag = self.data[self.pos]
        self.pos += 1
        
        if tag != ASN1_NULL:
            raise ValueError(f"Expected NULL tag, got 0x{tag:02x}")
        
        length = self.decode_length()
        return None
    
    def decode_ip_address(self):
        """Decode SNMP IP Address"""
        tag = self.data[self.pos]
        self.pos += 1
        
        if tag != ASN1_IPADDRESS:
            raise ValueError(f"Expected IP ADDRESS tag, got 0x{tag:02x}")
        
        length = self.decode_length()
        ip_bytes = self.data[self.pos:self.pos + length]
        self.pos += length
        
        return '.'.join(map(str, ip_bytes))
    
    def decode_timeticks(self):
        """Decode SNMP TimeTicks"""
        tag = self.data[self.pos]
        self.pos += 1
        
        if tag != ASN1_TIMETICKS:
            raise ValueError(f"Expected TIMETICKS tag, got 0x{tag:02x}")
        
        length = self.decode_length()
        value = 0
        
        for _ in range(length):
            value = (value << 8) | self.data[self.pos]
            self.pos += 1
        
        return value
    
    def decode_counter32(self):
        """Decode SNMP Counter32"""
        tag = self.data[self.pos]
        self.pos += 1
        
        if tag != ASN1_COUNTER32:
            raise ValueError(f"Expected COUNTER32 tag, got 0x{tag:02x}")
        
        length = self.decode_length()
        value = 0
        
        for _ in range(length):
            value = (value << 8) | self.data[self.pos]
            self.pos += 1
        
        return value
    
    def decode_gauge32(self):
        """Decode SNMP Gauge32"""
        tag = self.data[self.pos]
        self.pos += 1
        
        if tag != ASN1_GAUGE32:
            raise ValueError(f"Expected GAUGE32 tag, got 0x{tag:02x}")
        
        length = self.decode_length()
        value = 0
        
        for _ in range(length):
            value = (value << 8) | self.data[self.pos]
            self.pos += 1
        
        return value
    
    def decode_value(self):
        """Decode any BER value based on tag"""
        tag = self.data[self.pos]
        
        if tag == ASN1_INTEGER:
            return ("INTEGER", self.decode_integer())
        elif tag == ASN1_OCTET_STRING:
            return ("OCTET STRING", self.decode_octet_string())
        elif tag == ASN1_OBJECT_IDENTIFIER:
            return ("OID", self.decode_oid())
        elif tag == ASN1_NULL:
            return ("NULL", self.decode_null())
        elif tag == ASN1_IPADDRESS:
            return ("IpAddress", self.decode_ip_address())
        elif tag == ASN1_TIMETICKS:
            return ("TimeTicks", self.decode_timeticks())
        elif tag == ASN1_COUNTER32:
            return ("Counter32", self.decode_counter32())
        elif tag == ASN1_GAUGE32:
            return ("Gauge32", self.decode_gauge32())
        else:
            # Skip unknown types
            self.pos += 1
            length = self.decode_length()
            value = self.data[self.pos:self.pos + length]
            self.pos += length
            return (f"Unknown(0x{tag:02x})", value.hex())


def parse_snmp_v2c_trap(data):
    """Parse SNMP v2c trap message"""
    decoder = BERDecoder(data)
    
    print(f"\n{'='*70}")
    print(f"SNMP Trap Received at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    try:
        # SEQUENCE tag
        if decoder.data[decoder.pos] != ASN1_SEQUENCE:
            print(f"Error: Expected SEQUENCE, got 0x{decoder.data[decoder.pos]:02x}")
            return
        decoder.pos += 1
        msg_length = decoder.decode_length()
        
        # SNMP Version
        version = decoder.decode_integer()
        version_str = {0: "v1", 1: "v2c", 2: "v2u", 3: "v3"}.get(version, f"Unknown({version})")
        print(f"SNMP Version: {version_str}")
        
        # Community String
        community = decoder.decode_octet_string()
        print(f"Community: {community}")
        
        # PDU
        pdu_type = decoder.data[decoder.pos]
        decoder.pos += 1
        pdu_length = decoder.decode_length()
        
        pdu_type_name = {
            SNMP_TRAP_V1: "SNMPv1 Trap",
            SNMP_TRAP_V2: "SNMPv2 Trap",
            SNMP_INFORM_REQUEST: "Inform Request",
            SNMP_GET_RESPONSE: "Get Response"
        }.get(pdu_type, f"Unknown PDU (0x{pdu_type:02x})")
        
        print(f"PDU Type: {pdu_type_name}")
        
        if pdu_type == SNMP_TRAP_V1:
            # SNMPv1 Trap - different structure
            parse_v1_trap_pdu(decoder)
        else:
            # SNMPv2c Trap or Inform
            parse_v2c_trap_pdu(decoder)
        
    except Exception as e:
        print(f"Error parsing trap: {e}")
        import traceback
        traceback.print_exc()


def parse_v1_trap_pdu(decoder):
    """Parse SNMPv1 Trap PDU"""
    # Enterprise OID
    enterprise = decoder.decode_oid()
    print(f"Enterprise OID: {enterprise}")
    
    # Agent Address
    agent_addr = decoder.decode_ip_address()
    print(f"Agent Address: {agent_addr}")
    
    # Generic Trap Type
    generic_trap = decoder.decode_integer()
    generic_names = {
        0: "coldStart",
        1: "warmStart", 
        2: "linkDown",
        3: "linkUp",
        4: "authenticationFailure",
        5: "egpNeighborLoss",
        6: "enterpriseSpecific"
    }
    print(f"Generic Trap: {generic_names.get(generic_trap, generic_trap)}")
    
    # Specific Trap Type
    specific_trap = decoder.decode_integer()
    print(f"Specific Trap: {specific_trap}")
    
    # Timestamp
    timestamp = decoder.decode_timeticks()
    print(f"Timestamp: {timestamp} ({timestamp/100:.2f} seconds)")
    
    # Variable Bindings
    parse_varbinds(decoder)


def parse_v2c_trap_pdu(decoder):
    """Parse SNMPv2c Trap PDU"""
    # Request ID
    request_id = decoder.decode_integer()
    print(f"Request ID: {request_id}")
    
    # Error Status
    error_status = decoder.decode_integer()
    print(f"Error Status: {error_status}")
    
    # Error Index
    error_index = decoder.decode_integer()
    print(f"Error Index: {error_index}")
    
    # Variable Bindings
    parse_varbinds(decoder)


def parse_varbinds(decoder):
    """Parse Variable Bindings"""
    # VarBind List SEQUENCE
    if decoder.data[decoder.pos] != ASN1_SEQUENCE:
        print(f"Error: Expected varbind SEQUENCE")
        return
    
    decoder.pos += 1
    varbind_list_length = decoder.decode_length()
    end_pos = decoder.pos + varbind_list_length
    
    print(f"\nVariable Bindings:")
    print("-" * 70)
    
    varbind_num = 1
    while decoder.pos < end_pos:
        # Each VarBind is a SEQUENCE
        if decoder.data[decoder.pos] != ASN1_SEQUENCE:
            break
        
        decoder.pos += 1
        varbind_length = decoder.decode_length()
        
        # OID
        oid = decoder.decode_oid()
        
        # Value
        value_type, value = decoder.decode_value()
        
        print(f"  [{varbind_num}] {oid}")
        print(f"       Type: {value_type}, Value: {value}")
        
        varbind_num += 1
    
    print("=" * 70)


def start_trap_listener(port=TRAP_PORT):
    """Start listening for SNMP traps"""
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(('', port))
        print(f"\nSNMP Trap Listener started on port {port}")
        print(f"Waiting for traps... (Press Ctrl+C to stop)\n")
        
        while True:
            data, addr = sock.recvfrom(65535)
            print(f"\nReceived {len(data)} bytes from {addr[0]}:{addr[1]}")
            parse_snmp_v2c_trap(data)
            
    except KeyboardInterrupt:
        print("\n\nStopping trap listener...")
    except PermissionError:
        print(f"\nError: Permission denied to bind to port {port}")
        print(f"Try running with sudo: sudo python3 {__file__}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    import sys
    
    port = TRAP_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    start_trap_listener(port)
