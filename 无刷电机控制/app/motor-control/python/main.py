import time

from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI

ui = WebUI()

TELEMETRY_INTERVAL_SEC = 0.05
AUTO_TUNE_SETTLE_SEC = 0.65
AUTO_TUNE_STEP_SEC = 1.8
AUTO_TUNE_DEFAULT_STEP_RAD = 0.5
AUTO_TUNE_DEFAULT_MAX_VOLTAGE = 2.5
AUTO_TUNE_VELOCITY_LIMIT = 15.0
AUTO_TUNE_DEFAULT_MAX_VELOCITY = 25.0
AUTO_TUNE_FIXED_VELOCITY_D = 0.0
AUTO_TUNE_SMALL_STEP_RATIO = 0.18
AUTO_TUNE_MIN_SMALL_STEP_RAD = 0.05
AUTO_TUNE_MAX_SMALL_STEP_RAD = 0.12
AUTO_TUNE_STEP_TOTAL = 4
AUTO_TUNE_MIN_ABORT_OBSERVE_SEC = 0.25
AUTO_TUNE_MAX_OVERSHOOT_RAD = 0.08
AUTO_TUNE_MAX_OVERSHOOT_RATIO = 0.35
AUTO_TUNE_MAX_ERROR_RATIO = 1.65
AUTO_TUNE_MAX_VELOCITY_RATIO = 1.35
AUTO_TUNE_MAX_SMALL_FINAL_ERROR_RAD = 0.018
AUTO_TUNE_MAX_SMALL_STEADY_ERROR_RAD = 0.018
AUTO_TUNE_MAX_SMALL_JITTER_RAD = 0.006

last_telemetry = None
auto_tune = {
    "active": False,
    "phase": "idle",
    "stage": "idle",
    "started_at": 0.0,
    "phase_started_at": 0.0,
    "candidate_index": 0,
    "step_index": 0,
    "candidates": [],
    "pending_stages": [],
    "samples": [],
    "step_results": [],
    "results": [],
    "baseline": 0.0,
    "step_target": 0.0,
    "step_size": AUTO_TUNE_DEFAULT_STEP_RAD,
    "max_voltage": AUTO_TUNE_DEFAULT_MAX_VOLTAGE,
    "max_velocity_limit": AUTO_TUNE_DEFAULT_MAX_VELOCITY,
    "active_voltage_limit": AUTO_TUNE_DEFAULT_MAX_VOLTAGE,
    "active_velocity_limit": AUTO_TUNE_VELOCITY_LIMIT,
    "tune_d": False,
    "tune_velocity_limit": False,
    "tune_voltage_limit": False,
    "original": None,
    "best": None,
}

print("Brushless motor control app started.")
print("The SimpleFOC control loop runs on the UNO Q MCU sketch.")
print("Open the Web UI to tune target angle, limits, and PID parameters.")


def parse_telemetry(raw):
    """Parse the CSV telemetry string returned by the MCU sketch."""
    fields = str(raw).split(",")
    if len(fields) != 12:
        raise ValueError(f"Expected 12 telemetry fields, got {len(fields)}: {raw}")

    return {
        "millis": int(float(fields[0])),
        "target_angle": float(fields[1]),
        "shaft_angle": float(fields[2]),
        "shaft_velocity": float(fields[3]),
        "angle_error": float(fields[4]),
        "voltage_limit": float(fields[5]),
        "velocity_limit": float(fields[6]),
        "angle_p": float(fields[7]),
        "velocity_p": float(fields[8]),
        "velocity_i": float(fields[9]),
        "velocity_d": float(fields[10]),
        "enabled": fields[11].strip() == "1",
    }


def call_mcu(method, *args):
    """Call an MCU RPC method and report the result to the Web UI."""
    try:
        ok = Bridge.call(method, *args)
    except Exception as exc:
        ui.send_message("status", message={"ok": False, "message": f"{method} failed: {exc}"})
        return False

    ui.send_message("status", message={"ok": bool(ok), "message": f"{method}: {'ok' if ok else 'failed'}"})
    return bool(ok)


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, float(value)))


