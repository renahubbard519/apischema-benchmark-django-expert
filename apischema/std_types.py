import re
import sys
from datetime import date, datetime, time
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
)
from uuid import UUID

from apischema.conversion import inout_str, input_converter, output_converter
from apischema.schema import schema

# ==================== uuid ====================

inout_str(UUID)
schema(format="uuid")(UUID)

# ==================== datetime ====================

if sys.version_info >= (3, 7):
    input_converter(date.fromisoformat, str, date)
    output_converter(date.isoformat, date, str)
    schema(format="date")(date)

    input_converter(datetime.fromisoformat, str, datetime)
    output_converter(datetime.isoformat, datetime, str)
    schema(format="date-time")(datetime)

    input_converter(time.fromisoformat, str, time)
    input_converter(time.isoformat, time, str)
    schema(format="time")(time)

# ==================== ipaddress ====================

inout_str(IPv4Address)
schema(format="ipv4")(IPv4Address)

inout_str(IPv4Interface)
schema(format="ipv4")(IPv4Interface)

inout_str(IPv4Network)
schema(format="ipv4")(IPv4Network)

inout_str(IPv6Address)
schema(format="ipv6")(IPv6Address)

inout_str(IPv6Interface)
schema(format="ipv6")(IPv6Interface)

inout_str(IPv6Network)
schema(format="ipv6")(IPv6Network)

# ==================== pattern ====================
Pattern = type(re.compile(r""))
input_converter(re.compile, str, Pattern)
output_converter(lambda p: p.pattern, Pattern, str)
