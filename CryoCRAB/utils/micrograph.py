import numpy as np
from numba import jit
from . import fft
from . import fft_sizes
# from .background import do_lowpass_filter_2D_herm_gaussian_core

# ----------------------------------------------------- PADDING AND TRIMMING

def get_lowest_pow_2(
    shape: tuple
) -> int:
    if type(shape) in [list, tuple, np.array]:
        shape = list(shape)
    else:
        shape = [shape]
    return 2**int(  np.ceil(np.log2(float(max(shape))))  )

def pad_mic(
    arr: np.ndarray, 
    N: int = None, 
    val: float = 0, 
    dtype = np.float32, 
    out: np.ndarray = None
):
    arr = arr.reshape((-1,)+arr.shape[-2:])
    nz, ny, nx = arr.shape
    if dtype is None: dtype = arr.dtype
    if N is None: N = get_lowest_pow_2(arr.shape[-2:])
    if out is None:
        res = np.zeros((nz,N,N), dtype)
    else:
        res = out.reshape(nz, N, N)
    nya = ny // 2
    nyb = ny-nya
    nxa = nx // 2
    nxb = nx-nxa
    ya, yb = (N//2)-nya, (N//2)+nyb
    xa, xb = (N//2)-nxa, (N//2)+nxb
    for z in range(nz):
        res[z, ya:yb, xa:xb] = arr[z]
    res[:,:,:xa] = val
    res[:,:,xb:] = val
    res[:,:ya,:] = val
    res[:,yb:,:] = val
    if nz == 1:
        return res.reshape(res.shape[-2:])
    else:
        return res
    
def pad_mic_with_mean(
    arr: np.ndarray, 
    N: int = None, 
    dtype = np.float32
):
    mean = arr.mean()
    return pad_mic(arr, N, mean, dtype)

def pad_mic_with_zero(
    arr: np.ndarray, 
    N = None,
    dtype = np.float32
):
    return pad_mic(arr, N, 0, dtype)

def trim_mic(
    arr: np.ndarray, 
    shape: tuple
):
    Ny, Nx = arr.shape
    ny, nx = shape
    nya = (ny//2)
    nyb = ny-nya
    nxa = (nx//2)
    nxb = nx-nxa
    ya, yb = (Ny//2)-nya, (Ny//2)+nyb
    xa, xb = (Nx//2)-nxa, (Nx//2)+nxb
    return arr[ya:yb, xa:xb]

@jit
def contrast_normalization(
    arr_bin: np.ndarray, 
    tile_size: int = 128, 
    extend: float = 1.5
):
    '''
    Computes the minimum and maximum contrast values to use when
    displaying a micrograph by calculating the mean of the medians 
    of the mic split up into tile_size * tile_size patches.

    :param arr_bin: the micrograph represented as a numpy array
    :type arr_bin: list
    :param tile_size: the size of the patch to split the mic by 
        (larger is faster)
    :type tile_size: int
    '''
    ny,nx = arr_bin.shape
    # set up start and end indexes to make looping code readable
    tile_start_x = np.arange(0, nx, tile_size)
    tile_end_x = tile_start_x + tile_size
    tile_start_y = np.arange(0, ny, tile_size)
    tile_end_y = tile_start_y + tile_size
    num_tile_x = len(tile_start_x)
    num_tile_y = len(tile_start_y)
    
    # initialize array that will hold means and std devs of all patches
    tile_all_data = np.empty((num_tile_y*num_tile_x, 2), dtype=np.float32)

    index = 0
    for y in range(num_tile_y):
        for x in range(num_tile_x):
            # cut out a patch of the mic
            arr_tile = arr_bin[tile_start_y[y]:tile_end_y[y], tile_start_x[x]:tile_end_x[x]]
            # store 2nd and 98th percentile values
            tile_all_data[index:,0] = np.percentile(arr_tile, 98)
            tile_all_data[index:,1] = np.percentile(arr_tile, 2)
            index += 1

    # calc median of non-NaN percentile values
    all_tiles_98_median = np.nanmedian(tile_all_data[:,0])
    all_tiles_2_median = np.nanmedian(tile_all_data[:,1])
    vmid = 0.5*(all_tiles_2_median+all_tiles_98_median)
    vrange = abs(all_tiles_2_median-all_tiles_98_median)
    # extend vmin and vmax enough to not include outliers
    vmin = vmid - extend*0.5*vrange
    vmax = vmid + extend*0.5*vrange

    return vmin, vmax

def contrast_normalization_naive(
    arr_bin: np.ndarray, 
    extend: float = 1.5
):
    p2, p98 = np.percentile(arr_bin.reshape(-1), (2, 98))
    vmid = (p98 + p2) * 0.5
    vrange = abs(p98 - p2)
    vmin = vmid - extend*0.5*vrange
    vmax = vmid + extend*0.5*vrange
    
    return vmin, vmax 

def contrast_normalization_show(
    arr_bin: np.ndarray, 
    extend: float = 1.5,
):
    vmin, vmax = contrast_normalization(arr_bin, extend=extend)
    arr_bin = np.clip(arr_bin, vmin, vmax)
    return arr_bin

def show_array(
    arr: np.ndarray,
):
    bin_factor = max(1, arr.shape[0] / 1024)
    arr_bin = bin_mic(
        arr=arr,
        bin_factor=bin_factor
    )
    arr_bin = contrast_normalization_show(
        arr_bin=arr_bin
    )
    return arr_bin

def do_lowpass_filter_2D_herm_gaussian_core(
    farr: np.ndarray, 
    frame_shape: tuple, # extra input reason: since this is the shape of micrograph not its FT
    one_over_sigma_fspace2: float,
):
    # one_over_sigma2 is of gaussian in fourier space 
    # one_over_sigma_fspace**2 = pi^2 * sigma_real^2 in terms of the sigma in real space
    ny, nx = farr.shape
    freqs = fft.get_rfft_center_freqs(frame_shape, psize_A=1.0)
    freqs_y = freqs[..., 0] * frame_shape[0] # unit: 1
    freqs_x = freqs[..., 1] * frame_shape[1] # unit: 1
    freqs_norm2 = freqs_y**2 + freqs_x**2
    filt = np.exp(- freqs_norm2 * 0.5 * one_over_sigma_fspace2)
    farr *= filt
    # zero nyquist at the end
    farr[0, :] = 0.0
    farr[-1, :] = 0.0
    farr[:, -1] = 0.0
    return farr

def estimate_background(
    arr: np.ndarray, 
    fwhm: float, 
    out_N: int = None
):
    """ 
    arr should be ny x nx (not padded, but binned because it will get zeropadded to 2N) 
    fwhm should be in fraction of N, like 0.1
    """
    sigma_real2 = (2*fwhm/2.3548)**2
    one_over_sigma_fspace2 = np.pi**2 * sigma_real2
    # assume that arr is already binned down to a reasonable size
    # assert ny == nx
    # assert np.log2(ny).is_integer()
    N = get_lowest_pow_2(arr.shape)
    N_zp = 2 * N 
    if out_N is not None: out_shape = (out_N, out_N)
    else: out_shape = arr.shape
    
    do_zeropad_rfft_filt = lambda x: do_lowpass_filter_2D_herm_gaussian_core(
        farr=fft.rfft2_center( 
            pad_mic_with_zero( arr=x, N=N_zp ) 
        ),
        frame_shape=(N_zp, N_zp),
        one_over_sigma_fspace2=one_over_sigma_fspace2,
    )    
    do_irfft_crop = lambda x: trim_mic(
        arr=fft.irfft2_center( x ), 
        shape=out_shape
    )
    
    farr_zp = do_zeropad_rfft_filt(arr)
    # now farr_zp is the lowpass version of the zeropadded array. 
    # only now the edges need to be taken care of.
    fones_zp = do_zeropad_rfft_filt(
        np.ones(arr.shape, np.float32)
    )
    
    arr_zp_lp_cp = do_irfft_crop(farr_zp)
    ones_zp_lp_cp = do_irfft_crop(fones_zp)

    return arr_zp_lp_cp / ones_zp_lp_cp

def bin_mic(
    arr: np.ndarray, 
    bin_factor: float = None,
    frame_shape_out: tuple = None,
):
    assert bin_factor is not None or frame_shape_out is not None, "Please provide bin_factor or frame_shaoe_out at least!"
    
    frame_shape_in = arr.shape
    
    if bin_factor is not None:
        # since we do not consider soft mask on the boundary of freqs, we only can handle downsample here
        assert bin_factor >= 1, "Only support bin_factor > 1 here, if you want to upsample, please use upsample_mic instead"
        frame_shape_out = [int(x / bin_factor) for x in frame_shape_in]
    
    N_in = fft_sizes.get_lowest_fast_size(frame_shape_in)
    N_out = fft_sizes.get_lowest_fast_size(N_in / bin_factor)
    
    do_meanpad_rfft_crop = lambda x: fft.ZT(
        x=fft.rfft2_center(
          pad_mic_with_mean( arr=x,  N=N_in, )  
        ),
        M=N_out,
    )
    do_irfft_trim = lambda x: trim_mic(
        arr=fft.irfft2_center(x),
        shape=frame_shape_out
    )
    
    arr_ft = do_meanpad_rfft_crop(arr)
    arr = do_irfft_trim(arr_ft)
    
    return arr

def upsample_mic(
    arr: np.array,
    upsample_factor: float = None,
    frame_shape_out: tuple = None,
):
    assert upsample_factor is not None or frame_shape_out is not None, "Please provide upsample_factor or frame_shaoe_out at least!"
    
    frame_shape_in = arr.shape
    
    if upsample_factor is not None:
        # since we do not consider soft mask on the boundary of freqs, we only can handle downsample here
        assert upsample_factor >= 1, "Only support upsample_factor > 1 here, if you want to downsample, please use bin_mic instead"
        frame_shape_out = [int(x * upsample_factor) for x in frame_shape_in]
        
    N_in = fft_sizes.get_lowest_fast_size(frame_shape_in)
    N_out = fft_sizes.get_lowest_fast_size(N_in * upsample_factor)
    
    do_meanpad_rfft_zeropad_softmask = lambda x: fft.ZT( # zeropad
        x=fft.rfft2_center(  # rfft
            pad_mic_with_mean( arr=x,  N=N_in, ) # meanpad
        ),
        M=N_out,
    ) * fft.get_upsample_softmask( # softmask
        frame_shape_in=(N_in, N_in),
        frame_shape_out=(N_out, N_out),
    )
    do_irfft_trim = lambda x: trim_mic(
        arr=fft.irfft2_center(x),
        shape=frame_shape_out
    )
    
    arr_ft = do_meanpad_rfft_zeropad_softmask(arr)
    arr = do_irfft_trim(arr_ft)
    
    return arr
        

def estimate_subtract_background(
    mic_gc: np.ndarray, 
    psize: float,
):
    """
    Estimate the background and subtract it from a gain corrected micrograph

    :param mic_gc: the gain corrected micrograph
    :type mic_gc: 2D array
    :param psize: the pixel size of the micrograph
    :type psize: float
    """
    frame_shape = mic_gc.shape
    N = get_lowest_pow_2(frame_shape)
    bg_binfactor = int(np.ceil(N / 1024.0))
    mic_bin = bin_mic(mic_gc, bg_binfactor)
    # "full width half max" - a parameterization of gaussians used for smoothing
    fwhm = (200 / psize) / N
    # this is a padded 1024x1024 bg size
    bg_bin = estimate_background(mic_bin, fwhm, out_N=1024)
    bg_full = upsample_mic(
        arr=bg_bin,
        upsample_factor=bg_binfactor
    )
    # now final bg_full of summed movie
    bg_full = trim_mic(bg_full, frame_shape).copy()
    mic_bg_sub = mic_gc - bg_full
    return mic_bg_sub

def background_addition(
    mic_gc_noBG: np.ndarray, 
    bg_bin: np.ndarray,
):
    frame_shape = mic_gc_noBG.shape
    N = get_lowest_pow_2(frame_shape)
    bg_binfactor = int(np.ceil(N / 1024.0))
    bg_full = upsample_mic(
        arr=bg_bin,
        upsample_factor=bg_binfactor
    )
    # now final bg_full of summed movie
    bg_full = trim_mic(bg_full, frame_shape).copy()
    mic_bg_add = mic_gc_noBG + bg_full
    return mic_bg_add