def call_mcu_quiet(method, *args):
    try:
        return bool(Bridge.call(method, *args))
    except Exception as exc:
        ui.send_message("status", message={"ok": False, "message": f"{method} failed: {exc}"})
        return False


def handle_set_target(_sid, value):
    call_mcu("set_target_angle", float(value))


def handle_set_voltage_limit(_sid, value):
    call_mcu("set_voltage_limit", float(value))


def handle_set_velocity_limit(_sid, value):
    call_mcu("set_velocity_limit", float(value))


def handle_set_angle_p(_sid, value):
    call_mcu("set_angle_p", float(value))


def handle_set_velocity_p(_sid, value):
    call_mcu("set_velocity_p", float(value))


def handle_set_velocity_i(_sid, value):
    call_mcu("set_velocity_i", float(value))


def handle_set_velocity_d(_sid, value):
    call_mcu("set_velocity_d", float(value))


def handle_hold(_sid, *_args):
    call_mcu("hold_current_angle")


def handle_set_enabled(_sid, value):
    call_mcu("set_motor_enabled", bool(value))


def make_candidate(
    angle_p,
    velocity_p,
    velocity_i,
    velocity_d=AUTO_TUNE_FIXED_VELOCITY_D,
    stage="custom",
    voltage_limit=None,
    velocity_limit=None,
):
    candidate = {
        "stage": stage,
        "angle_p": round(clamp(angle_p, 1.0, 70.0), 4),
        "velocity_p": round(clamp(velocity_p, 0.005, 0.5), 4),
        "velocity_i": round(clamp(velocity_i, 0.0, 0.2), 4),
        "velocity_d": round(clamp(velocity_d, 0.0, 0.2), 4),
    }
    if voltage_limit is not None:
        candidate["voltage_limit"] = round(clamp(voltage_limit, 0.5, 4.0), 3)
    if velocity_limit is not None:
        candidate["velocity_limit"] = round(clamp(velocity_limit, 1.0, 50.0), 3)
    return candidate


def candidate_voltage_limit(candidate):
    return candidate.get("voltage_limit", auto_tune.get("active_voltage_limit", auto_tune["max_voltage"]))


def candidate_velocity_limit(candidate):
    return candidate.get("velocity_limit", auto_tune.get("active_velocity_limit", AUTO_TUNE_VELOCITY_LIMIT))


def current_candidate_velocity_limit():
    try:
        candidate = auto_tune["candidates"][auto_tune["candidate_index"]]
    except (IndexError, KeyError):
        return auto_tune.get("active_velocity_limit", AUTO_TUNE_VELOCITY_LIMIT)
    return candidate_velocity_limit(candidate)


def unique_candidates(candidates):
    seen = set()
    unique = []
    for candidate in candidates:
        key = (
            candidate["stage"],
            candidate["angle_p"],
            candidate["velocity_p"],
            candidate["velocity_i"],
            candidate["velocity_d"],
            candidate.get("voltage_limit"),
            candidate.get("velocity_limit"),
        )
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def build_coarse_angle_candidates(base_velocity_p=0.055, base_velocity_i=0.018):
    return [
        make_candidate(
            angle_p,
            base_velocity_p,
            base_velocity_i,
            stage="coarse_angle",
            voltage_limit=auto_tune["active_voltage_limit"],
            velocity_limit=auto_tune["active_velocity_limit"],
        )
        for angle_p in (8.0, 12.0, 16.0, 22.0, 28.0, 36.0, 46.0)
    ]


def build_fine_angle_candidates(best):
    center = best["angle_p"]
    return unique_candidates(
        [
            make_candidate(
                center + delta,
                best["velocity_p"],
                best["velocity_i"],
                best["velocity_d"],
                stage="fine_angle",
                voltage_limit=candidate_voltage_limit(best),
                velocity_limit=candidate_velocity_limit(best),
            )
            for delta in (-6.0, -3.0, -1.5, 0.0, 1.5, 3.0, 6.0)
        ]
    )


