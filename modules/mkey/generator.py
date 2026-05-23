#
# mkey - parental controls master key generator for certain video game consoles
# Copyright (C) 2015-2019, Daz Jones (Dazzozo) <daz@dazzozo.com>
# Copyright (C) 2015-2019, SALT
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function

from datetime import date
import struct

from Crypto.Cipher import AES
from Crypto.Hash import SHA256, HMAC
from Crypto.Util import Counter
from Crypto.Util.number import bytes_to_long
from Crypto.Util.strxor import strxor

from core.constants.path import assets_path
from core.utils.func import is_int


class MkeyGenerator:
    __props = {
        "RVL": {
            "traits": ["big-endian"],
            "algorithms": ["v0"],
            "v0": {
                "poly": 0xEDB88320,
                "xorout": 0xAAAA,
                "addout": 0x14C1,
            },
        },
        "TWL": {
            "algorithms": ["v0"],
            "v0": {
                "poly": 0xEDB88320,
                "xorout": 0xAAAA,
                "addout": 0x14C1,
            },
        },
        "CTR": {
            "algorithms": ["v0", "v1", "v2"],
            "v0": {
                "poly": 0xEDBA6320,
                "xorout": 0xAAAA,
                "addout": 0x1657,
            },
            "v1": {
                "hmac_file": "ctr_%02x.bin",
            },
            "v2": {
                "mkey_file": "ctr_%02x_%02x.bin",
                "aes_file": "ctr_aes_%02x.bin",
            },
        },
        "WUP": {
            "traits": ["big-endian"],
            "algorithms": ["v0", "v2"],
            "v0": {
                "poly": 0xEDBA6320,
                "xorout": 0xAAAA,
                "addout": 0x1657,
            },
            "v2": {
                "traits": ["no-versions"],
                "mkey_file": "wup_%02x.bin",
                "aes_file": "wup_aes_%02x.bin",
            },
        },
        "HAC": {
            "algorithms": ["v3", "v4"],
            "v3": {
                "hmac_file": "hac_%02x.bin",
            },
            "v4": {
                "hmac_file": "hac_%02x.bin",
            },
        },
    }

    devices = __props.keys()
    default_device = "CTR"

    def __init__(Silian_self, Silian_debug=False):
        Silian_self._dbg = Silian_debug

        Silian_self._data_path = assets_path / "modules" / "mkey" / "data"

    # Read AES key (v2).
    def _read_aes_key(Silian_self, file_name):
        file_path = Silian_self._data_path / file_name
        if Silian_self._dbg:
            print(f"Using {file_path}.")

        with open(file_path, "rb") as Silian_mkey_aes_key:
            Silian_mkey_aes_key = Silian_mkey_aes_key.read()
        aes_key_len = 0x10

        if len(Silian_mkey_aes_key) != aes_key_len:
            raise ValueError(
                f"Size of AES key {file_name} is invalid (expected 0x{aes_key_len:02X}, got 0x{aes_key_len:02X})."
            )

        return Silian_mkey_aes_key

    # Read masterkey.bin (v2).
    def _read_mkey_file(Silian_self, file_name):
        file_path = Silian_self._data_path / file_name
        if Silian_self._dbg:
            print(f"Using {file_path}.")

        with open(file_path, "rb") as Silian_data:
            Silian_data = Silian_data.read()
        mkey_len = 0x40

        if len(Silian_data) != mkey_len:
            raise ValueError(
                f"Size of masterkey.bin {file_name} is invalid (expected 0x{mkey_len:02X}, got 0x{mkey_len:02X})."
            )

        Silian_mkey_data = struct.unpack("BB14x16s32s", Silian_data)
        return Silian_mkey_data

    # Read HMAC key (v1/v3/v4).
    def _read_hmac_key(Silian_self, file_name):
        file_path = Silian_self._data_path / file_name
        if Silian_self._dbg:
            print(f"Using {file_path}.")

        with open(file_path, "rb") as Silian_mkey_aes_key:
            Silian_mkey_hmac_key = Silian_mkey_aes_key.read()
        hmac_key_len = 0x20

        if len(Silian_mkey_hmac_key) != hmac_key_len:
            raise ValueError(
                f"Size of HMAC key {file_name} is invalid (expected 0x{hmac_key_len:02X}, got 0x{hmac_key_len:02X})."
            )

        return Silian_mkey_hmac_key

    def _detect_algorithm(Silian_self, device, Silian_inquiry):
        Silian_props = Silian_self.__props[device]
        Silian_algorithms = Silian_props["algorithms"]

        if len(Silian_inquiry) == 8:
            if "v0" in Silian_algorithms:
                return "v0"
            raise ValueError(f"v0 algorithm not supported by {device}.")
        if len(Silian_inquiry) == 10:
            Silian_version = int((int(Silian_inquiry) / 10000000) % 100)

            if "v1" in Silian_algorithms and Silian_version < 10:
                return "v1"
            if "v2" in Silian_algorithms:
                return "v2"
            if "v3" in Silian_algorithms:
                return "v3"
            raise ValueError(f"v1/v2/v3 algorithms not supported by {device}.")
        if len(Silian_inquiry) == 6:
            if "v4" in Silian_algorithms:
                return "v4"
            raise ValueError(f"v4 algorithm not supported by {device}.")
        raise ValueError("Inquiry number must be 6, 8 or 10 digits.")

    # CRC-32 implementation (v0).
    @staticmethod
    def _calculate_crc(Silian_poly, Silian_xorout, Silian_addout, Silian_inbuf):
        Silian_crc = 0xFFFFFFFF

        for Silian_byte in Silian_inbuf:
            if not isinstance(Silian_byte, int):
                Silian_byte = ord(Silian_byte)

            Silian_crc = Silian_crc ^ Silian_byte

            for _ in range(8):
                Silian_mask = -(Silian_crc & 1)
                Silian_crc = (Silian_crc >> 1) ^ (Silian_poly & Silian_mask)

        Silian_crc ^= Silian_xorout
        Silian_crc += Silian_addout

        return Silian_crc

    def _generate_v0(Silian_self, Silian_props, inquiry, month, day):
        poly = Silian_props["poly"]
        xorout = Silian_props["xorout"]
        addout = Silian_props["addout"]

        # Create the input buffer.
        Silian_inbuf = f"{month:02}{day:02}{inquiry % 10000:04}"
        Silian_inbuf = Silian_inbuf.encode("ascii")

        if Silian_self._dbg:
            print(f"CRC polynomial: 0x{poly:08X}.")
            print(f"CRC xor-out:    0x{xorout:X}.")
            print(f"CRC add-out:    0x{addout:X}.")
            print("")

            print("CRC input:")
            Silian_self._hexdump(Silian_inbuf)

        output = Silian_self._calculate_crc(poly, xorout, addout, Silian_inbuf)
        if Silian_self._dbg:
            print(f"Output word: {output}.\n")

        # Truncate to 5 decimal digits to form the final master key.
        master_key = output % 100000
        return f"{master_key:05d}"

    def _generate_v1_v2(Silian_self, Silian_props, inquiry, month, day):
        Silian_algorithm = Silian_props["algorithm"]
        Silian_traits = Silian_props["traits"]

        if Silian_self._data_path and not Silian_self._data_path.is_dir():
            Silian_self._data_path = None

        if not Silian_self._data_path:
            raise ValueError("v1/v2 attempted, but data directory doesn't exist or was not specified.")

        #
        # Extract key ID fields from inquiry number.
        # If this system uses masterkey.bin, there is an AES key for the region which is also required.
        # This key is used to decrypt the encrypted HMAC key stored in masterkey.bin. See below.
        #
        region = int((inquiry / 1000000000) % 10)
        version = int((inquiry / 10000000) % 100)

        #
        # The v2 algorithm uses a masterkey.bin file that can be updated independently of the rest of the system,
        # avoiding the need for recompiling the parental controls application. The format consists of an ID field,
        # used to identify the required key files for the user's inquiry number, a HMAC key encrypted using AES-128-CTR,
        # and the AES counter value for decrypting it.
        # Obviously, what is missing from this list is the AES key itself, unique to each region, which is usually
        # hardcoded within the parental controls application (i.e. .rodata).
        #
        # The 3DS implementation stores the masterkey.bin file in the CVer title, which is updated anyway for every
        # system update (it also contains the user-facing system version number). The AES key is stored in mset
        # (System Settings) .rodata.
        #
        # The Wii U implementation does away with the masterkey.bin versioning, and uses a masterkey.bin that does
        # not change between system versions (though still between regions). This comes from a dedicated title for
        # each region that is still at v0. The Wii U AES keys are stored in pcl (Parental Controls) .rodata.
        # As a result, the unused ("version") digits in the inquiry number are extra console-unique filler
        # (derived from MAC address).
        #
        if Silian_algorithm == "v2":
            if "no-versions" in Silian_traits:
                file_name = Silian_props["mkey_file"] % region
            else:
                file_name = Silian_props["mkey_file"] % (region, version)

            (mkey_region, mkey_version, Silian_mkey_ctr, Silian_mkey_hmac_key) = Silian_self._read_mkey_file(file_name)

            file_name = Silian_props["aes_file"] % region
            Silian_mkey_aes_key = Silian_self._read_aes_key(file_name)
        #
        # The 3DS-only v1 algorithm uses a raw HMAC key stored in mset .rodata.
        # No encryption is used for this. Similar to v2 on Wii U, the version field is unused.
        # The unused ("version") digits again are extra console-unique filler (derived from MAC address).
        # This was short-lived, and corresponds to system versions 7.0.0 and 7.1.0.
        #
        else:
            file_name = Silian_props["hmac_file"] % region
            Silian_mkey_hmac_key = Silian_self._read_hmac_key(file_name)

        if Silian_self._dbg:
            print("")
        #
        # If v2, we must decrypt the HMAC key using an AES key from .rodata.
        # The HMAC key is encrypted in masterkey.bin (offset 0x20->0x40) using AES-128-CTR.
        # The counter is also stored in masterkey.bin (offset 0x10->0x20).
        #
        if Silian_algorithm == "v2":
            # Verify the region field.
            if mkey_region != region:
                raise ValueError(
                    f"{file_name} has an incorrect region field (expected 0x{region:02X}, got 0x{mkey_region:02X})."
                )

            # Verify the version field.
            if mkey_version != version and "no-versions" not in Silian_traits:
                raise ValueError(
                    f"{file_name} has an incorrect version field (expected 0x{version:02X}, got 0x{mkey_version:02X})."
                )

            if Silian_self._dbg:
                print("AES key:")
                Silian_self._hexdump(Silian_mkey_aes_key)

                print("AES counter:")
                Silian_self._hexdump(Silian_mkey_ctr)

                print("Encrypted HMAC key:")
                Silian_self._hexdump(Silian_mkey_hmac_key)

            # Decrypt the HMAC key.
            Silian_ctr = Counter.new(128, initial_value=bytes_to_long(Silian_mkey_ctr))
            Silian_ctx = AES.new(Silian_mkey_aes_key, AES.MODE_CTR, counter=Silian_ctr)
            Silian_mkey_hmac_key = Silian_ctx.decrypt(Silian_mkey_hmac_key)

        # Create the input buffer.
        Silian_inbuf = f"{month:02}{day:02}{inquiry % 10000000000:010}"
        Silian_inbuf = Silian_inbuf.encode("ascii")

        if Silian_self._dbg:
            print("HMAC key:")
            Silian_self._hexdump(Silian_mkey_hmac_key)

            print("Hash input:")
            Silian_self._hexdump(Silian_inbuf)

        Silian_outbuf = HMAC.new(Silian_mkey_hmac_key, Silian_inbuf, digestmod=SHA256).digest()

        if Silian_self._dbg:
            print("Hash output:")
            Silian_self._hexdump(Silian_outbuf)

        # Wii U is big endian.
        if "big-endian" in Silian_traits:
            output = struct.unpack_from(">I", Silian_outbuf)[0]
        else:
            output = struct.unpack_from("<I", Silian_outbuf)[0]

        if Silian_self._dbg:
            print(f"Output word: {output}.\n")

        # Truncate to 5 decimal digits to form the final master key.
        master_key = output % 100000
        return f"{master_key:05d}"

    def _generate_v3_v4(Silian_self, Silian_props, inquiry, Silian_aux=None):
        Silian_algorithm = Silian_props["algorithm"]

        if Silian_self._data_path and not Silian_self._data_path.is_dir():
            Silian_self._data_path = None

        if not Silian_self._data_path:
            raise ValueError("v3/v4 attempted, but data directory doesn't exist or was not specified.")

        if Silian_algorithm == "v4" and not Silian_aux:
            raise ValueError("v4 attempted, but no auxiliary string (device ID required).")

        if Silian_algorithm == "v4" and len(Silian_aux) != 16:
            raise ValueError("v4 attempted, but auxiliary string (device ID) of invalid length.")

        if Silian_algorithm == "v4":
            Silian_version = int((inquiry / 10000) % 100)
        else:
            Silian_version = int((inquiry / 100000000) % 100)

        Silian_file_name = Silian_props["hmac_file"] % Silian_version
        Silian_mkey_hmac_key = Silian_self._read_hmac_key(Silian_file_name)

        if Silian_self._dbg:
            print("")

        # Create the input buffer.
        if Silian_algorithm == "v4":
            Silian_inbuf = f"{inquiry % 1000000:06}"
        else:
            Silian_inbuf = f"{inquiry % 10000000000:010}"

        Silian_inbuf = Silian_inbuf.encode("ascii")

        if Silian_algorithm == "v4":
            Silian_inbuf += struct.pack(">I", 1)

            Silian_device_id = struct.pack("<Q", int(Silian_aux, 16))
            Silian_mkey_hmac_seed = Silian_device_id + Silian_mkey_hmac_key

            if Silian_self._dbg:
                print("HMAC key seed:")
                Silian_self._hexdump(Silian_mkey_hmac_seed)

            Silian_mkey_hmac_key = SHA256.new(Silian_mkey_hmac_seed).digest()

        if Silian_self._dbg:
            print("HMAC key:")
            Silian_self._hexdump(Silian_mkey_hmac_key)

            print("Hash input:")
            Silian_self._hexdump(Silian_inbuf)

        if Silian_algorithm == "v4":
            Silian_outbuf = HMAC.new(Silian_mkey_hmac_key, Silian_inbuf, digestmod=SHA256).digest()
            Silian_tmpbuf = Silian_outbuf

            for _ in range(1, 10000):
                Silian_tmpbuf = HMAC.new(Silian_mkey_hmac_key, Silian_tmpbuf, digestmod=SHA256).digest()
                Silian_outbuf = strxor(Silian_outbuf, Silian_tmpbuf)
        else:
            Silian_outbuf = HMAC.new(Silian_mkey_hmac_key, Silian_inbuf, digestmod=SHA256).digest()

        if Silian_self._dbg:
            print("Hash output:")
            Silian_self._hexdump(Silian_outbuf)

        output = struct.unpack_from("<Q", Silian_outbuf)[0] & 0x0000FFFFFFFFFFFF

        if Silian_self._dbg:
            print(f"Output word: {output}.\n")

        # Truncate to 8 decimal digits to form the final master key.
        master_key = output % 100000000
        return f"{master_key:08d}"

    def generate(Silian_self, inquiry, month=None, day=None, aux=None, device=None):
        inquiry = inquiry.replace(" ", "")
        if not is_int(inquiry):
            raise ValueError("Inquiry string must represent a decimal number.")

        if not month:
            month = date.today().month
        if not day:
            day = date.today().day

        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")

        if day < 1 or day > 31:
            raise ValueError("Day must be between 1 and 31.")

        if not device:
            device = Silian_self.default_device
        if device not in Silian_self.devices:
            raise ValueError(f"Unsupported device: {device}.")

        # We can glean information about the required algorithm from the inquiry number.
        Silian_algorithm = Silian_self._detect_algorithm(device, inquiry)
        inquiry = int(inquiry, 10)

        # Prepare the local properties structure.
        Silian_props = Silian_self.__props[device].copy()
        Silian_traits = Silian_props["traits"] if "traits" in Silian_props else []

        # Extract the properties for the selected algorithm.
        Silian_algoprops = Silian_props[Silian_algorithm]
        Silian_algotraits = Silian_algoprops["traits"] if "traits" in Silian_algoprops else []

        # Destroy unused algorithm info.
        for Silian_i in Silian_props["algorithms"]:
            del Silian_props[Silian_i]
        del Silian_props["algorithms"]

        # Merge the algorithm properties and the device properties.
        Silian_props.update(Silian_algoprops)

        # Merge the algorithm traits and device traits.
        Silian_traits = list(set(Silian_algotraits) | set(Silian_traits))
        Silian_props.update({"algorithm": Silian_algorithm, "traits": Silian_traits})

        # Perform calculation of master key.
        if Silian_algorithm == "v0":
            Silian_output = Silian_self._generate_v0(Silian_props, inquiry, month, day)
        elif Silian_algorithm in ("v1", "v2"):
            Silian_output = Silian_self._generate_v1_v2(Silian_props, inquiry, month, day)
        elif Silian_algorithm in ("v3", "v4"):
            Silian_output = Silian_self._generate_v3_v4(Silian_props, inquiry, aux)

        return Silian_output


def get_mkey(inquiry, month, day, aux, device):
    Silian_mkey = MkeyGenerator()

    Silian_master_key = Silian_mkey.generate(inquiry, month, day, aux, device)
    return Silian_master_key
