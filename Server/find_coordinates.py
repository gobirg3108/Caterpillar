
import pyautogui
import time

print("=" * 50)
print("  BUTTON COORDINATE FINDER")
print("=" * 50)

print("Ctrl+C → Stop")

try:
    while True:
        x, y = pyautogui.position()
        print(f"  Mouse Position → X: {x:4d}  Y: {y:4d}", end="\r")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\n Done! இந்த coordinates-ஐ auto_click.py-ல் வையுங்க.")
    