const socket = io(`http://${window.location.host}`);

const MAX_POINTS = 240;
const samples = [];
let motorEnabled = true;
let uiSyncActive = false;

const els = {
  connectionStatus: document.getElementById("connectionStatus"),
  statusLog: document.getElementById("statusLog"),
  targetAngle: document.getElementById("targetAngle"),
  targetAngleInput: document.getElementById("targetAngleInput"),
  targetDegreesInput: document.getElementById("targetDegreesInput"),
  targetAngleValue: document.getElementById("targetAngleValue"),
  voltageLimit: document.getElementById("voltageLimit"),
  voltageLimitValue: document.getElementById("voltageLimitValue"),
  velocityLimit: document.getElementById("velocityLimit"),
  velocityLimitValue: document.getElementById("velocityLimitValue"),
  angleP: document.getElementById("angleP"),
  anglePValue: document.getElementById("anglePValue"),
  velocityP: document.getElementById("velocityP"),
  velocityI: document.getElementById("velocityI"),
  velocityD: document.getElementById("velocityD"),
  autoTuneStep: document.getElementById("autoTuneStep"),
  autoTuneVoltage: document.getElementById("autoTuneVoltage"),
  autoTuneMaxVelocity: document.getElementById("autoTuneMaxVelocity"),
  autoTuneD: document.getElementById("autoTuneD"),
  autoTuneVelocityLimit: document.getElementById("autoTuneVelocityLimit"),
  autoTuneVoltageLimit: document.getElementById("autoTuneVoltageLimit"),
  autoTuneStartButton: document.getElementById("autoTuneStartButton"),
  autoTuneStopButton: document.getElementById("autoTuneStopButton"),
  autoTuneApplyButton: document.getElementById("autoTuneApplyButton"),
  autoTuneState: document.getElementById("autoTuneState"),
  autoTuneBest: document.getElementById("autoTuneBest"),
  autoTuneResults: document.getElementById("autoTuneResults"),
  holdButton: document.getElementById("holdButton"),
  zeroButton: document.getElementById("zeroButton"),
  enableButton: document.getElementById("enableButton"),
  clearChartButton: document.getElementById("clearChartButton"),
  chart: document.getElementById("telemetryChart"),
  shaftAngleStat: document.getElementById("shaftAngleStat"),
  targetAngleStat: document.getElementById("targetAngleStat"),
  angleErrorStat: document.getElementById("angleErrorStat"),
  shaftVelocityStat: document.getElementById("shaftVelocityStat"),
  voltageLimitStat: document.getElementById("voltageLimitStat"),
  enabledStat: document.getElementById("enabledStat"),
};

const ctx = els.chart.getContext("2d");

function format(value, digits = 2, unit = "") {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return "--";
  }
  return `${Number(value).toFixed(digits)}${unit}`;
}

function radToDeg(rad) {
  return rad * 180 / Math.PI;
}

function degToRad(deg) {
  return deg * Math.PI / 180;
}

function emitNumber(eventName, value) {
  socket.emit(eventName, Number(value));
}

function setStatus(message, ok = true) {
  els.statusLog.textContent = message;
  els.statusLog.classList.toggle("error", !ok);
}

function bindRange(rangeEl, valueEl, eventName, digits, unit) {
  const send = () => {
    const value = Number(rangeEl.value);
    valueEl.textContent = format(value, digits, unit);
    emitNumber(eventName, value);
  };
  rangeEl.addEventListener("input", send);
}

function syncTargetControls(rad, send = true) {
  const clamped = Math.max(-25, Math.min(25, Number(rad)));
  uiSyncActive = true;
  els.targetAngle.value = String(Math.max(-6.28, Math.min(6.28, clamped)));
  els.targetAngleInput.value = clamped.toFixed(2);
  els.targetDegreesInput.value = radToDeg(clamped).toFixed(0);
  els.targetAngleValue.textContent = format(clamped, 2, " rad");
  uiSyncActive = false;

  if (send) {
    emitNumber("set_target_angle", clamped);
  }
}

els.targetAngle.addEventListener("input", () => syncTargetControls(els.targetAngle.value));
els.targetAngleInput.addEventListener("change", () => syncTargetControls(els.targetAngleInput.value));
els.targetDegreesInput.addEventListener("change", () => syncTargetControls(degToRad(Number(els.targetDegreesInput.value))));

bindRange(els.voltageLimit, els.voltageLimitValue, "set_voltage_limit", 2, " V");
bindRange(els.velocityLimit, els.velocityLimitValue, "set_velocity_limit", 1, " rad/s");
bindRange(els.angleP, els.anglePValue, "set_angle_p", 1, "");