def build_velocity_candidates(best):
    p_values = [
        best["velocity_p"] * factor
        for factor in (0.7, 0.9, 1.0, 1.2, 1.45, 1.75)
    ]
    i_values = unique_values([
        0.006,
        0.012,
        0.018,
        0.026,
        0.036,
        best["velocity_i"] * 0.8,
        best["velocity_i"],
        best["velocity_i"] * 1.4,
        best["velocity_i"] * 1.9,
    ])

    candidates = []
    for velocity_p in p_values:
        for velocity_i in i_values:
            candidates.append(
                make_candidate(
                    best["angle_p"],
                    velocity_p,
                    velocity_i,
                    best["velocity_d"],
                    stage="velocity_pi",
                    voltage_limit=candidate_voltage_limit(best),
                    velocity_limit=candidate_velocity_limit(best),
                )
            )
    return unique_candidates(candidates)


def build_velocity_d_candidates(best):
    d_values = unique_values(
        [
            0.0,
            0.0003,
            0.0006,
            0.001,
            0.0015,
            0.0025,
            0.004,
            best["velocity_d"],
        ]
    )
    return [
        make_candidate(
            best["angle_p"],
            best["velocity_p"],
            best["velocity_i"],
            velocity_d,
            stage="velocity_d",
            voltage_limit=candidate_voltage_limit(best),
            velocity_limit=candidate_velocity_limit(best),
        )
        for velocity_d in d_values
    ]


def build_velocity_limit_candidates(best):
    current = candidate_velocity_limit(best)
    max_velocity = auto_tune["max_velocity_limit"]
    values = unique_limit_values(
        [
            current * 0.75,
            current,
            current * 1.2,
            10.0,
            15.0,
            20.0,
            max_velocity,
        ],
        8.0,
        max_velocity,
        1,
    )
    return [
        make_candidate(
            best["angle_p"],
            best["velocity_p"],
            best["velocity_i"],
            best["velocity_d"],
            stage="velocity_limit",
            voltage_limit=candidate_voltage_limit(best),
            velocity_limit=velocity_limit,
        )
        for velocity_limit in values
    ]


def build_voltage_limit_candidates(best):
    current = candidate_voltage_limit(best)
    max_voltage = auto_tune["max_voltage"]
    values = unique_limit_values(
        [
            current * 0.75,
            current,
            max_voltage * 0.55,
            max_voltage * 0.7,
            max_voltage * 0.85,
            max_voltage,
        ],
        0.5,
        max_voltage,
        2,
    )
    return [
        make_candidate(
            best["angle_p"],
            best["velocity_p"],
            best["velocity_i"],
            best["velocity_d"],
            stage="voltage_limit",
            voltage_limit=voltage_limit,
            velocity_limit=candidate_velocity_limit(best),
        )
        for voltage_limit in values
    ]


def build_confirmation_candidates(best):
    return [
        make_candidate(
            best["angle_p"],
            best["velocity_p"],
            best["velocity_i"],
            best["velocity_d"],
            stage="confirm",
            voltage_limit=candidate_voltage_limit(best),
            velocity_limit=candidate_velocity_limit(best),
        )
    ]


def unique_values(values):
    result = []
    seen = set()
    for value in values:
        rounded = round(clamp(value, 0.0, 0.2), 4)
        if rounded not in seen:
            seen.add(rounded)
            result.append(rounded)
    return result


def unique_limit_values(values, min_value, max_value, digits):
    result = []
    seen = set()
    for value in values:
        rounded = round(clamp(value, min_value, max_value), digits)
        if rounded not in seen:
            seen.add(rounded)
            result.append(rounded)
    return result


def apply_candidate(candidate):
    if "voltage_limit" in candidate:
        call_mcu_quiet("set_voltage_limit", candidate["voltage_limit"])
    if "velocity_limit" in candidate:
        call_mcu_quiet("set_velocity_limit", candidate["velocity_limit"])
    call_mcu_quiet("set_angle_p", candidate["angle_p"])
    call_mcu_quiet("set_velocity_p", candidate["velocity_p"])
    call_mcu_quiet("set_velocity_i", candidate["velocity_i"])
    call_mcu_quiet("set_velocity_d", candidate["velocity_d"])


