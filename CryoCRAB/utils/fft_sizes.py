from typing import List

import numpy as np

def fast_cufft_fft2_sizes_single() -> List[int]:
    """
    For single 2D arrays (e.g., micrographs)
    Tested on K40 with rfft2
    """
    return [512,  576,   640,   648,   672,   720,   768,   784,   810,  1024,
            1152,  1280,  1296,  1344,  1440,  1568,  1728,  1792,  2048,
            2160,  2592,  2744,  3456,  4096,  4116,  4480,  4608,  5120,
            5184,  5488,  5832,  6144,  6272,  6400, 8192,  8640,  9216,  9408,
            9720, 10240, 10368, 11664, 12544, 12800, 13122, 13608, 14336,
            16384]
    
def fast_cufft_fft2_sizes_batch() -> List[int]:
    """
    For multiple 2D arrays (e.g.,  particles)
    Tested on K40 with rfft2
    """
    return [32,   36,   40,   42,   48,   56,   60,   64,   70,   72,   80,
            84,   90,   96,  100,  108,  112,  120,  128,  144,  160,  180,
            192,  200,  216,  224,  240,  256,  270,  288,  300,  320,  324,
            336,  384,  400,  432,  448,  450,  512,
            576,  640,  648,  672,  720,  768,  784,  810,  864,  882, 1024,
            1152, 1280, 1296, 1344, 1440, 1568, 1620, 1728, 1792, 2000, 2048,
            2160, 2592, 2744, 3456, 4096]

def fast_cufft_fft3_sizes() -> List[int]:
    """
    For 3D arrays (e.g., volumes)
    Tested on K40 with rfft3 inplace
    Maximum Sizes:
        - 1120 box size with 11GB (11721506816 bytes GTX1080Ti)
        - 1152 box size with 12GB (12799574016 bytes K40C)
        - 1280 box size with 16GB (16877158400 bytes RTX5000)
        - 1600 box size with 32GB (34055847936 bytes GV100)
    """
    return [42,   48,   50,   56,   60,   64,   72,   80,   84,   90,   96,
            100,  108,  112,  120,  128,  144,  160,  168,  180,  192,  200,
            216,  224,  240,  256,  270,  288,  300,  320,  324,  336,  360,
            378,  384,  392,  400,  432,  450,  512,  540,  576,  600,  640,
            648,  672,  700,  720,  756,  768,  784,  810,  882,  900, 1024,
            1080, 1120, 1152]

def get_lowest_fast_size(
        frame_shape: int,
        d: int = 2,
        batch: bool = False) -> int:
    """
    Using the optimized list of sizes tested to perform well in FFTs, find
    the next lowest size to use for an array.

    :param frame_shape: the size of the array to optimize
    :type frame_shape: int
    :param d: the dimension of the array (e.g., 2 or 3)
    :type d: int
    :param batch: if True, implies the search is for a 2D stack
    of particles rather than a micrograph
    :type batch: bool
    """
    assert d in [2, 3], "Dimension of array must be either 2 or 3"
    q = np.max(frame_shape)

    if d == 2:
        fast_sizes = fast_cufft_fft2_sizes_batch(
        ) if batch else fast_cufft_fft2_sizes_single()
    elif d == 3:
        fast_sizes = fast_cufft_fft3_sizes()

    hits = np.where(np.array(fast_sizes) >= q)[0]
    if len(hits) > 0:
        return fast_sizes[hits[0]]
    else:  # default to lowest pow 2
        return 2**int(np.ceil(np.log2(float(q))))

def get_nearest_fast_size(
        frame_shape: int,
        d: int = 2,
        batch: bool = False) -> int:
    """
    Using the optimized list of sizes tested to perform well in FFTs, find
    the nearest size that is fast.

    :param frame_shape: the size of the array to optimize
    :type frame_shape: int
    :param d: the dimension of the array (e.g., 2 or 3)
    :type d: int
    :param batch: if True, implies the search is for a 2D stack
    of particles rather than a micrograph
    :type batch: bool
    """
    assert d in [2, 3], "Dimension of array must be either 2 or 3"
    q = np.max(frame_shape)

    if d == 2:
        fast_sizes = fast_cufft_fft2_sizes_batch(
        ) if batch else fast_cufft_fft2_sizes_single()
    elif d == 3:
        fast_sizes = fast_cufft_fft3_sizes()

    diffs2 = (np.array(fast_sizes) - q)**2
    hit = np.argmin(diffs2)
    return fast_sizes[hit]

def get_shapes_for_desired_psize(psize_in, frame_shape_in, psize_des):
    # figure out downsampling factor
    N_in = get_lowest_fast_size(frame_shape_in)
    N_out = get_nearest_fast_size(psize_in * N_in / psize_des)
    psize_out = psize_in * N_in / N_out
    downfactor = N_out / N_in
    frame_shape_out = np.round(np.array(frame_shape_in)*downfactor).astype(int)
    return N_in, N_out, psize_out, downfactor, frame_shape_out