els.velocityP.addEventListener("change", () => emitNumber("set_velocity_p", els.velocityP.value));
els.velocityI.addEventListener("change", () => emitNumber("set_velocity_i", els.velocityI.value));
els.velocityD.addEventListener("change", () => emitNumber("set_velocity_d", els.velocityD.value));

els.holdButton.addEventListener("click", () => socket.emit("hold_current_angle"));
els.zeroButton.addEventListener("click", () => syncTargetControls(0));
els.enableButton.addEventListener("click", () => {
  motorEnabled = !motorEnabled;
  socket.emit("set_motor_enabled", motorEnabled);
  updateEnableButton();
});
els.clearChartButton.addEventListener("click", () => {
  samples.length = 0;
  drawChart();
});
els.autoTuneStartButton.addEventListener("click", () => {
  socket.emit("autotune_start", {
    step_size: Number(els.autoTuneStep.value),
    max_voltage: Number(els.autoTuneVoltage.value),
    max_velocity: Number(els.autoTuneMaxVelocity.value),
    tune_d: els.autoTuneD.checked,
    tune_velocity_limit: els.autoTuneVelocityLimit.checked,
    tune_voltage_limit: els.autoTuneVoltageLimit.checked,
  });
});
els.autoTuneStopButton.addEventListener("click", () => socket.emit("autotune_stop"));
els.autoTuneApplyButton.addEventListener("click", () => socket.emit("autotune_apply"));

function updateEnableButton() {
  els.enableButton.textContent = motorEnabled ? "Disable" : "Enable";
  els.enableButton.classList.toggle("danger", motorEnabled);
  els.enableButton.classList.toggle("primary", !motorEnabled);
}

function updateStats(t) {
  els.shaftAngleStat.textContent = format(t.shaft_angle, 3, " rad");
  els.targetAngleStat.textContent = format(t.target_angle, 3, " rad");
  els.angleErrorStat.textContent = format(t.angle_error, 3, " rad");
  els.shaftVelocityStat.textContent = format(t.shaft_velocity, 2, " rad/s");
  els.voltageLimitStat.textContent = format(t.voltage_limit, 2, " V");
  els.enabledStat.textContent = t.enabled ? "Enabled" : "Disabled";
}

function updateAutoTune(message) {
  const activeText = message.active ? "running" : "idle";
  const total = message.candidate_total || 0;
  const current = total ? Math.min((message.candidate_index || 0) + 1, total) : 0;
  const step = message.step_total ? ` step ${(message.step_index || 0) + 1}/${message.step_total}` : "";
  els.autoTuneState.textContent = `State: ${message.stage || "idle"} / ${message.phase || activeText} (${current}/${total})${step}`;

  if (message.best) {
    els.autoTuneBest.textContent =
      `Best: angle P ${format(message.best.angle_p, 1)}, ` +
      `vel P ${format(message.best.velocity_p, 3)}, ` +
      `vel I ${format(message.best.velocity_i, 3)}, ` +
      `vel D ${format(message.best.velocity_d, 4)}, ` +
      `V ${format(message.best.voltage_limit, 2)}, ` +
      `limit ${format(message.best.velocity_limit, 1)}, ` +
      `score ${format(message.best.score, 3)}`;
  } else {
    els.autoTuneBest.textContent = "No recommendation yet";
  }

  renderAutoTuneResults(message.results || [], message.best);
}

function renderAutoTuneResults(results, best) {
  if (!results.length) {
    els.autoTuneResults.innerHTML = `<tr><td colspan="17">No tests yet</td></tr>`;
    return;
  }

  const bestScore = best ? best.score : Math.min(...results.map((item) => item.score));
  els.autoTuneResults.innerHTML = results.map((result, index) => {
    const isBest = Math.abs(result.score - bestScore) < 0.0001;
    return `
      <tr class="${result.rejected ? "rejected-row" : isBest ? "best-row" : ""}">
        <td>${index + 1}</td>
        <td>${result.stage || "--"}</td>
        <td>${format(result.angle_p, 1)}</td>
        <td>${format(result.velocity_p, 3)}</td>
        <td>${format(result.velocity_i, 3)}</td>
        <td>${format(result.velocity_d, 4)}</td>
        <td>${format(result.voltage_limit, 2)}</td>
        <td>${format(result.velocity_limit, 1)}</td>
        <td>${format(result.settling_time, 3)}s</td>
        <td>${format(result.overshoot, 4)}</td>
        <td>${format(result.steady_error, 4)}</td>
        <td>${format(result.jitter, 4)}</td>
        <td>${format(result.small_final_error, 4)}</td>
        <td>${format(result.small_steady_error, 4)}</td>
        <td>${format(result.small_jitter, 4)}</td>
        <td>${format(result.score, 3)}</td>
        <td>${result.rejected ? result.reject_reason || "rejected" : "ok"}</td>
      </tr>
    `;
  }).join("");
}

