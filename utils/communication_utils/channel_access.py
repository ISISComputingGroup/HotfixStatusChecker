"""Module containing utility methods for interacting with a PV."""

import binascii
import json
import zlib
from builtins import (
    object,
)
from enum import (
    Enum,
)
from typing import Dict, Any

from genie_python.channel_access_exceptions import (
    ReadAccessException,
    UnableToConnectToPVException,
)
from genie_python.genie_cachannel_wrapper import (
    CaChannelWrapper,
)

# Some instruments may not be available. If this is the case, we don't want to wait too long for the response which
# will never come (which would slow down the tests)
CHANNEL_ACCESS_TIMEOUT = 5


class ChannelAccessUtils(object):
    """Class containing utility methods for interacting with a PV."""

    def __init__(
        self,
        pv_prefix="",
    ) -> None:
        self.pv_prefix = pv_prefix

    def get_value(
        self,
        pv,
    ) ->  str | dict | None:
        """Gets the value of the PV. Returns None if PV is unavailable.
        :return: The PV value as a string, or None if there was an error.
        """
        try:
            return CaChannelWrapper.get_pv_value(
                "{}{}".format(
                    self.pv_prefix,
                    pv,
                ),
                timeout=CHANNEL_ACCESS_TIMEOUT,
            )
        except (
            UnableToConnectToPVException,
            ReadAccessException,
        ):
            return None

    @staticmethod
    def _dehex_and_decompress(
        data,
    ) -> bytes:
        """Converts the raw data from a PV to a decompressed string.
        :param data: The raw data from the PV. It is a string of numbers representing the bytes of the raw data of the
        PV.
        :return: The data of the PV in the form of a decompressed and decoded string.
        """
        return zlib.decompress(binascii.unhexlify(data))

    def get_inst_list(
        self,
    ) -> Dict | Any:
        """Gets a list with all instruments running on IBEX from CS:INSTLIST.
        :return: a list of strings of instrument names.
        """
        pv_value = self.get_value("CS:INSTLIST")
        return (
            {} if pv_value is None else json.loads(self._dehex_and_decompress(pv_value))
        )


class PvInterestingLevel(Enum):
    """Enumerated type representing the possible interesting levels a PV can have."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    FACILITY = "FACILITY"
