# tcc_engine.py

import numpy as np

CTI_Q1_Q4 = 0.150
CTI_Q1_Q5 = 0.300
CTI_Q4_Q5 = 0.150


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


def transformer_calculations(MVA, LV, HV, Z):
    FLC_LV = (MVA * 1000) / (np.sqrt(3) * LV)
    Isc_LV = FLC_LV / (Z / 100)
    HV_factor = HV / LV
    return FLC_LV, Isc_LV, HV_factor


def calculate_tcc(
        MVA, LV, HV, Z,
        fault_current,
        relay_settings
):
    """
    relay_settings = list of dicts:
    {
        "pickup": float,
        "tms": float,
        "curve": str,
        "idmt": bool,
        "dt1": bool,
        "dt1_pickup": float,
        "dt1_time": float,
        "dt2": bool,
        "dt2_pickup": float,
        "dt2_time": float
    }
    """

    currents = np.logspace(1, 5, 800)

    FLC_LV, Isc_LV, HV_factor = transformer_calculations(MVA, LV, HV, Z)

    if Isc_LV and fault_current and fault_current > Isc_LV:
        fault_current = Isc_LV

    trip_times = {}
    merged_curves = []

    for i, relay in enumerate(relay_settings):

        Ip = relay["pickup"]
        TMS = relay["tms"]
        curve = relay["curve"]

        current_scaling = HV_factor if i == 4 else 1
        merged_curve = []

        for I in currents:
            I_scaled = I / current_scaling
            times = []

            if relay["idmt"]:
                t_idmt = iec_curve(I_scaled, Ip, TMS, curve)
                if not np.isnan(t_idmt):
                    times.append(t_idmt)

            if relay["dt1"]:
                if I_scaled >= relay["dt1_pickup"]:
                    times.append(relay["dt1_time"])

            if i >= 3 and relay["dt2"]:
                if I_scaled >= relay["dt2_pickup"]:
                    times.append(relay["dt2_time"])

            merged_curve.append(min(times) if times else np.nan)

        merged_curve = np.array(merged_curve)
        merged_curves.append(merged_curve)

        # Fault intersection logic (exact from GUI_Final5)
        I_fault_scaled = fault_current / current_scaling
        intersection_times = []

        if relay["idmt"]:
            t_f = iec_curve(I_fault_scaled, Ip, TMS, curve)
            if not np.isnan(t_f):
                intersection_times.append(t_f)

        if relay["dt1"]:
            if I_fault_scaled >= relay["dt1_pickup"]:
                intersection_times.append(relay["dt1_time"])

        if i >= 3 and relay["dt2"]:
            if I_fault_scaled >= relay["dt2_pickup"]:
                intersection_times.append(relay["dt2_time"])

        if intersection_times:
            t_res = min(intersection_times)
            trip_times[f"Q{i+1}"] = round(t_res, 3)

    # Coordination margin checks (exact logic)
    coordination_results = []

    checks = [
        ("Q1", "Q4", CTI_Q1_Q4),
        ("Q2", "Q4", CTI_Q1_Q4),
        ("Q3", "Q4", CTI_Q1_Q4),
        ("Q1", "Q5", CTI_Q1_Q5),
        ("Q2", "Q5", CTI_Q1_Q5),
        ("Q3", "Q5", CTI_Q1_Q5),
        ("Q4", "Q5", CTI_Q4_Q5),
    ]

    for d, u, c in checks:
        if d in trip_times and u in trip_times:
            margin = trip_times[u] - trip_times[d]
            coordination_results.append({
                "downstream": d,
                "upstream": u,
                "margin": round(margin, 3),
                "required": c,
                "status": "OK" if margin >= c else "NOT OK"
            })

    return {
        "currents": currents,
        "curves": merged_curves,
        "trip_times": trip_times,
        "coordination": coordination_results,
        "FLC_LV": FLC_LV,
        "Isc_LV": Isc_LV,
        "fault_current": fault_current
    }
