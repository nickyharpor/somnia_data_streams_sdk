"""Schema encoder for ABI encoding/decoding."""

import re
from typing import List, Any, Dict, Tuple, Optional
from eth_abi import encode, decode
from eth_utils import to_bytes, to_hex
from eth_typing import HexStr

from somnia_data_streams_sdk.types import SchemaItem, SchemaDecodedItem

TUPLE_TYPE = "tuple"
BYTES32 = "bytes32"
ADDRESS = "address"
BOOL = "bool"
IPFS_HASH = "ipfsHash"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class SchemaEncoder:
    """Encode and decode data according to Solidity schemas."""
    
    def __init__(self, schema: str) -> None:
        """
        Initialize schema encoder.
        
        Args:
            schema: Schema string (e.g., "uint256 value, address owner")
        """
        self.schema: List[Dict[str, Any]] = []
        self.abi_types: List[str] = []
        self.abi_names: List[str] = []
        
        # Replace ipfsHash with bytes32
        fixed_schema = schema.replace(IPFS_HASH, BYTES32)
        
        # Parse the schema
        self._parse_schema(fixed_schema)
    
    def _parse_schema(self, schema: str) -> None:
        """Parse schema string into structured format."""
        if not schema or not schema.strip():
            return
        
        # Split by comma (but not within parentheses for tuples)
        parts = self._split_schema(schema)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Handle tuple types
            if part.startswith("("):
                type_str, name = self._parse_tuple_type(part)
                signature = f"{type_str} {name}" if name else type_str
            else:
                # Regular type: "type name" or just "type"
                tokens = part.rsplit(None, 1)
                if len(tokens) == 2:
                    type_str, name = tokens
                else:
                    type_str = tokens[0]
                    name = ""
                signature = part
            
            # Determine if it's an array
            is_array = "[]" in type_str
            type_name = type_str.replace("[]", "")
            
            # Get default value
            default_value = self._get_default_value(type_name)
            if is_array:
                default_value = []
            
            self.schema.append({
                "name": name,
                "type": type_str,
                "signature": signature,
                "value": default_value,
            })
            
            self.abi_types.append(type_str)
            self.abi_names.append(name)
    
    def _split_schema(self, schema: str) -> List[str]:
        """Split schema by commas, respecting parentheses."""
        parts = []
        current = ""
        depth = 0
        
        for char in schema:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(current)
                current = ""
                continue
            current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    def _parse_tuple_type(self, part: str) -> Tuple[str, str]:
        """Parse tuple type definition."""
        # Extract tuple components and name
        # Format: (type1,type2,...) name or (type1,type2,...)[]
        match = re.match(r'\(([^)]+)\)((?:\[\])?)(?:\s+(\w+))?', part)
        if not match:
            raise ValueError(f"Invalid tuple format: {part}")
        
        components = match.group(1)
        array_suffix = match.group(2) or ""
        name = match.group(3) or ""
        
        type_str = f"({components}){array_suffix}"
        return type_str, name
    
    def _get_default_value(self, type_name: str) -> Any:
        """Get default value for a type."""
        if type_name == BOOL:
            return False
        elif "int" in type_name:
            return 0
        elif type_name == ADDRESS:
            return ZERO_ADDRESS
        elif type_name.startswith("bytes"):
            return b""
        elif type_name == "string":
            return ""
        else:
            return ""
    
    def encode_data(self, params: List[SchemaItem]) -> HexStr:
        """
        Encode data according to schema.
        
        Args:
            params: List of schema items to encode
            
        Returns:
            Hex-encoded data
            
        Raises:
            ValueError: If params don't match schema
        """
        if len(params) != len(self.schema):
            raise ValueError("Invalid number of values")
        
        data = []
        
        for i, schema_item in enumerate(self.schema):
            param = params[i]
            
            # Validate type
            sanitized_type = param.type.replace(" ", "")
            schema_type = schema_item["type"]
            schema_sig = schema_item["signature"]
            
            if (sanitized_type != schema_type and 
                sanitized_type != schema_sig and
                not (sanitized_type == IPFS_HASH and schema_type == BYTES32)):
                raise ValueError(f"Incompatible param type: {sanitized_type}")
            
            # Validate name
            if param.name != schema_item["name"]:
                raise ValueError(f"Incompatible param name: {param.name}")
            
            # Handle value conversion based on type
            value = param.value
            
            # Convert address strings to checksum format
            if schema_type == ADDRESS and isinstance(value, str):
                from eth_utils import to_checksum_address
                value = to_checksum_address(value)
            
            # Handle bytes32 conversion
            elif schema_type == BYTES32:
                if isinstance(value, str):
                    if value.startswith("0x") or value.startswith("0X"):
                        # Convert hex string to bytes
                        value = to_bytes(hexstr=value)
                    else:
                        # Convert regular string to bytes32
                        value = value.encode().ljust(32, b'\x00')[:32]
            
            data.append(value)
        
        # Encode using eth_abi
        encoded = encode(self.abi_types, data)
        return HexStr(to_hex(encoded))
    
    def decode_data(self, data: HexStr) -> List[SchemaDecodedItem]:
        """
        Decode data according to schema.
        
        Args:
            data: Hex-encoded data
            
        Returns:
            List of decoded schema items
        """
        # Convert hex to bytes
        data_bytes = to_bytes(hexstr=data)
        
        # Decode using eth_abi
        values = decode(self.abi_types, data_bytes)
        
        # Build decoded items
        result = []
        for i, schema_item in enumerate(self.schema):
            value = values[i]
            
            # Convert bytes to hex strings
            if isinstance(value, bytes):
                value = to_hex(value)
            
            decoded_item = SchemaDecodedItem(
                name=schema_item["name"],
                type=schema_item["type"],
                signature=schema_item["signature"],
                value=SchemaItem(
                    name=schema_item["name"],
                    type=schema_item["type"],
                    value=value,
                ),
            )
            result.append(decoded_item)
        
        return result
    
    @staticmethod
    def is_schema_valid(schema: str) -> bool:
        """
        Check if a schema is valid.
        
        Args:
            schema: Schema string to validate
            
        Returns:
            True if valid
        """
        try:
            SchemaEncoder(schema)
            return True
        except Exception:
            return False
    
    def is_encoded_data_valid(self, data: HexStr) -> bool:
        """
        Check if encoded data is valid for this schema.
        
        Args:
            data: Hex-encoded data
            
        Returns:
            True if valid
        """
        try:
            self.decode_data(data)
            return True
        except Exception:
            return False
