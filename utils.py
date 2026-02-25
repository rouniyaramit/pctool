import numpy as np

def iec_curve(I, Ip, TMS, curve):
    if I <= Ip:
        return np.nan
    curves = {
        "Standard Inverse": (0.14, 0.02),
        "Very Inverse": (13.5, 1),
        "Extremely Inverse": (80, 2),
    }
    k, alpha = curves[curve]
    M = I / Ip
    return TMS * (k / ((M ** alpha) - 1))

def transformer_calculations(MVA, LV, Z):
    FLC_LV = (MVA * 1000) / (np.sqrt(3) * LV)
    Isc_LV = FLC_LV / (Z / 100)
    return FLC_LV, Isc_LV
