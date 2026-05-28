import React, { useState } from "react";

const buttonsTop = [
  { label: "MEMORY", color: "green" },
  { label: "EDIT", color: "yellow" },
  { label: "MDI", color: "yellow" },
  { label: "OPTIONAL STOP", color: "yellow" },
  { label: "SINGLE BLOCK", color: "yellow" },
  { label: "FEED HOLD", color: "red" },
];

const buttonsBottom = [
  { label: "TABLE STOP", color: "red" },
  { label: "CYCLE START", color: "green" },
  { label: "COOLANT ON", color: "green" },
  { label: "BLOCK SKIP", color: "yellow" },
  { label: "RESET", color: "red" },
  { label: "DOOR I/L", color: "green" },
];

const getButtonColor = (color, active) => {
  if (!active) return "bg-zinc-700";

  switch (color) {
    case "green":
      return "bg-green-500 shadow-green-400";
    case "yellow":
      return "bg-yellow-400 shadow-yellow-300";
    case "red":
      return "bg-red-500 shadow-red-400";
    default:
      return "bg-zinc-500";
  }
};

const sendCommand = async (endpoint) => {
  try {
    const response = await fetch(`http://localhost:5000/${endpoint}`, {
      method: "POST",
    });

    const data = await response.json();

    console.log(data);
  } catch (error) {
    console.log(error);
  }
};

const CNCButton = ({ label, color }) => {
  const [active, setActive] = useState(true);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="text-white text-xs font-semibold text-center h-8">
        {label}
      </div>

      <button
        onClick={() => {
          setActive(!active);

          if (label === "CYCLE START") {
            sendCommand("cycle-start");
          }

          if (label === "FEED HOLD") {
            sendCommand("feed-hold");
          }

          if (label === "RESET") {
            sendCommand("reset");
          }

          if (label === "COOLANT ON") {
            sendCommand("coolant");
          }
        }}
        className={`
          w-16 h-16 rounded-full border-4 border-zinc-800
          transition-all duration-150
          shadow-lg
          cursor-pointer

          hover:scale-110
          hover:brightness-125
          hover:shadow-2xl

          active:scale-95
          active:translate-y-1

          ${getButtonColor(color, active)}`}
      >
        <div className="w-full h-full rounded-full border border-white/20"></div>
      </button>
    </div>
  );
};

const RotaryKnob = () => {
  const [rotation, setRotation] = useState(0);

  const rotateLeft = () => {
    setRotation((prev) => Math.max(prev - 10, -120));
  };

  const rotateRight = () => {
    setRotation((prev) => Math.min(prev + 10, 120));
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32 flex items-center justify-center">
        {/* Outer Circle */}
        <div className="absolute w-full h-full rounded-full border-4 border-zinc-500"></div>

        {/* Knob */}
        <div
          className="w-20 h-20 bg-zinc-400 rounded-full border-4 border-zinc-700 relative transition-transform duration-200"
          style={{
            transform: `rotate(${rotation}deg)`,
          }}
        >
          <div className="absolute top-1 left-1/2 -translate-x-1/2 w-2 h-8 bg-white rounded"></div>
        </div>
      </div>

      <div className="flex gap-3 mt-4">
        <button
          onClick={rotateLeft}
          className="px-3 py-1 bg-zinc-700 text-white rounded"
        >
          -
        </button>

        <button
          onClick={rotateRight}
          className="px-3 py-1 bg-zinc-700 text-white rounded"
        >
          +
        </button>
      </div>

      <div className="text-white mt-2 text-sm">{rotation}°</div>
    </div>
  );
};

export default function CNCControlPanel() {
  const [emergency, setEmergency] = useState(false);
  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-8">
      <div className="bg-zinc-900 border-4 border-zinc-700 rounded-2xl p-10 shadow-2xl">
        {/* TOP BUTTONS */}
        <div className="grid grid-cols-6 gap-10 mb-12">
          {buttonsTop.map((btn) => (
            <CNCButton key={btn.label} label={btn.label} color={btn.color} />
          ))}
        </div>

        {/* BOTTOM SECTION */}
        <div className="flex items-center gap-10">
          {/* Rotary Knob */}
          <RotaryKnob />

          {/* Bottom Buttons */}
          <div className="grid grid-cols-6 gap-10">
            {buttonsBottom.map((btn) => (
              <CNCButton key={btn.label} label={btn.label} color={btn.color} />
            ))}
          </div>

          {/* Emergency */}
          <div className="flex flex-col items-center ml-10">
            <div
              className={`
      font-bold mb-4 text-2xl tracking-widest
      ${emergency ? "text-red-400 animate-pulse" : "text-red-700"}
    `}
            >
              EMERGENCY
            </div>

            <button
              onClick={() => {
                setEmergency(!emergency);

                sendCommand("emergency");
              }}
              className={`
      w-24 h-24 rounded-full
      border-8 border-red-900
      transition-all duration-200

      ${
        emergency
          ? `
            bg-red-500
            animate-pulse
            shadow-[0_0_60px_rgba(255,0,0,1)]
            scale-110
          `
          : `
            bg-red-700
            shadow-[0_0_20px_rgba(255,0,0,0.5)]
          `
      }

      hover:scale-110
      active:scale-95
    `}
            >
              <div className="w-full h-full rounded-full bg-gradient-to-b from-white/30 to-transparent"></div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
