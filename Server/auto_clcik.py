import pyautogui
import time
import sys


BUTTONS = [
    # ( X,     Y,    "Button Name"    )
    # --- TOP ROW ---
    ( 1090,  480,  "MEMORY"          ),
    ( 1230,  480,  "EDIT"            ),
    ( 1370,  480,  "MDI"             ),
    ( 1510,  480,  "OPTIONAL STOP"   ),
    ( 1645,  480,  "SINGLE BLOCK"    ),
    ( 1785,  480,  "FEED HOLD"       ),
    # --- BOTTOM ROW ---
    ( 1250,  690,  "TABLE STOP"      ),
    ( 1333,  690,  "CYCLE START"     ),
    ( 1414,  690,  "COOLANT ON"      ),
    ( 1500,  690,  "BLOCK SKIP"      ),
    ( 1580,  690,  "RESET"           ),
    ( 1660,  690,  "DOOR I/L"        ),
    # --- E-STOP ---
    ( 1790,  680,  "E-STOP"          ),
    # --- EXIT ---
    (1772, 23, "EXIT")
]



DELAY_SECONDS  = 5      
MOVE_DURATION  = 0.4    
STARTUP_WAIT   = 5      

pyautogui.FAILSAFE = True  


def countdown(seconds, msg):
    for i in range(seconds, 0, -1):
        print(f"  {msg} {i}...", end="\r")
        time.sleep(1)
    print()

def main():
    print("═" * 55)
    print("═" * 55)
    print(f"  Buttons    : {len(BUTTONS)}")
    print(f"  Delay      : {DELAY_SECONDS} seconds each")
    print(f"  Total time : ~{len(BUTTONS) * DELAY_SECONDS} seconds")

    countdown(STARTUP_WAIT, "🚀 Starting in")

    print("  Click sequence starting...\n")
    print(f"  {'#':<5} {'Button':<20} {'Coords':<18} Status")
    print("  " + "─" * 52)

    for i, (x, y, name) in enumerate(BUTTONS, 1):
        print(f"  [{i:02d}/{len(BUTTONS)}] {name:<20} (X:{x}, Y:{y})  ", end="", flush=True)

        pyautogui.moveTo(x, y, duration=MOVE_DURATION)

        pyautogui.click()

        print(f"✅ Clicked!")

        if i < len(BUTTONS):
            for remaining in range(DELAY_SECONDS, 0, -1):
                print(f"     ⏳ Next click in {remaining}s...", end="\r")
                time.sleep(1)
            print(" " * 30, end="\r")

    print()
    print("═" * 55)
    print("  ✅ AUTO CLICK SEQUENCE COMPLETE!")
    print(f"  Total {len(BUTTONS)} buttons clicked successfully.")
    print("═" * 55)
    print()


if __name__ == "__main__":
    try:
        main()
    except pyautogui.FailSafeException:
        print("\n\n stopped!")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n (Ctrl+C)")
        sys.exit(0)