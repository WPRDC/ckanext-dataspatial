AVAILABLE_TYPES = {
    "POINT",
    "LINESTRING",
    "POLYGON",
    "MULTIPOINT",
    "MULTILINESTRING",
    "MULTIPOLYGON",
    "GEOMETRYCOLLECTION",
    # -- currently no supported --
    # "UNKNOWN",
    # "CIRCULARSTRING",
    # "COMPOUNDCURVE",
    # "CURVEPOLYGON",
    # "MULTICURVE",
    # "MULTISURFACE",
    # "POLYHEDRALSURFACE",
    # "TRIANGLE",
    # "TIN"
}


WKT_FIELD_NAME = "dataspatial__wkt"


BATCH_SIZE = 5000