def send_auto_tune_update():
    total = len(auto_tune["candidates"])
    index = auto_tune["candidate_index"]
    ui.send_message(
        "autotune",
        message={
            "active": auto_tune["active"],
            "phase": auto_tune["phase"],
            "stage": auto_tune["stage"],
            "candidate_index": index,
            "candidate_total": total,
            "step_index": auto_tune["step_index"],
            "step_total": AUTO_TUNE_STEP_TOTAL,
            "results": auto_tune["results"],
            "best": auto_tune["best"],
            "step_size": auto_tune["step_size"],
            "max_voltage": auto_tune["max_voltage"],
            "max_velocity_limit": auto_tune["max_velocity_limit"],
            "tune_d": auto_tune["tune_d"],
            "tune_velocity_limit": auto_tune["tune_velocity_limit"],
            "tune_voltage_limit": auto_tune["tune_voltage_limit"],
        },
    )


def start_candidate(index):
    candidate = auto_tune["candidates"][index]
    auto_tune["candidate_index"] = index
    auto_tune["step_index"] = 0
    auto_tune["phase"] = "settle"
    auto_tune["phase_started_at"] = time.time()
    auto_tune["samples"] = []
    auto_tune["step_results"] = []

    apply_candidate(candidate)
    call_mcu_quiet("set_target_angle", auto_tune["baseline"])
    send_auto_tune_update()


def current_step_target():
    direction = 1.0 if auto_tune["step_index"] % 2 == 0 else -1.0
    amplitude = current_step_amplitude()
    return auto_tune["baseline"] + direction * amplitude


def current_step_amplitude():
    if auto_tune["step_index"] < 2:
        return auto_tune["step_size"]
    return clamp(
        auto_tune["step_size"] * AUTO_TUNE_SMALL_STEP_RATIO,
        AUTO_TUNE_MIN_SMALL_STEP_RAD,
        AUTO_TUNE_MAX_SMALL_STEP_RAD,
    )


def evaluate_step(samples, target):
    if not samples:
        return {
            "score": 9999.0,
            "overshoot": 999.0,
            "settling_time": AUTO_TUNE_STEP_SEC,
            "steady_error": 999.0,
            "jitter": 999.0,
            "max_velocity": 999.0,
            "final_error": 999.0,
            "rejected": True,
            "reject_reason": "no samples",
        }

    start_angle = samples[0]["shaft_angle"]
    direction = 1.0 if target >= start_angle else -1.0
    command_step = max(0.01, abs(target - start_angle))
    small_step = command_step <= auto_tune["step_size"] * 0.45
    threshold = max(0.012 if small_step else 0.025, command_step * (0.12 if small_step else 0.08))
    errors = [abs(target - s["shaft_angle"]) for s in samples]
    signed_positions = [(s["shaft_angle"] - target) * direction for s in samples]
    overshoot = max(0.0, max(signed_positions))

    settling_time = AUTO_TUNE_STEP_SEC
    for idx, _sample in enumerate(samples):
        window_errors = errors[idx:]
        if window_errors and max(window_errors) <= threshold:
            settling_time = (samples[idx]["millis"] - samples[0]["millis"]) / 1000.0
            break

    tail = samples[max(0, int(len(samples) * 0.7)) :]
    tail_errors = [abs(target - s["shaft_angle"]) for s in tail] or errors
    steady_error = sum(tail_errors) / len(tail_errors)
    tail_angles = [s["shaft_angle"] for s in tail]
    if len(tail_angles) >= 2:
        mean_angle = sum(tail_angles) / len(tail_angles)
        jitter = (sum((v - mean_angle) ** 2 for v in tail_angles) / len(tail_angles)) ** 0.5
    else:
        jitter = 0.0

    max_velocity = max(abs(s["shaft_velocity"]) for s in samples)
    final_error = errors[-1]
    if small_step:
        score = (
            settling_time * 0.75
            + steady_error * 34.0
            + final_error * 18.0
            + overshoot * 14.0
            + jitter * 55.0
            + max(0.0, max_velocity - current_candidate_velocity_limit() * 0.55) * 0.25
        )
    else:
        score = (
            settling_time * 1.05
            + steady_error * 16.0
            + final_error * 8.0
            + overshoot * 10.0
            + jitter * 24.0
            + max(0.0, max_velocity - current_candidate_velocity_limit() * 0.9) * 0.2
        )

    return {
        "score": round(score, 4),
        "overshoot": round(overshoot, 4),
        "settling_time": round(settling_time, 3),
        "steady_error": round(steady_error, 4),
        "jitter": round(jitter, 4),
        "max_velocity": round(max_velocity, 4),
        "final_error": round(final_error, 4),
        "small_step": small_step,
        "rejected": small_step and (
            final_error > AUTO_TUNE_MAX_SMALL_FINAL_ERROR_RAD
            or steady_error > AUTO_TUNE_MAX_SMALL_STEADY_ERROR_RAD
            or jitter > AUTO_TUNE_MAX_SMALL_JITTER_RAD
        ),
        "reject_reason": (
            "small angle hold error"
            if small_step and (
                final_error > AUTO_TUNE_MAX_SMALL_FINAL_ERROR_RAD
                or steady_error > AUTO_TUNE_MAX_SMALL_STEADY_ERROR_RAD
                or jitter > AUTO_TUNE_MAX_SMALL_JITTER_RAD
            )
            else ""
        ),
    }


