# oc_ef_engine.py

import math


def calculate_oc_ef(
    mva,
    hv_v,
    lv_v,
    z_pct,
    cti_ms,
    q4_ct,
    q5_ct,
    feeder_data  # list of {"load": float, "ct": float}
):

    if cti_ms < 120:
        return {"error": "CTI must be greater than or equal to 120ms."}

    cti_s = cti_ms / 1000

    # ---------------- Transformer Calculations ----------------
    flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_v), 2)
    flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_v), 2)
    isc_lv = round(flc_lv / (z_pct / 100), 2)

    if_lv = round(isc_lv * 0.9, 2)
    if_hv = round(if_lv / (hv_v / lv_v), 2)

    total_load = 0.0
    max_t_oc = 0.0
    max_t_ef = 0.0

    feeder_oc_text = ""
    feeder_ef_text = ""
    ct_alerts = []

    # ---------------- Feeder Calculations ----------------
    for i, row in enumerate(feeder_data):

        l = float(row["load"])
        ct = float(row["ct"])

        total_load += l

        if ct < l:
            ct_alerts.append(
                f"ALERT: Feeder Q{i+1} CT ({ct}A) is less than Load ({l}A)"
            )

        # -------- Overcurrent --------
        p_oc = round(1.1 * l, 2)
        r1 = round(p_oc / ct, 2)

        t_oc = round(
            0.025 * (
                0.14 / (math.pow(max(1.05, if_lv / p_oc), 0.02) - 1)
            ),
            3
        )

        max_t_oc = max(max_t_oc, t_oc)

        p2 = round(3 * l, 2)
        r2 = round(p2 / ct, 2)

        feeder_oc_text += (
            f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n"
            f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), "
            f"TMS=0.025, Time={t_oc}s\n"
            f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"
        )

        # -------- Earth Fault --------
        p_ef = round(0.15 * l, 2)
        r_ef1 = round(p_ef / ct, 2)

        t_ef = round(
            0.025 * (
                0.14 / (math.pow(max(1.05, if_lv / p_ef), 0.02) - 1)
            ),
            3
        )

        max_t_ef = max(max_t_ef, t_ef)

        p_ef2 = round(1.0 * l, 2)
        r_ef2 = round(p_ef2 / ct, 2)

        feeder_ef_text += (
            f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n"
            f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), "
            f"TMS=0.025, Time={t_ef}s\n"
            f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"
        )

    hv_load = total_load / (hv_v / lv_v)

    # ---------------- Incomer CT Validation ----------------
    if q4_ct < total_load:
        ct_alerts.append(
            f"ALERT: Q4 Incomer CT ({q4_ct}A) "
            f"is less than Total Load ({round(total_load,2)}A)"
        )

    if q5_ct < hv_load:
        ct_alerts.append(
            f"ALERT: Q5 HV CT ({q5_ct}A) "
            f"is less than HV Load ({round(hv_load,2)}A)"
        )

    # ---------------- Incomer Coordination ----------------
    coord_data = [
        ("INCOMER Q4 (LV)", q4_ct, if_lv, 1,
         round(0.9 * isc_lv, 2), cti_ms,
         max_t_oc, max_t_ef),

        ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_v / lv_v,
         round(if_hv, 2), cti_ms * 2,
         max_t_oc + cti_s, max_t_ef + cti_s)
    ]

    incomer_oc_text = ""
    incomer_ef_text = ""

    for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:

        l_cur = total_load / scale

        t_req_oc = round(t_prev_oc + cti_s, 3)
        t_req_ef = round(t_prev_ef + cti_s, 3)

        # -------- OC --------
        p_oc = round(1.1 * l_cur, 2)
        r1 = round(p_oc / ct_v, 2)

        tms_oc = round(
            t_req_oc / (
                0.14 / (
                    math.pow(max(1.05, fault / p_oc), 0.02) - 1
                )
            ),
            3
        )

        p2 = round(3 * l_cur, 2)
        r2 = round(p2 / ct_v, 2)
        r3 = round(s3 / ct_v, 2)

        incomer_oc_text += (
            f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n"
            f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), "
            f"TMS={tms_oc}, Time={t_req_oc}s\n"
            f" - S2 (DT):   Pickup={p2}A ({r2}*In), "
            f"Time={dt_ms/1000}s\n"
            f" - S3 (DT):   Pickup={s3}A ({r3}*In), "
            f"Time=0.0s\n\n"
        )

        # -------- EF --------
        p_ef = round(0.15 * l_cur, 2)
        r_ef1 = round(p_ef / ct_v, 2)

        tms_ef = round(
            t_req_ef / (
                0.14 / (
                    math.pow(max(1.05, fault / p_ef), 0.02) - 1
                )
            ),
            3
        )

        p_ef2 = round(1.0 * l_cur, 2)
        r_ef2 = round(p_ef2 / ct_v, 2)
        r_ef3 = round(s3 / ct_v, 2)

        incomer_ef_text += (
            f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n"
            f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), "
            f"TMS={tms_ef}, Time={t_req_ef}s\n"
            f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), "
            f"Time={dt_ms/1000}s\n"
            f" - S3 (DT):   Pickup={s3}A ({r_ef3}*In), "
            f"Time=0.0s\n\n"
        )

    # ---------------- Final Report Header ----------------
    header = (
        f"FLC LV: {flc_lv}A | "
        f"FLC HV: {flc_hv}A | "
        f"Short Circuit: {isc_lv}A\n"
        + "=" * 60 + "\n"
    )

    overload_alert = (
        f"CRITICAL ALERT: TRANSFORMER OVERLOAD "
        f"({total_load}A > {flc_lv}A)"
        if total_load > flc_lv else None
    )

    return {
        "header": header,
        "overload": overload_alert,
        "ct_alerts": ct_alerts,
        "oc_report": feeder_oc_text + incomer_oc_text,
        "ef_report": feeder_ef_text + incomer_ef_text
    }
