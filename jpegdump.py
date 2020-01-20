# Copyright (c) Victor Derks.
# SPDX-License-Identifier: MIT

import sys
from enum import IntEnum, unique
from typing import BinaryIO


@unique
class JpegMarker(IntEnum):
    START_OF_IMAGE = 0xD8  # SOI
    END_OF_IMAGE = 0xD9  # EOI
    START_OF_SCAN = 0xDA  # SOS
    START_OF_FRAME_JPEGLS = 0xF7  # SOF_55: Marks the start of a (JPEG-LS) encoded frame.
    JPEGLS_EXTENDED_PARAMETERS = 0xF8  # LSE: JPEG-LS extended parameters.
    APPLICATION_DATA0 = 0xE0  # APP0: Application data 0: used for JFIF header.
    APPLICATION_DATA7 = 0xE7  # APP7: Application data 7: color space.
    APPLICATION_DATA8 = 0xE8  # APP8: Application data 8: colorXForm.
    COMMENT = 0xFE  # COM:  Comment block.


class JpegReader:
    def __init__(self, file: BinaryIO) -> None:
        self.file = file
        self.jpegls_stream = False
        self.dump_functions = {JpegMarker.START_OF_IMAGE: self._dump_start_of_image_marker,
                               JpegMarker.END_OF_IMAGE: self._dump_end_of_image,
                               JpegMarker.START_OF_FRAME_JPEGLS: self._dump_start_of_frame_jpegls,
                               JpegMarker.START_OF_SCAN: self._dump_start_of_scan}
        self.interleave_names = ["None", "Line interleaved", "Sample interleaved"]

    def dump(self) -> None:
        byte = self._read_bytes()
        while byte:
            if byte[0] == 0xFF:
                byte = self._read_byte()
                if self._is_marker_code(byte):
                    self._dump_marker_code(byte)
            byte = self._read_bytes()

    def _read_bytes(self) -> bytes:
        return self.file.read(1)

    def _read_byte(self) -> int:
        return self.file.read(1)[0]

    def _read_uint16_big_endian(self) -> int:
        return self._read_byte() << 8 | self._read_byte()

    def _is_marker_code(self, marker_code: int) -> bool:
        # To prevent marker codes in the encoded bit stream encoders must encode the next byte zero or
        # the next bit zero (jpeg-ls).
        if self.jpegls_stream:
            return (marker_code & 0x80) == 0x80
        return marker_code > 0

    def _dump_marker_code(self, marker_code: int) -> None:
        dump_function = self.dump_functions.get(marker_code, None)
        if dump_function is None:
            self._dump_unknown_marker(marker_code)
        else:
            dump_function()

    def _dump_start_of_image_marker(self) -> None:
        print(f"{self._get_start_offset:8} Marker 0xFFD8: SOI (Start Of Image), defined in ITU T.81/IEC 10918-1")

    def _dump_end_of_image(self) -> None:
        print(f"{self._get_start_offset:8} Marker 0xFFD9. EOI (End Of Image), defined in ITU T.81/IEC 10918-1")

    def _dump_start_of_frame_jpegls(self) -> None:
        print(f"{self._get_start_offset:8} Marker 0xFFF7: SOF_55 (Start Of Frame JPEG-LS),"
              f" defined in ITU T.87/IEC 14495-1 JPEG LS")
        print(f"{self._position:8}  Size = {self._read_uint16_big_endian()}")
        print(f"{self._position:8}  Sample precision (P) = {self._read_byte()}")
        print(f"{self._position:8}  Number of lines (Y) = {self._read_uint16_big_endian()}")
        print(f"{self._position:8}  Number of samples per line (X) = {self._read_uint16_big_endian()}")
        position: int = self._position
        component_count: int = self._read_byte()
        print(f"{position:8}  Number of image components in a frame (Nf) = {component_count}",)
        for _ in range(component_count):
            print(f"{self._position:8}   Component identifier (Ci) = {self._read_byte()}")
            position = self._position
            sampling_factor: int = self._read_byte()
            print(f"{position:8}   H and V sampling factor (Hi + Vi) = {sampling_factor}"
                  f" ({sampling_factor >> 4} + {sampling_factor & 0xF})") 
            print(f"{self._position:8}   Quantization table (Tqi) [reserved, should be 0] = {self._read_byte()}")
        self.jpegls_stream = True

    def _dump_start_of_scan(self) -> None:
        print(f"{self._get_start_offset:8} Marker 0xFFDA: SOS (Start Of Scan), defined in ITU T.81/IEC 10918-1")
        print(f"{self._position:8}  Size = {self._read_uint16_big_endian()}")
        print(f"{self._position:8}  Component Count = ", end='')
        component_count: int = self._read_byte()
        print(component_count)
        for _ in range(component_count):
            print(f"{self._position:8}   Component identifier (Ci) = {self._read_byte()}")
            print(f"{self._position:8}   Mapping table selector = {self._read_byte()}")
        print(f"{self._position:8}  Near lossless (NEAR parameter) = {self._read_byte()}")
        print(f"{self._position:8}  Interleave mode (ILV parameter) = ", end='')
        interleave_mode: int = self._read_byte()
        print(f"{interleave_mode} ({self._get_interleave_mode_name(interleave_mode)})")
        print(f"{self._position:8}  Point Transform = {self._read_byte()}")

    def _dump_unknown_marker(self, marker_code: int) -> None:
        print(f"{self._get_start_offset :8} Marker 0xFF{marker_code:02X}")

    def _get_interleave_mode_name(self, interleave_mode: int) -> str:
        return self.interleave_names[interleave_mode] if interleave_mode < len(self.interleave_names) else "Invalid"

    @property
    def _position(self) -> int:
        return self.file.tell()

    @property
    def _get_start_offset(self) -> int:
        return self._position - 2


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: jpegdump <filename>")
        return 64  # os.EX_USAGE

    try:
        with open(sys.argv[1], "rb") as jpeg_file:
            print(f"Dumping JPEG file: {sys.argv[1]}")
            print("=============================================================================")

            reader = JpegReader(jpeg_file)
            reader.dump()
            return 0  # os.EX_OK
    except FileNotFoundError:
        print("Error opening the file")
        return 74  # os.EX_IOERR


main()