def evaluate_candidate(candidate, step_results):
    if not step_results:
        return {
            **candidate,
            "score": 9999.0,
            "overshoot": 999.0,
            "settling_time": AUTO_TUNE_STEP_SEC,
            "steady_error": 999.0,
            "jitter": 999.0,
            "max_velocity": 999.0,
            "final_error": 999.0,
            "rejected": True,
            "reject_reason": "no step result",
        }

    rejected_steps = [step for step in step_results if step.get("rejected")]
    averaged = {}
    for key in ("score", "overshoot", "settling_time", "steady_error", "jitter", "max_velocity", "final_error"):
        averaged[key] = round(sum(step[key] for step in step_results) / len(step_results), 4)

    small_steps = [step for step in step_results if step.get("small_step")]
    if small_steps:
        averaged["small_steady_error"] = round(sum(step["steady_error"] for step in small_steps) / len(small_steps), 4)
        averaged["small_jitter"] = round(sum(step["jitter"] for step in small_steps) / len(small_steps), 4)
        max_small_final = max(step["final_error"] for step in small_steps)
        averaged["small_final_error"] = round(max_small_final, 4)
        averaged["score"] = round(
            averaged["score"]
            + averaged["small_steady_error"] * 60.0
            + averaged["small_jitter"] * 90.0
            + averaged["small_final_error"] * 45.0,
            4,
        )
    else:
        averaged["small_steady_error"] = 999.0
        averaged["small_jitter"] = 999.0
        averaged["small_final_error"] = 999.0
        averaged["score"] = 9999.0

    rejected = bool(rejected_steps)
    reject_reason = "; ".join(sorted({step.get("reject_reason", "rejected") for step in rejected_steps}))
    if rejected:
        averaged["score"] = 9999.0

    return {
        **candidate,
        **averaged,
        "steps": len(step_results),
        "small_steady_error": averaged["small_steady_error"],
        "small_jitter": averaged["small_jitter"],
        "small_final_error": averaged["small_final_error"],
        "rejected": rejected,
        "reject_reason": reject_reason,
    }


def best_result_for_stage(stage):
    stage_results = [
        result
        for result in auto_tune["results"]
        if result["stage"] == stage and not result.get("rejected")
    ]
    if not stage_results:
        return None
    return min(stage_results, key=lambda item: item["score"])


def best_valid_result():
    valid_results = [result for result in auto_tune["results"] if not result.get("rejected")]
    if not valid_results:
        return None
    return min(valid_results, key=lambda item: item["score"])


