import numpy as np
from . import fft

# ================= 2D REAL CTF 
def defocus_polar_to_cartesian(df1_A, df2_A, df_angle_rad):
    DF = (df1_A + df2_A) / 2
    df = (df1_A - df2_A) / 2
    dfxx = np.cos(2*df_angle_rad)*df
    dfxy = np.sin(2*df_angle_rad)*df
    return np.array(DF), np.array(dfxx), np.array(dfxy)
def get_chi_consts ( akv, csmm, wgh, phase_shift):
    av = akv * 1e3
    e = 12.2643247 / np.sqrt(av + av**2 * 0.978466e-6)
    CTF2 = np.pi * e 
    CTF4 = - np.pi * e**3 * (csmm*1e7) / 2.0
    chi_offset = phase_shift - np.arccos(wgh)
    return CTF2, CTF4, chi_offset
def compute_ctf_chi_2D ( freqs, akv, csmm, wgh, DF,  dfxx, dfxy, phase_shift):
    CTF2, CTF4, chi_offset = get_chi_consts ( akv, csmm, wgh, phase_shift)
    fx = freqs[...,0]
    fy = freqs[...,1]
    f2 = (fx*fx + fy*fy)
    chi = CTF2*((DF+dfxx)*fx*fx + 2*(dfxy)*fx*fy + (DF-dfxx)*fy*fy) + CTF4*f2*f2 + chi_offset
    return chi

def compute_ctf(
    defocus_u: float,
    defocus_v: float,
    defocus_angle_rad: float,
    accel_kv: float,
    cs_mm: float,
    amp_contrast: float,
    phase_shift_rad: float,
    freqs: np.ndarray, # unit: 1/Angstrom, not extra computation for single dataset, which speeds up the CTF correction
    N_out: int,  
    psize_out: float,
    D0: float=5.0, # cutoff freq, unit: 1/A
    n: int=4, # butterworth filter order
    min_chi: float=-1.50, # minimum chi for stable ctf correction
):
    """
    Generate CTF filter: Invert CTF up to first peak, phase-flip beyond first peak
    """
    DFs, dfxxs, dfxys = defocus_polar_to_cartesian(
        df1_A=defocus_u, 
        df2_A=defocus_v, 
        df_angle_rad=defocus_angle_rad
    )
    chi = compute_ctf_chi_2D(
        freqs=freqs, 
        akv=accel_kv, 
        csmm=cs_mm, 
        wgh=amp_contrast, 
        DF=DFs, 
        dfxx=dfxxs, 
        dfxy=dfxys, 
        phase_shift=phase_shift_rad
    )
    if min_chi is not None:
        chi = np.maximum(chi, min_chi) # -1.50 corresponding to CTF=-0.07 or 1/CTF = ~14.3
    ctf = np.cos(chi)
    
    freqs_pix = freqs*N_out*psize_out
    hpfilt = 1. - 1. / (1. + (np.linalg.norm(freqs_pix, axis=-1) / D0) ** (2*n))
    ctffilt = hpfilt
    ctffilt[chi < 0] *= 1.0 / ctf[chi < 0]
    ctffilt[chi >= 0] *= np.sign(ctf[chi >= 0])
    
    return ctffilt