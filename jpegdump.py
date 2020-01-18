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
        self.dump_functions = {JpegMarker.START_OF_IMAGE: self.__dump_start_of_image_marker}

    def dump(self) -> None:
        byte = self.__read_byte()
        while byte:
            if byte[0] == 0xFF:
                byte = self.__read_byte()
                if self.__is_marker_code(byte[0]):
                    self.__dump_marker_code(byte[0])
            byte = self.__read_byte()

    def __read_byte(self) -> bytes:
        return self.file.read(1)

    def __is_marker_code(self, marker_code: int) -> bool:
        # To prevent marker codes in the encoded bit stream encoders must encode the next byte zero or
        # the next bit zero (jpeg-ls).
        if self.jpegls_stream:
            return (marker_code & 0x80) == 0X80
        return marker_code > 0

    def __dump_marker_code(self, marker_code: int) -> None:
        dump_function = self.dump_functions.get(marker_code, None)
        if dump_function == None:
            self.__dump_unknown_marker(marker_code)
        else:
            dump_function()

    def __dump_start_of_image_marker(self) -> None:
        print(f"{self.__get_start_offset():8} Marker 0xFFD8: SOI (Start Of Image), defined in ITU T.81/IEC 10918-1")

    def __dump_unknown_marker(self, marker_code: int) -> None:
        print(f"{self.__get_start_offset():8} Marker 0xFF{marker_code:02X}")

    def __get_start_offset(self) -> int:
        return self.file.tell() - 2


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