# Copyright (c) Victor Derks.
# SPDX-License-Identifier: MIT

import sys
from enum import Enum, unique
from typing import BinaryIO


@unique
class JpegMarker(Enum):
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
        self.dump_functions = {JpegMarker.START_OF_IMAGE: self.dump_start_of_image_marker}

    def read_byte(self) -> bytes:
        return self.file.read(1)

    def is_marker_code(self, marker_code) -> bool:
        # To prevent marker codes in the encoded bit stream encoders must encode the next byte zero or
        # the next bit zero (jpeg-ls).
        if self.jpegls_stream:
            return (marker_code & 0x80) == 0X80
        return marker_code > 0

    def dump_marker_code(self, marker_code) -> None:
        dump_function = self.dump_functions.get(marker_code, self.dump_unknown_marker)
        dump_function(marker_code)

    def dump_start_of_image_marker(self):
        pass

    def dump_unknown_marker(self, marker_code) -> None:
        print(f"{self.get_start_offset():8} Marker 0xFF{marker_code:02X}");

    def get_start_offset(self) -> int:
        return self.file.tell() - 2;

    def dump(self) -> None:
        byte = self.read_byte()
        while byte:
            if byte[0] == 0xFF:
                byte = self.read_byte()
                if self.is_marker_code(byte[0]):
                    self.dump_marker_code(byte[0])
            byte = self.read_byte()


if len(sys.argv) < 2:
    print("Usage: jpegdump <filename>")
    raise SystemExit(1)

try:
    with open(sys.argv[1], "rb") as jpeg_file:
        print(f"Dumping JPEG file: {sys.argv[1]}")
        print("=============================================================================")

        reader = JpegReader(jpeg_file)
        reader.dump()
except FileNotFoundError:
    print("Error opening the file")
