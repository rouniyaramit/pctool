import math


def validate_cti_ms(cti_ms: float) -> tuple[bool, str | None]:
    if cti_ms < 120:
        return False, "CTI must be greater than or equal to 120ms."
    return True, None


def calculate_grid(
    mva: float,
    hv_kv: float,
    lv_kv: float,
    z_pct: float,
    cti_ms: float,
    q4_ct: float,
    q5_ct: float,
    feeders: list[dict],  # [{"load": float, "ct": float}, ...]
):
    cti_s = cti_ms / 1000.0

    flc_lv = round((mva * 1000.0) / (math.sqrt(3.0) * lv_kv), 2)
    flc_hv = round((mva * 1000.0) / (math.sqrt(3.0) * hv_kv), 2)
    isc_lv = round(flc_lv / (z_pct / 100.0), 2)
    if_lv = round(isc_lv * 0.9, 2)
    if_hv = round(if_lv / (hv_kv / lv_kv), 2)

    total_load = 0.0
    ct_alerts = []

    feeder_oc_txt = ""
    feeder_ef_txt = ""
    max_t_oc = 0.0
    max_t_ef = 0.0

    for i, f in enumerate(feeders):
        l = float(f["load"])
        ct = float(f["ct"])
        total_load += l

        if ct < l:
            ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct}A) is less than Load ({l}A)")

        p_oc = round(1.1 * l, 2)
        r1 = round(p_oc / ct, 2) if ct else 0.0
        t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv / p_oc), 0.02) - 1.0)), 3)
        max_t_oc = max(max_t_oc, t_oc)
        p2 = round(3.0 * l, 2)
        r2 = round(p2 / ct, 2) if ct else 0.0
        feeder_oc_txt += (
            f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n"
            f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n"
            f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"
        )

        p_ef = round(0.15 * l, 2)
        r_ef1 = round(p_ef / ct, 2) if ct else 0.0
        t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv / p_ef), 0.02) - 1.0)), 3)
        max_t_ef = max(max_t_ef, t_ef)
        p_ef2 = round(1.0 * l, 2)
        r_ef2 = round(p_ef2 / ct, 2) if ct else 0.0
        feeder_ef_txt += (
            f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n"
            f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n"
            f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"
        )

    hv_load = total_load / (hv_kv / lv_kv)

    if q4_ct < total_load:
        ct_alerts.append(f"ALERT: Q4 Incomer CT ({q4_ct}A) is less than Total Load ({total_load}A)")

    if q5_ct < hv_load:
        ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) is less than HV Load ({round(hv_load, 2)}A)")

    coord_data = [
        ("INCOMER Q4 (LV)", q4_ct, if_lv, 1.0, round(0.9 * isc_lv, 2), cti_ms, max_t_oc, max_t_ef),
        ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_kv / lv_kv, round(if_hv, 2), cti_ms * 2.0, max_t_oc + cti_s, max_t_ef + cti_s),
    ]

    incomer_oc = ""
    incomer_ef = ""

    for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
        l_cur = total_load / scale
        t_req_oc = round(t_prev_oc + cti_s, 3)
        t_req_ef = round(t_prev_ef + cti_s, 3)

        p_oc = round(1.1 * l_cur, 2)
        r1 = round(p_oc / ct_v, 2) if ct_v else 0.0
        tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault / p_oc), 0.02) - 1.0)), 3)

        p2 = round(3.0 * l_cur, 2)
        r2 = round(p2 / ct_v, 2) if ct_v else 0.0
        r3 = round(s3 / ct_v, 2) if ct_v else 0.0

        incomer_oc += (
            f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n"
            f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n"
            f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000.0}s\n"
            f" - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"
        )

        p_ef = round(0.15 * l_cur, 2)
        r_ef1 = round(p_ef / ct_v, 2) if ct_v else 0.0
        tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault / p_ef), 0.02) - 1.0)), 3)
        p_ef2 = round(1.0 * l_cur, 2)
        r_ef2 = round(p_ef2 / ct_v, 2) if ct_v else 0.0
        r_ef3 = round(s3 / ct_v, 2) if ct_v else 0.0

        incomer_ef += (
            f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n"
            f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n"
            f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000.0}s\n"
            f" - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"
        )

    head = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "=" * 60 + "\n"

    oc_report = head + feeder_oc_txt + incomer_oc
    ef_report = head + feeder_ef_txt + incomer_ef

    critical_overload = total_load > flc_lv

    return {
        "flc_lv": flc_lv,
        "flc_hv": flc_hv,
        "isc_lv": isc_lv,
        "if_lv": if_lv,
        "if_hv": if_hv,
        "total_load": round(total_load, 2),
        "hv_load": round(hv_load, 2),
        "critical_overload": critical_overload,
        "alerts": ct_alerts,
        "oc_report": oc_report,
        "ef_report": ef_report,
    }