def check_step_abort(samples, target):
    if len(samples) < 4:
        return None

    elapsed = (samples[-1]["millis"] - samples[0]["millis"]) / 1000.0
    if elapsed < AUTO_TUNE_MIN_ABORT_OBSERVE_SEC:
        return None

    start_angle = samples[0]["shaft_angle"]
    step_amplitude = max(0.05, abs(target - start_angle))
    direction = 1.0 if target >= start_angle else -1.0
    latest = samples[-1]

    small_step = step_amplitude <= auto_tune["step_size"] * 0.45
    overshoot_limit = max(
        0.025 if small_step else AUTO_TUNE_MAX_OVERSHOOT_RAD,
        step_amplitude * (0.22 if small_step else AUTO_TUNE_MAX_OVERSHOOT_RATIO),
    )
    overshoot = max(0.0, max((sample["shaft_angle"] - target) * direction for sample in samples))
    if overshoot > overshoot_limit:
        return f"overshoot {overshoot:.3f} rad"

    latest_error = abs(target - latest["shaft_angle"])
    if elapsed > 0.45 and latest_error > step_amplitude * AUTO_TUNE_MAX_ERROR_RATIO:
        return f"diverging error {latest_error:.3f} rad"

    progress = (latest["shaft_angle"] - start_angle) * direction
    if elapsed > 0.45 and progress < -max(0.04, step_amplitude * 0.2):
        return "moving away from target"

    max_velocity = max(abs(sample["shaft_velocity"]) for sample in samples)
    velocity_limit = current_candidate_velocity_limit() * (0.75 if small_step else AUTO_TUNE_MAX_VELOCITY_RATIO)
    if max_velocity > velocity_limit:
        return f"velocity spike {max_velocity:.2f} rad/s"

    recent = samples[-min(len(samples), 10) :]
    if len(recent) >= 6:
        angles = [sample["shaft_angle"] for sample in recent]
        peak_to_peak = max(angles) - min(angles)
        velocity_sign_changes = 0
        last_sign = 0
        for sample in recent:
            velocity = sample["shaft_velocity"]
            sign = 1 if velocity > 0.02 else -1 if velocity < -0.02 else 0
            if sign and last_sign and sign != last_sign:
                velocity_sign_changes += 1
            if sign:
                last_sign = sign
        oscillation_limit = max(0.025 if small_step else 0.08, step_amplitude * (0.35 if small_step else 0.45))
        if peak_to_peak > oscillation_limit and velocity_sign_changes >= 3:
            return f"oscillation {peak_to_peak:.3f} rad"

    return None


def start_stage(stage, candidates):
    auto_tune["stage"] = stage
    auto_tune["candidates"] = unique_candidates(candidates)
    auto_tune["candidate_index"] = 0
    start_candidate(0)


def maybe_start_next_stage():
    current_stage = auto_tune["stage"]
    best = best_result_for_stage(current_stage)
    if not best:
        finish_auto_tune(apply_best=False, reason=f"{current_stage}_failed")
        ui.send_message(
            "status",
            message={
                "ok": False,
                "message": f"Auto Tune stopped: all candidates in {current_stage} were rejected.",
            },
        )
        return False

    if current_stage == "coarse_angle":
        start_stage("fine_angle", build_fine_angle_candidates(best))
        return True

    if current_stage == "fine_angle":
        start_stage("velocity_pi", build_velocity_candidates(best))
        return True

    if current_stage == "velocity_pi":
        if auto_tune["tune_d"]:
            start_stage("velocity_d", build_velocity_d_candidates(best))
            return True
        if auto_tune["tune_velocity_limit"]:
            start_stage("velocity_limit", build_velocity_limit_candidates(best))
            return True
        if auto_tune["tune_voltage_limit"]:
            start_stage("voltage_limit", build_voltage_limit_candidates(best))
            return True
        start_stage("confirm", build_confirmation_candidates(best))
        return True

    if current_stage == "velocity_d":
        if auto_tune["tune_velocity_limit"]:
            start_stage("velocity_limit", build_velocity_limit_candidates(best))
            return True
        if auto_tune["tune_voltage_limit"]:
            start_stage("voltage_limit", build_voltage_limit_candidates(best))
            return True
        start_stage("confirm", build_confirmation_candidates(best))
        return True

    if current_stage == "velocity_limit":
        if auto_tune["tune_voltage_limit"]:
            start_stage("voltage_limit", build_voltage_limit_candidates(best))
            return True
        start_stage("confirm", build_confirmation_candidates(best))
        return True

    if current_stage == "voltage_limit":
        start_stage("confirm", build_confirmation_candidates(best))
        return True

    return False


