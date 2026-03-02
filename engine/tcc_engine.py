"""
TCC Engine (logic-only)

Refactors the computational logic from your Tkinter GUI_Final5.py into pure functions.
Streamlit UI must call compute_tcc() and must NOT implement formulas itself.

Keeps key behaviors:
- IEC curve constants/formula
- merged curve = min(enabled stages) at each current
- DT2 applies only to Q4 & Q5
- Q5 current scaling by HV/LV
- clamp fault current to LV Isc
- intersection trip time = min(stage times at fault), rounded to 3 decimals
- CTI constants (0.150/0.300/0.150)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np


# --- CTI VALUES (same as Tkinter suite) ---
CTI_Q1_Q4 = 0.150
CTI_Q1_Q5 = 0.300
CTI_Q4_Q5 = 0.150


def iec_curve(I: float, Ip: float, TMS: float, curve: str) -> float:
    """IEC 60255 inverse-time curve (same constants as your GUI)."""
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


@dataclass(frozen=True)
class TransformerInputs:
    mva: float
    hv_kv: float
    lv_kv: float
    z_pct: float


@dataclass(frozen=True)
class StageSettings:
    # IDMT
    idmt_enabled: bool
    pickup_ip: float
    tms: float
    curve: str  # Standard/Very/Extremely Inverse

    # DT1
    dt1_enabled: bool
    dt1_pickup: float
    dt1_time: float

    # DT2 (only applies for Q4 & Q5)
    dt2_enabled: bool
    dt2_pickup: float
    dt2_time: float


@dataclass(frozen=True)
class TCCInputs:
    transformer: TransformerInputs
    fault_current_a: Optional[float]     # None allowed
    relays: List[StageSettings]          # must be length 5


@dataclass(frozen=True)
class TransformerResults:
    flc_lv: Optional[float]
    isc_lv: Optional[float]
    hv_factor: float


@dataclass(frozen=True)
class TCCResults:
    currents: np.ndarray
    curves: Dict[str, np.ndarray]        # "Q1".."Q5" merged curve arrays
    trip_times: Dict[str, float]         # "Q1".."Q5" rounded trip time at fault current
    transformer: TransformerResults
    fault_current_used_a: Optional[float]
    warnings: List[str]
    report_text: str


def transformer_calculations(inp: TransformerInputs) -> TransformerResults:
    try:
        MVA = float(inp.mva)
        LV = float(inp.lv_kv)
        HV = float(inp.hv_kv)
        Z = float(inp.z_pct)
        flc_lv = (MVA * 1000) / (np.sqrt(3) * LV)
        isc_lv = flc_lv / (Z / 100)
        hv_factor = HV / LV
        return TransformerResults(flc_lv=flc_lv, isc_lv=isc_lv, hv_factor=hv_factor)
    except Exception:
        return TransformerResults(flc_lv=None, isc_lv=None, hv_factor=1.0)


def _merged_time_for_current(I_scaled: float, stage: StageSettings, allow_dt2: bool) -> float:
    """Merged curve = min(IDMT, DT1, DT2) among enabled stages, else NaN."""
    times: List[float] = []

    if stage.idmt_enabled:
        t = iec_curve(I_scaled, stage.pickup_ip, stage.tms, stage.curve)
        if not np.isnan(t):
            times.append(float(t))

    if stage.dt1_enabled:
        if I_scaled >= float(stage.dt1_pickup):
            times.append(float(stage.dt1_time))

    if allow_dt2 and stage.dt2_enabled:
        if I_scaled >= float(stage.dt2_pickup):
            times.append(float(stage.dt2_time))

    return min(times) if times else np.nan


def _intersection_time_at_fault(I_fault_scaled: float, stage: StageSettings, allow_dt2: bool) -> Optional[float]:
    """Trip time at fault = min(enabled stage times evaluated at fault)."""
    times: List[float] = []

    if stage.idmt_enabled:
        t = iec_curve(I_fault_scaled, stage.pickup_ip, stage.tms, stage.curve)
        if not np.isnan(t):
            times.append(float(t))

    if stage.dt1_enabled:
        if I_fault_scaled >= float(stage.dt1_pickup):
            times.append(float(stage.dt1_time))

    if allow_dt2 and stage.dt2_enabled:
        if I_fault_scaled >= float(stage.dt2_pickup):
            times.append(float(stage.dt2_time))

    if not times:
        return None
    return min(times)


def build_report(trip_times: Dict[str, float], tr: TransformerResults, fault_current: Optional[float]) -> str:
    out = []
    out.append("Coordination Report")
    out.append("=" * 20)

    if tr.flc_lv is not None and tr.isc_lv is not None:
        out.append(f"LV FLC: {tr.flc_lv:.3f} A | LV Isc: {tr.isc_lv:.3f} A")

    if fault_current is not None:
        out.append(f"Fault Current: {fault_current:.3f} A")
        out.append("")

    for q in sorted(trip_times.keys()):
        out.append(f"{q} Trip: {trip_times[q]:.3f} s")

    out.append("")
    out.append("Coordination Results:")

    checks = [
        ("Q1", "Q4", CTI_Q1_Q4), ("Q2", "Q4", CTI_Q1_Q4), ("Q3", "Q4", CTI_Q1_Q4),
        ("Q1", "Q5", CTI_Q1_Q5), ("Q2", "Q5", CTI_Q1_Q5), ("Q3", "Q5", CTI_Q1_Q5),
        ("Q4", "Q5", CTI_Q4_Q5),
    ]
    for d, u, cti in checks:
        if d in trip_times and u in trip_times:
            margin = trip_times[u] - trip_times[d]
            out.append(f"{d}->{u}: {margin:.3f}s {'OK' if margin >= cti else 'NOT OK'}")

    return "\n".join(out)


def compute_tcc(inp: TCCInputs) -> TCCResults:
    # Same domain you used (logspace 1..5, 800 points)
    currents = np.logspace(1, 5, 800)

    tr = transformer_calculations(inp.transformer)
    warnings: List[str] = []

    fault_used = inp.fault_current_a

    # Clamp fault current to LV Isc
    if tr.isc_lv and fault_used and fault_used > tr.isc_lv:
        warnings.append("Fault current exceeds LV short circuit current; clamped to LV Isc.")
        fault_used = float(tr.isc_lv)

    curves: Dict[str, np.ndarray] = {}
    trip_times: Dict[str, float] = {}

    for i in range(5):
        stage = inp.relays[i]

        # Q5 scaling rule: current scaled by HV/LV
        current_scaling = tr.hv_factor if i == 4 else 1.0

        # DT2 only for Q4 & Q5
        allow_dt2 = (i >= 3)

        merged = []
        for I in currents:
            I_scaled = float(I) / float(current_scaling)
            merged.append(_merged_time_for_current(I_scaled, stage, allow_dt2))

        curves[f"Q{i+1}"] = np.array(merged, dtype=float)

        # Intersection at fault
        if fault_used is not None:
            I_fault_scaled = float(fault_used) / float(current_scaling)
            t = _intersection_time_at_fault(I_fault_scaled, stage, allow_dt2)
            if t is not None:
                trip_times[f"Q{i+1}"] = round(float(t), 3)

    report_text = build_report(trip_times, tr, fault_used)

    return TCCResults(
        currents=currents,
        curves=curves,
        trip_times=trip_times,
        transformer=tr,
        fault_current_used_a=fault_used,
        warnings=warnings,
        report_text=report_text,
    )
