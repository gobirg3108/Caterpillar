import React, { useState, useCallback } from "react";

const API_BASE = "http://localhost:5000";

const sendCommand = async (endpoint, body = null) => {
  const res = await fetch(`${API_BASE}/${endpoint}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

const BUTTONS_TOP = [
  { label: "MEMORY", color: "green", endpoint: "memory" },
  { label: "EDIT", color: "yellow", endpoint: "edit" },
  { label: "MDI", color: "yellow", endpoint: "mdi" },
  { label: "OPTIONAL STOP", color: "yellow", endpoint: "optional-stop" },
  { label: "SINGLE BLOCK", color: "yellow", endpoint: "single-block" },
  { label: "FEED HOLD", color: "red", endpoint: "feed-hold" },
];

const BUTTONS_BOTTOM = [
  { label: "TABLE STOP", color: "red", endpoint: "table-stop" },
  { label: "CYCLE START", color: "green", endpoint: "cycle-start" },
  { label: "COOLANT ON", color: "green", endpoint: "coolant" },
  { label: "BLOCK SKIP", color: "yellow", endpoint: "block-skip" },
  { label: "RESET", color: "red", endpoint: "reset" },
  { label: "DOOR I/L", color: "green", endpoint: "door-interlock" },
];

const COLOR_STYLES = {
  green: {
    active: "#22c55e",
    glow: "0 0 18px #22c55e88",
    indicator: "#16a34a",
  },
  yellow: {
    active: "#eab308",
    glow: "0 0 18px #eab30888",
    indicator: "#ca8a04",
  },
  red: { active: "#ef4444", glow: "0 0 18px #ef444488", indicator: "#dc2626" },
};

function CNCButton({ label, color, endpoint }) {
  const [lit, setLit] = useState(false);
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState(false);

  const style = COLOR_STYLES[color];

  const handleClick = useCallback(async () => {
    setLit((v) => !v);
    if (!endpoint) return;
    setBusy(true);
    try {
      await sendCommand(endpoint);
      setFlash(true);
      setTimeout(() => setFlash(false), 600);
    } catch (e) {
      console.error(endpoint, e);
    } finally {
      setBusy(false);
    }
  }, [endpoint]);

  const btnColor = lit ? style.active : "#3f3f46";
  const btnShadow = lit ? style.glow : "none";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
      }}
    >
      <span
        style={{
          color: lit ? "#f4f4f5" : "#71717a",
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.08em",
          textAlign: "center",
          height: 28,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "center",
          lineHeight: 1.2,
          fontFamily: "'Courier New', monospace",
        }}
      >
        {label}
      </span>

      <button
        onClick={handleClick}
        disabled={busy}
        style={{
          width: 60,
          height: 60,
          borderRadius: "50%",
          border: `3px solid ${lit ? style.indicator : "#27272a"}`,
          background: btnColor,
          boxShadow: btnShadow,
          cursor: busy ? "wait" : "pointer",
          transition: "all 0.15s ease",
          transform: flash ? "scale(0.9)" : "scale(1)",
          position: "relative",
          outline: "none",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 4,
            borderRadius: "50%",
            background:
              "linear-gradient(145deg, rgba(255,255,255,0.25) 0%, transparent 60%)",
            pointerEvents: "none",
          }}
        />
      </button>

      <div
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: lit ? style.active : "#3f3f46",
          boxShadow: lit ? style.glow : "none",
          transition: "all 0.2s",
        }}
      />
    </div>
  );
}

function RotaryKnob() {
  const [angle, setAngle] = useState(0);
  const [busy, setBusy] = useState(false);
  const [inputVal, setInputVal] = useState("0");

  const labels = ["0", "30", "60", "90", "120"];
  const min = 0,
    max = 120;

  const handleManualInput = async (e) => {
    if (e.key === "Enter") {
      const val = Math.max(0, Math.min(120, Number(inputVal)));
      setAngle(val);
      setInputVal(String(val));
      setBusy(true);
      try {
        await sendCommand("feed-rate", { value: val });
      } catch (e) {
        console.error("feed-rate", e);
      } finally {
        setBusy(false);
      }
    }
  };

  const rotate = async (delta) => {
    const newAngle = Math.max(min, Math.min(max, angle + delta));
    setAngle(newAngle);
    setInputVal(String(newAngle));
    if (busy) return;
    setBusy(true);
    try {
      await sendCommand("feed-rate", { value: newAngle });
    } catch (e) {
      console.error("feed-rate", e);
    } finally {
      setBusy(false);
    }
  };

  const pct = ((angle - min) / (max - min)) * 100;
  const rotation = ((angle - min) / (max - min)) * 240 - 120;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
      }}
    >
      <span
        style={{
          color: "#71717a",
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: "0.1em",
          fontFamily: "monospace",
        }}
      >
        FEED RATE
      </span>

      <div style={{ position: "relative", width: 112, height: 112 }}>
        <svg
          width={112}
          height={112}
          style={{ position: "absolute", top: 0, left: 0 }}
        >
          <circle
            cx={56}
            cy={56}
            r={52}
            fill="none"
            stroke="#3f3f46"
            strokeWidth={3}
          />
          <circle cx={56} cy={56} r={44} fill="#18181b" />
          {labels.map((l, i) => {
            const a =
              ((i / (labels.length - 1)) * 240 - 120) * (Math.PI / 180) -
              Math.PI / 2;
            const r = 50;
            return (
              <text
                key={l}
                x={56 + r * Math.cos(a)}
                y={56 + r * Math.sin(a) + 3}
                textAnchor="middle"
                fontSize={8}
                fill="#d6d3d3"
                fontFamily="monospace"
              >
                {l}
              </text>
            );
          })}
        </svg>

        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: 72,
            height: 72,
            borderRadius: "50%",
            background: "linear-gradient(135deg, #52525b, #27272a)",
            border: "3px solid #3f3f46",
            transform: `translate(-50%, -50%) rotate(${rotation}deg)`,
            transition: "transform 0.2s ease",
            boxShadow: "0 4px 12px rgba(0,0,0,0.6)",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "center",
            paddingTop: 6,
          }}
        >
          <div
            style={{
              width: 4,
              height: 16,
              background: "#f4f4f5",
              borderRadius: 2,
            }}
          />
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <button onClick={() => rotate(-10)} style={knobBtnStyle}>
          −
        </button>

        <input
          type="number"
          min={0}
          max={120}
          value={inputVal}
          onChange={(e) => {
            const raw = e.target.value;
            if (raw === "" || raw === "-") {
              setInputVal(raw);
              return;
            }
            const num = Number(raw);
            if (!isNaN(num)) {
              setInputVal(String(Math.min(120, Math.max(0, num))));
            }
          }}
          onKeyDown={handleManualInput}
          onBlur={async () => {
            const val = Math.max(0, Math.min(120, Number(inputVal) || 0));
            setAngle(val);
            setInputVal(String(val));
            setBusy(true);
            try {
              await sendCommand("feed-rate", { value: val });
            } catch (e) {
              console.error("feed-rate", e);
            } finally {
              setBusy(false);
            }
          }}
          style={{
            width: 56,
            background: "#18181b",
            border: "1px solid #3f3f46",
            borderRadius: 6,
            color: "#a1a1aa",
            fontSize: 11,
            fontFamily: "monospace",
            textAlign: "center",
            padding: "3px 4px",
            outline: "none",
          }}
        />

        <button onClick={() => rotate(10)} style={knobBtnStyle}>
          +
        </button>
      </div>

      <div
        style={{
          width: 88,
          height: 4,
          background: "#27272a",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: "#22c55e",
            transition: "width 0.2s",
          }}
        />
      </div>
    </div>
  );
}

const knobBtnStyle = {
  width: 28,
  height: 28,
  borderRadius: 6,
  background: "#27272a",
  border: "1px solid #3f3f46",
  color: "#d4d4d8",
  fontSize: 16,
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  lineHeight: 1,
};

function EmergencyStop() {
  const [active, setActive] = useState(false);
  const [busy, setBusy] = useState(false);

  const handleClick = async () => {
    const next = !active;
    setActive(next);
    setBusy(true);
    try {
      await sendCommand("emergency");
    } catch (e) {
      console.error("emergency", e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 10,
      }}
    >
      <span
        style={{
          color: active ? "#ef4444" : "#7f1d1d",
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.15em",
          fontFamily: "monospace",
          animation: active ? "pulse 1s infinite" : "none",
        }}
      >
        E-STOP
      </span>

      <div
        style={{
          width: 96,
          height: 96,
          borderRadius: "50%",
          background: "#1c0a0a",
          border: `6px solid ${active ? "#ef4444" : "#7f1d1d"}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: active
            ? "0 0 40px #ef444499, 0 0 80px #ef444433"
            : "0 0 12px #ef444422",
          transition: "all 0.2s",
        }}
      >
        <button
          onClick={handleClick}
          disabled={busy}
          style={{
            width: 76,
            height: 76,
            borderRadius: "50%",
            background: active ? "#ef4444" : "#991b1b",
            border: "none",
            cursor: busy ? "wait" : "pointer",
            boxShadow: active
              ? "inset 0 -4px 8px rgba(0,0,0,0.4)"
              : "inset 0 4px 8px rgba(0,0,0,0.4)",
            transform: active ? "translateY(2px)" : "translateY(0)",
            transition: "all 0.15s",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 8,
              left: "50%",
              transform: "translateX(-50%)",
              width: "60%",
              height: "40%",
              borderRadius: "50%",
              background: "rgba(255,255,255,0.15)",
              pointerEvents: "none",
            }}
          />
        </button>
      </div>

      <span
        style={{
          color: "#52525b",
          fontSize: 9,
          fontFamily: "monospace",
          letterSpacing: "0.05em",
        }}
      >
        {active ? "TRIGGERED" : "ARMED"}
      </span>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
      `}</style>
    </div>
  );
}

export default function CNCControlPanel() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#09090b",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 32,
        fontFamily: "'Courier New', monospace",
      }}
    >
      <div
        style={{
          background: "#111113",
          border: "2px solid #27272a",
          borderRadius: 20,
          padding: "36px 40px",
          boxShadow:
            "0 32px 64px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.04)",
          position: "relative",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 28,
            borderBottom: "1px solid #1e1e20",
            paddingBottom: 16,
          }}
        >
          <div>
            <div
              style={{ color: "#71717a", fontSize: 9, letterSpacing: "0.2em" }}
            >
              CNC MACHINE
            </div>
            <div
              style={{
                color: "#d4d4d8",
                fontSize: 14,
                fontWeight: 700,
                letterSpacing: "0.1em",
              }}
            >
              CONTROL PANEL
            </div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            {["POWER", "READY", "ALARM"].map((l, i) => (
              <div
                key={l}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 4,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background:
                      i === 0 ? "#22c55e" : i === 1 ? "#22c55e" : "#3f3f46",
                    boxShadow: i < 2 ? "0 0 6px #22c55e" : "none",
                  }}
                />
                <span
                  style={{
                    color: "#52525b",
                    fontSize: 7,
                    letterSpacing: "0.1em",
                  }}
                >
                  {l}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Row */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(6, 1fr)",
            gap: 20,
            marginBottom: 28,
          }}
        >
          {BUTTONS_TOP.map((btn) => (
            <CNCButton key={btn.label} {...btn} />
          ))}
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: "#1e1e20", marginBottom: 28 }} />

        {/* Bottom Section */}
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          <RotaryKnob />

          <div style={{ width: 1, height: 120, background: "#1e1e20" }} />

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(6, 1fr)",
              gap: 20,
              flex: 1,
            }}
          >
            {BUTTONS_BOTTOM.map((btn) => (
              <CNCButton key={btn.label} {...btn} />
            ))}
          </div>

          <div style={{ width: 1, height: 120, background: "#1e1e20" }} />

          <EmergencyStop />
        </div>

        {/* Footer */}
        <div
          style={{
            marginTop: 24,
            borderTop: "1px solid #1e1e20",
            paddingTop: 12,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span
            style={{ color: "#3f3f46", fontSize: 9, letterSpacing: "0.1em" }}
          >
            MODBUS TCP · 127.0.0.1:502
          </span>
          <span
            style={{ color: "#3f3f46", fontSize: 9, letterSpacing: "0.1em" }}
          >
            API · localhost:5000
          </span>
        </div>
      </div>
    </div>
  );
}