def finish_auto_tune(apply_best=False, reason="done"):
    auto_tune["active"] = False
    auto_tune["phase"] = reason

    if auto_tune["results"]:
        confirm_best = best_result_for_stage("confirm")
        auto_tune["best"] = confirm_best or best_valid_result()
        if apply_best:
            if auto_tune["best"]:
                apply_candidate(auto_tune["best"])
            elif auto_tune["original"]:
                apply_candidate(auto_tune["original"])
    elif auto_tune["original"]:
        apply_candidate(auto_tune["original"])

    if reason.endswith("_failed"):
        auto_tune["best"] = None

    if (reason == "stopped" or reason.endswith("_failed")) and auto_tune["original"]:
        apply_candidate(auto_tune["original"])
        call_mcu_quiet("set_voltage_limit", auto_tune["original"]["voltage_limit"])
        call_mcu_quiet("set_velocity_limit", auto_tune["original"]["velocity_limit"])
        call_mcu_quiet("set_target_angle", auto_tune["baseline"])

    send_auto_tune_update()


def handle_auto_tune_start(_sid, config=None):
    if last_telemetry is None:
        ui.send_message("status", message={"ok": False, "message": "Auto Tune needs telemetry first."})
        return

    config = config or {}
    step_size = clamp(config.get("step_size", AUTO_TUNE_DEFAULT_STEP_RAD), 0.1, 1.0)
    max_voltage = clamp(config.get("max_voltage", AUTO_TUNE_DEFAULT_MAX_VOLTAGE), 0.5, 4.0)
    max_velocity_limit = clamp(config.get("max_velocity", AUTO_TUNE_DEFAULT_MAX_VELOCITY), 8.0, 35.0)
    active_velocity_limit = min(AUTO_TUNE_VELOCITY_LIMIT, max_velocity_limit)

    auto_tune.update(
        {
            "active": True,
            "phase": "settle",
            "started_at": time.time(),
            "phase_started_at": time.time(),
            "candidate_index": 0,
            "step_index": 0,
            "candidates": [],
            "samples": [],
            "step_results": [],
            "results": [],
            "baseline": last_telemetry["shaft_angle"],
            "step_target": last_telemetry["shaft_angle"] + step_size,
            "step_size": step_size,
            "max_voltage": max_voltage,
            "max_velocity_limit": max_velocity_limit,
            "active_voltage_limit": max_voltage,
            "active_velocity_limit": active_velocity_limit,
            "tune_d": bool(config.get("tune_d", False)),
            "tune_velocity_limit": bool(config.get("tune_velocity_limit", False)),
            "tune_voltage_limit": bool(config.get("tune_voltage_limit", False)),
            "original": {
                "stage": "original",
                "angle_p": last_telemetry["angle_p"],
                "velocity_p": last_telemetry["velocity_p"],
                "velocity_i": last_telemetry["velocity_i"],
                "velocity_d": last_telemetry["velocity_d"],
                "voltage_limit": last_telemetry["voltage_limit"],
                "velocity_limit": last_telemetry["velocity_limit"],
            },
            "best": None,
        }
    )

    call_mcu_quiet("set_motor_enabled", True)
    call_mcu_quiet("set_voltage_limit", max_voltage)
    call_mcu_quiet("set_velocity_limit", active_velocity_limit)
    start_stage("coarse_angle", build_coarse_angle_candidates())
    ui.send_message("status", message={"ok": True, "message": "Auto Tune started."})


def handle_auto_tune_stop(_sid, *_args):
    if auto_tune["active"]:
        finish_auto_tune(apply_best=False, reason="stopped")
        ui.send_message("status", message={"ok": True, "message": "Auto Tune stopped and original gains restored."})


def handle_apply_auto_tune(_sid, *_args):
    best = auto_tune.get("best")
    if not best or best.get("rejected"):
        ui.send_message("status", message={"ok": False, "message": "No Auto Tune recommendation to apply."})
        return
    apply_candidate(best)
    ui.send_message("status", message={"ok": True, "message": "Applied recommended Auto Tune gains."})
    send_auto_tune_update()


