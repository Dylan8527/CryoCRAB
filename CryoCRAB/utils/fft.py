import numpy as np

def rfft2_center(img):
    return np.fft.fftshift(np.fft.rfft2(img), axes=(0))
    
def irfft2_center(img_ht):
    return np.fft.irfft2(np.fft.ifftshift(img_ht, axes=(0))).real
    
def get_rfft_center_freqs(frame_shape_real, psize_A):
    # freq_y: -0.5 ~ 0.5, freq_x: 0 ~ 0.5
    freqs_y = np.fft.fftshift(np.fft.fftfreq(frame_shape_real[0], d=psize_A))
    freqs_x = np.fft.rfftfreq(frame_shape_real[1], d=psize_A)
    freqs = np.stack(np.meshgrid(freqs_x, freqs_y), axis=-1)
    return freqs

def ZT(x, M: int, stack=False, res=None):
    ' Zeropad or truncate from N to M, either rspace or fspace input. If stack, first dim is the stack dimension. '
    if not stack:
        x = x.reshape((1,) + x.shape)
    ndim = len(x.shape) - 1
    assert ndim in [1,2,3]
    S = x.shape[0]
    sigshape = x.shape[1:]
    assert M % 2 == 0
    N = (sigshape[-1]-1)*2 if np.iscomplexobj(x) else sigshape[-1]
    assert all([d==N for d in sigshape[:-1]])
    resshape = [S] + [M]*(ndim-1) + [(M//2)+1 if np.iscomplexobj(x) else M]
    if res is None:
        res = np.zeros(resshape, x.dtype)
    else:
        assert res.shape == resshape
        assert res.dtype == x.dtype
        res[:] = 0.0
    Q = min(M, N) # amount to copy
    BM = ((M-Q)//2); EM = BM+Q
    BN = ((N-Q)//2); EN = BN+Q
    if np.iscomplexobj(x):
        # f-space
        if ndim == 1:
            res[:, :(Q//2)] = x[:, :(Q//2)]
        if ndim == 2:
            res[:, BM+1:EM, :(Q//2)] = x[:, BN+1:EN, :(Q//2)]
        if ndim == 3:
            res[:, BM+1:EM, BM+1:EM, :(Q//2)] = x[:, BN+1:EN, BN+1:EN, :(Q//2)]
    else:
        # r-space
        if ndim == 1:
            res[:, BM:EM] = x[:, BN:EN]
        if ndim == 2:
            res[:, BM:EM, BM:EM] = x[:, BN:EN, BN:EN]
        if ndim == 3:
            res[:, BM:EM, BM:EM, BM:EM] = x[:, BN:EN, BN:EN, BN:EN]
    if not stack:
        res = res[0]
    return res

def smoothstep(
    p1: float, 
    p2: float, 
    x: np.ndarray
):
    """ 5th-order smooth step function.
    p1: elements less than p1 = 1 
    p2: elements greater than p2 = 0
    x: array of numbers to smoothstep
    """
    if x.shape[-1] != 2 and len(x.shape) == 3:
        x = x.norm(axis=-1)
    s = np.piecewise(x,
                    [x<p1, np.logical_and(x>=p1,x<=p2), x>p2],
                    [0, lambda x:(x-p1)/(p2-p1), 1])
    return (s**3)*(s*(s*6 - 15)+10)


def get_upsample_softmask(
    frame_shape_in: tuple,
    frame_shape_out: tuple,
    psize_in: float=None,
    psize_out: float=None,
    cutoff_width: float=2,
):
    upsample_factor = frame_shape_out[0] / frame_shape_in[0]
    assert upsample_factor > 1, "If you want to upsample, please make sure frame_shape_out > frame_shape_in!"
    
    if psize_in is not None:
        psize_out = psize_in / upsample_factor
    elif psize_out is not None:
        psize_in = psize_out * upsample_factor
    else:
        psize_out = 1.0 
        psize_in = psize_out * upsample_factor
        
    # fact: psize_out > psize_in
        
    freqs_out = get_rfft_center_freqs(frame_shape_out, psize_out)
    softmask  = 1. - smoothstep(
        1./(psize_in + cutoff_width) / 2.0,
        1./psize_in,
        np.linalg.norm(freqs_out, axis=-1)
    )
    
    return softmask