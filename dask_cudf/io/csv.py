import os
from glob import glob

import cudf
from dask.base import tokenize
from dask.compatibility import apply
import dask.dataframe as dd
from dask.utils import parse_bytes


def read_csv(path, chunksize="128 MiB", **kwargs):
    if isinstance(chunksize, str):
        chunksize = parse_bytes(chunksize)
    filenames = sorted(glob(str(path)))  # TODO: lots of complexity
    name = "read-csv-" + tokenize(
        path, tokenize, **kwargs
    )  # TODO: get last modified time

    meta = cudf.read_csv(filenames[0], **kwargs)

    dsk = {}
    i = 0
    for fn in filenames:
        size = os.path.getsize(fn)
        for start in range(0, size, chunksize):
            kwargs2 = kwargs.copy()
            kwargs2["byte_range"] = (
                start,
                chunksize,
            )  # specify which chunk of the file we care about
            if start != 0:
                kwargs2["names"] = meta.columns  # no header in the middle of the file
                kwargs2["header"] = None
            dsk[(name, i)] = (apply, cudf.read_csv, [fn], kwargs2)
            i += 1

    divisions = [None] * (len(dsk) + 1)
    return dd.core.new_dd_object(dsk, name, meta, divisions)