def advance_auto_tune(telemetry):
    if not auto_tune["active"]:
        return

    now = time.time()
    elapsed = now - auto_tune["phase_started_at"]

    if auto_tune["phase"] == "settle" and elapsed >= AUTO_TUNE_SETTLE_SEC:
        auto_tune["phase"] = "step"
        auto_tune["phase_started_at"] = now
        auto_tune["samples"] = []
        auto_tune["step_target"] = current_step_target()
        call_mcu_quiet("set_target_angle", auto_tune["step_target"])
        send_auto_tune_update()
        return

    if auto_tune["phase"] == "step":
        auto_tune["samples"].append(dict(telemetry))
        abort_reason = check_step_abort(auto_tune["samples"], auto_tune["step_target"])
        if abort_reason:
            candidate = auto_tune["candidates"][auto_tune["candidate_index"]]
            rejected_step = evaluate_step(auto_tune["samples"], auto_tune["step_target"])
            rejected_step["rejected"] = True
            rejected_step["reject_reason"] = abort_reason
            result = evaluate_candidate(candidate, auto_tune["step_results"] + [rejected_step])
            result["rejected"] = True
            result["reject_reason"] = abort_reason
            auto_tune["results"].append(result)
            auto_tune["best"] = best_valid_result()

            next_index = auto_tune["candidate_index"] + 1
            call_mcu_quiet("set_target_angle", auto_tune["baseline"])
            if next_index >= len(auto_tune["candidates"]):
                if not maybe_start_next_stage():
                    return
            else:
                start_candidate(next_index)
            return

        if elapsed >= AUTO_TUNE_STEP_SEC:
            candidate = auto_tune["candidates"][auto_tune["candidate_index"]]
            step_result = evaluate_step(auto_tune["samples"], auto_tune["step_target"])
            auto_tune["step_results"].append(step_result)

            if auto_tune["step_index"] < AUTO_TUNE_STEP_TOTAL - 1:
                auto_tune["step_index"] += 1
                auto_tune["phase"] = "settle"
                auto_tune["phase_started_at"] = now
                auto_tune["samples"] = []
                call_mcu_quiet("set_target_angle", auto_tune["baseline"])
                send_auto_tune_update()
                return

            result = evaluate_candidate(candidate, auto_tune["step_results"])
            auto_tune["results"].append(result)
            auto_tune["best"] = best_valid_result()

            next_index = auto_tune["candidate_index"] + 1
            if next_index >= len(auto_tune["candidates"]):
                if not maybe_start_next_stage():
                    if auto_tune["active"]:
                        finish_auto_tune(apply_best=True, reason="done")
                        ui.send_message("status", message={"ok": True, "message": "Auto Tune finished and recommended gains were applied."})
            else:
                start_candidate(next_index)


ui.on_message("set_target_angle", handle_set_target)
ui.on_message("set_voltage_limit", handle_set_voltage_limit)
ui.on_message("set_velocity_limit", handle_set_velocity_limit)
ui.on_message("set_angle_p", handle_set_angle_p)
ui.on_message("set_velocity_p", handle_set_velocity_p)
ui.on_message("set_velocity_i", handle_set_velocity_i)
ui.on_message("set_velocity_d", handle_set_velocity_d)
ui.on_message("hold_current_angle", handle_hold)
ui.on_message("set_motor_enabled", handle_set_enabled)
ui.on_message("autotune_start", handle_auto_tune_start)
ui.on_message("autotune_stop", handle_auto_tune_stop)
ui.on_message("autotune_apply", handle_apply_auto_tune)


def loop():
    """Poll MCU telemetry and forward it to the Web UI."""
    global last_telemetry

    try:
        raw = Bridge.call("get_telemetry")
        telemetry = parse_telemetry(raw)
        last_telemetry = telemetry
        ui.send_message("telemetry", message=telemetry)
        advance_auto_tune(telemetry)
    except Exception as exc:
        ui.send_message("status", message={"ok": False, "message": f"telemetry failed: {exc}"})

    time.sleep(TELEMETRY_INTERVAL_SEC)


App.run(user_loop=loop)