function syncControlsFromTelemetry(t) {
  if (document.activeElement && ["INPUT", "BUTTON"].includes(document.activeElement.tagName)) {
    return;
  }
  if (uiSyncActive) {
    return;
  }

  syncTargetControls(t.target_angle, false);
  els.voltageLimit.value = String(t.voltage_limit);
  els.voltageLimitValue.textContent = format(t.voltage_limit, 2, " V");
  els.velocityLimit.value = String(t.velocity_limit);
  els.velocityLimitValue.textContent = format(t.velocity_limit, 1, " rad/s");
  els.angleP.value = String(t.angle_p);
  els.anglePValue.textContent = format(t.angle_p, 1, "");
  els.velocityP.value = String(t.velocity_p);
  els.velocityI.value = String(t.velocity_i);
  els.velocityD.value = String(t.velocity_d);
  motorEnabled = Boolean(t.enabled);
  updateEnableButton();
}

function resizeCanvas() {
  const rect = els.chart.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(320, Math.floor(rect.width));
  const height = Math.max(260, Math.floor(rect.height));
  els.chart.width = Math.floor(width * ratio);
  els.chart.height = Math.floor(height * ratio);
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  drawChart();
}

function drawChart() {
  const rect = els.chart.getBoundingClientRect();
  const width = Math.max(320, rect.width);
  const height = Math.max(260, rect.height);
  const pad = { left: 58, right: 18, top: 18, bottom: 34 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  const values = samples.flatMap((s) => [s.target_angle, s.shaft_angle, s.angle_error]);
  let minY = values.length ? Math.min(...values) : -1;
  let maxY = values.length ? Math.max(...values) : 1;
  if (Math.abs(maxY - minY) < 0.2) {
    maxY += 0.1;
    minY -= 0.1;
  }
  const padY = (maxY - minY) * 0.12;
  minY -= padY;
  maxY += padY;

  const xFor = (i) => pad.left + (samples.length <= 1 ? 0 : i / (samples.length - 1) * plotW);
  const yFor = (v) => pad.top + (maxY - v) / (maxY - minY) * plotH;

  ctx.strokeStyle = "#d9e2e2";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i <= 4; i += 1) {
    const y = pad.top + i / 4 * plotH;
    ctx.moveTo(pad.left, y);
    ctx.lineTo(width - pad.right, y);
  }
  ctx.stroke();

  ctx.fillStyle = "#526365";
  ctx.font = "12px system-ui, sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let i = 0; i <= 4; i += 1) {
    const value = maxY - i / 4 * (maxY - minY);
    ctx.fillText(value.toFixed(2), pad.left - 8, pad.top + i / 4 * plotH);
  }
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillText("latest", width - pad.right - 18, height - pad.bottom + 12);

  drawSeries("target_angle", "#008184", 2, false);
  drawSeries("shaft_angle", "#5b4bdb", 2, false);
  drawSeries("angle_error", "#c44b4b", 1.5, true);

  function drawSeries(key, color, lineWidth, dashed) {
    if (samples.length < 2) {
      return;
    }
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    if (dashed) {
      ctx.setLineDash([6, 5]);
    }
    ctx.beginPath();
    samples.forEach((sample, index) => {
      const x = xFor(index);
      const y = yFor(sample[key]);
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();
    ctx.restore();
  }
}

socket.on("connect", () => {
  els.connectionStatus.textContent = "Connected";
  els.connectionStatus.classList.add("ok");
  setStatus("Connected. Waiting for MCU telemetry...");
});

socket.on("disconnect", () => {
  els.connectionStatus.textContent = "Disconnected";
  els.connectionStatus.classList.remove("ok");
  setStatus("Web UI disconnected from the app backend.", false);
});

socket.on("status", (message) => {
  setStatus(message.message || "Status update", Boolean(message.ok));
});

socket.on("telemetry", (telemetry) => {
  samples.push(telemetry);
  while (samples.length > MAX_POINTS) {
    samples.shift();
  }
  updateStats(telemetry);
  syncControlsFromTelemetry(telemetry);
  drawChart();
});

socket.on("autotune", (message) => {
  updateAutoTune(message);
});

window.addEventListener("resize", resizeCanvas);
syncTargetControls(0, false);
updateEnableButton();
resizeCanvas();
