import os
import time
import threading
import subprocess
import webview
import speech_recognition as sr
import sounddevice as sd
import numpy as np
from datetime import datetime
import urllib.parse
import requests
import json
import psutil
import pyautogui
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(SCRIPT_DIR, "jarvis_holographic_dashboard_hey_jarvis.html")
NOTES_FILE = os.path.join(SCRIPT_DIR, "jarvis_notes.txt")

active_window = None
wake_word_enabled = False
wake_word_lock = threading.Lock()
_last_cpu_temp_check = 0.0
_cached_cpu_temp = None

# Windows background window hiding flag
NO_WINDOW = 0x08000000 if os.name == 'nt' else 0

# ==========================================
# STRICT SYSTEM APPLICATION & SITE DIRECTORY
# ==========================================
APPS_MAP = {
    "notepad": "start notepad",
    "calculator": "calc",
    "calc": "calc",
    "paint": "mspaint",
    "task manager": "taskmgr",
    "cmd": "start cmd",
    "command prompt": "start cmd",
    "explorer": "start explorer",
    "file manager": "start explorer",
    "settings": "start ms-settings:",
    "microsoft store": "start ms-windows-store:",
    "store": "start ms-windows-store:",
    "chrome": "start chrome",
    "google chrome": "start chrome",
    "edge": "start msedge",
    "microsoft edge": "start msedge",
    "vscode": "code",
    "visual studio code": "code",
    "word": "start winword",
    "excel": "start excel",
    "powerpoint": "start powerpnt",
    "vlc": "start vlc",
    "spotify": "start spotify"
}

WEBSITES_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.in",
    "stack overflow": "https://stackoverflow.com",
    "gmail": "https://mail.google.com"
}

# ==========================================
# HELPER: SPEECH & LOGGING (Hidden Window)
# ==========================================
def speak_and_log(text):
    global active_window
    message = str(text)
    print(f"J.A.R.V.I.S.: {message}", flush=True)
    
    if active_window:
        try:
            safe_msg = message.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
            active_window.evaluate_js(f"appendLog('JARVIS', '{safe_msg}');")
        except Exception:
            pass
            
    def _speak_async():
        try:
            spoken_text = message
            safe_message = spoken_text.replace("'", "''").replace('"', '')
            ps_command = (
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$synth.Speak('{safe_message}');"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=NO_WINDOW
            )
        except Exception as error:
            print(f"[VOICE ERROR] {error}", flush=True)

    threading.Thread(target=_speak_async, daemon=True).start()

# ==========================================
# FEATURE 1: WEB SEARCH CAPABILITY
# ==========================================
def web_search(query):
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = soup.find_all('a', class_='result__snippet', limit=3)
        snippets = [r.text.strip() for r in results]
        if snippets:
            return " ".join(snippets[:2])
    except Exception as e:
        print(f"[SEARCH ERROR]: {e}")
    return None

# ==========================================
# DUAL-CORE NEURAL ROUTER
# ==========================================
def ask_local_ai(prompt):
    url = "http://localhost:11434/api/generate"
    
    code_keywords = ["code", "python", "script", "function", "debug", "math", "logic", "algorithm", "json", "fix error"]
    
    if any(keyword in prompt.lower() for keyword in code_keywords):
        selected_model = "mistral"
        system_instruction = (
            "You are J.A.R.V.I.S. Core 02 (Logic & Code Specialist). "
            "Provide concise, accurate responses. Address the user as 'sir'."
        )
    else:
        selected_model = "llama3"
        system_instruction = (
            "You are J.A.R.V.I.S., tactical AI built for Mayank Singh. "
            "Give direct, accurate, and professional responses. Address him as 'sir'."
        )

    payload = {
        "model": selected_model,
        "prompt": f"{system_instruction}\n\nQuery: {prompt}",
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=45)
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            return result if result else "Neural core returned an empty response, sir."
        else:
            return f"Ollama engine error ({response.status_code}), sir."
            
    except requests.exceptions.ConnectionError:
        return "Local AI server is offline, sir. Please run Ollama."
    except requests.exceptions.Timeout:
        return "Model loading timed out, sir. Please try again."
    except Exception as e:
        return f"Neural routing failed: {str(e)}"

# ==========================================
# INTELLIGENT HYBRID EXECUTION MATRIX
# ==========================================
def execute_system_command(command_text):
    cmd = command_text.lower().strip()
    print(f"[EXECUTING COMMAND]: {cmd}", flush=True)

    if "time" in cmd:
        return f"The current time is {datetime.now().strftime('%I:%M %p')}, sir."
    elif "date" in cmd:
        return f"Today's date is {datetime.now().strftime('%A, %B %d, %Y')}, sir."
    elif "battery" in cmd or "power status" in cmd:
        battery = psutil.sensors_battery()
        if battery:
            plugged = "Plugged in" if battery.power_plugged else "Unplugged"
            return f"Battery is at {battery.percent} percent, {plugged}, sir."
        return "Battery telemetry unavailable on this system, sir."

    elif "volume up" in cmd:
        pyautogui.press("volumeup", presses=5)
        return "Increasing volume, sir."
    elif "volume down" in cmd:
        pyautogui.press("volumedown", presses=5)
        return "Decreasing volume, sir."
    elif "mute" in cmd or "unmute" in cmd:
        pyautogui.press("volumemute")
        return "Toggling volume mute, sir."
    elif "screenshot" in cmd or "take screenshot" in cmd:
        shot_path = os.path.join(os.path.expanduser("~"), "Pictures", f"JARVIS_Shot_{int(time.time())}.png")
        pyautogui.screenshot(shot_path)
        return f"Screenshot captured and saved to Pictures, sir."

    elif "note " in cmd or "take a note" in cmd:
        note_text = cmd.replace("take a note", "").replace("note", "").strip()
        if note_text:
            with open(NOTES_FILE, "a") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note_text}\n")
            return f"Note saved, sir: '{note_text}'"
        return "Please specify what you'd like me to note down, sir."
    elif "show notes" in cmd or "read notes" in cmd:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r") as f:
                notes = f.readlines()
            return f"You have {len(notes)} notes saved, sir. Latest: {notes[-1].strip() if notes else 'None'}"
        return "No saved notes found, sir."

    elif any(word in cmd for word in ["exit", "shutdown", "stop assistant", "turn off"]):
        speak_and_log("Shutting down tactical interface, sir.")
        time.sleep(1)
        os._exit(0)

    elif cmd.startswith("search ") or "search web for" in cmd or "google search" in cmd:
        search_query = cmd.replace("search web for", "").replace("google search", "").replace("search", "").strip()
        speak_and_log(f"Searching web frequencies for: {search_query}...")
        web_res = web_search(search_query)
        if web_res:
            return ask_local_ai(f"Summarize this search result for the query '{search_query}' concisely: {web_res}")
        return "Unable to fetch live search results at this moment, sir."

    words = cmd.split()
    for app_name, app_cmd in APPS_MAP.items():
        if app_name in words or app_name in cmd:
            try:
                os.system(app_cmd)
                return f"Launching {app_name.capitalize()}, sir."
            except Exception as e:
                return f"Failed to launch {app_name}, sir."

    for site_name, site_url in WEBSITES_MAP.items():
        if cmd == site_name or cmd == f"open {site_name}" or cmd == f"launch {site_name}":
            os.system(f"start {site_url}")
            return f"Opening {site_name.capitalize()}, sir."

    if cmd.startswith("open "):
        target = cmd.replace("open ", "").strip()
        target_url = f"https://www.{target}.com" if "." not in target else f"https://{target}"
        os.system(f"start {target_url}")
        return f"Opening {target}, sir."

    return ask_local_ai(command_text)

# ==========================================
# PYTHON-TO-JS BRIDGE & TELEMETRY THREAD
# ==========================================
class JarvisAPI:
    def set_wake_word_enabled(self, enabled):
        global wake_word_enabled
        with wake_word_lock:
            wake_word_enabled = bool(enabled)
        if active_window:
            try:
                active_window.evaluate_js(f"updateWakeWordStatus({str(bool(enabled)).lower()});")
            except Exception:
                pass
        print(f"[WAKE WORD] {'ARMED' if enabled else 'DISARMED'} — phrase: hey jarvis", flush=True)
        return {"ok": True, "enabled": bool(enabled)}

    def handle_chat_input(self, text):
        print(f"\n[TEXT CHAT] User: {text}", flush=True)
        response_msg = execute_system_command(text)
        speak_and_log(response_msg)

    def trigger_push_to_talk(self):
        print(f"\n[PTT ACTIVATED] Listening for voice command...", flush=True)
        threading.Thread(target=self._listen_ptt_command, daemon=True).start()

    def _listen_ptt_command(self):
        global active_window
        try:
            recognizer = sr.Recognizer()
            sample_rate = 16000
            audio_data = sd.rec(int(6 * sample_rate), samplerate=sample_rate, channels=1, dtype='int16', device=None)
            sd.wait()
            audio_data = audio_data.flatten()
            audio = sr.AudioData(audio_data.tobytes(), sample_rate, 2)
            command = recognizer.recognize_google(audio, language="en-IN").strip().lower()
            
            print(f"PTT Heard: {command}")
            if active_window:
                active_window.evaluate_js(f"appendLog('USER', '{command}');")

            response_msg = execute_system_command(command)
            speak_and_log(response_msg)

        except Exception as e:
            print(f"[PTT ERROR]: {e}")
            speak_and_log("I couldn't catch that frequency, sir. Please try again.")
        finally:
            if active_window:
                try:
                    active_window.evaluate_js("resetPTTButton();")
                except:
                    pass

def get_nvidia_telemetry():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2, check=True,
            creationflags=NO_WINDOW
        )
        first_line = result.stdout.strip().splitlines()[0]
        values = [v.strip() for v in first_line.split(",")]
        return float(values[0]), float(values[1])
    except Exception:
        return None, None

def get_cpu_temperature():
    global _last_cpu_temp_check, _cached_cpu_temp
    now = time.time()
    if now - _last_cpu_temp_check < 15:
        return _cached_cpu_temp
    _last_cpu_temp_check = now
    try:
        ps_lhm = r"$s=Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor -ErrorAction Stop | Where-Object {$_.SensorType -eq 'Temperature' -and $_.Name -match 'CPU Package|CPU Die|Tctl/Tdie|Core #0'} | Select-Object -First 1; if($s){[math]::Round($s.Value,1)}"
        result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_lhm], capture_output=True, text=True, timeout=4, creationflags=NO_WINDOW)
        value = result.stdout.strip()
        if value:
            _cached_cpu_temp = float(value)
        else:
            ps_acpi = r"$z=Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop | Select-Object -First 1; if($z){[math]::Round(($z.CurrentTemperature/10)-273.15,1)}"
            result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_acpi], capture_output=True, text=True, timeout=4, creationflags=NO_WINDOW)
            value = result.stdout.strip()
            _cached_cpu_temp = float(value) if value else None
    except Exception:
        _cached_cpu_temp = None
    return _cached_cpu_temp

def update_telemetry_loop():
    time.sleep(6)
    while True:
        try:
            if active_window:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                gpu, gpu_temp = get_nvidia_telemetry()
                cpu_temp = get_cpu_temperature()
                def jsnum(value):
                    return "null" if value is None else str(round(float(value), 1))
                js_code = f"if (typeof updateTelemetry === 'function') {{ updateTelemetry({cpu}, {ram}, {jsnum(gpu)}, {jsnum(gpu_temp)}, {jsnum(cpu_temp)}); }}"
                active_window.evaluate_js(js_code)
        except Exception as e:
            print(f"[TELEMETRY WARNING] {e}", flush=True)
        time.sleep(3)

# ==========================================
# SOUNDDEVICE WAKE WORD LOOP
# ==========================================
def voice_loop():
    time.sleep(2)
    speak_and_log("All systems online. Say Hey Jarvis when the wake word is armed.")
    recognizer = sr.Recognizer()
    sample_rate = 16000
    
    while True:
        try:
            with wake_word_lock:
                armed = wake_word_enabled
            if not armed:
                time.sleep(0.5)
                continue
            
            audio_data = sd.rec(int(4 * sample_rate), samplerate=sample_rate, channels=1, dtype='int16', device=None)
            sd.wait()
            audio_data = audio_data.flatten()
            
            if int(np.max(np.abs(audio_data))) < 15:
                continue
                
            audio = sr.AudioData(audio_data.tobytes(), sample_rate, 2)
            speech = recognizer.recognize_google(audio, language="en-IN").strip().lower()
            print(f"[WAKE LISTENER] Heard: {speech}", flush=True)
            
            if "hey jarvis" in speech:
                speak_and_log("Yes, sir? I'm listening.")
                if active_window:
                    try:
                        active_window.evaluate_js("setPTTListeningState(); updateWakeWordStatus(true);")
                    except Exception:
                        pass
                
                cmd_audio_data = sd.rec(int(7 * sample_rate), samplerate=sample_rate, channels=1, dtype='int16', device=None)
                sd.wait()
                cmd_audio_data = cmd_audio_data.flatten()
                audio_cmd = sr.AudioData(cmd_audio_data.tobytes(), sample_rate, 2)
                
                command = recognizer.recognize_google(audio_cmd, language="en-IN").strip().lower()
                print(f"[WAKE WORD COMMAND]: {command}", flush=True)
                
                if active_window:
                    safe_cmd = command.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
                    try:
                        active_window.evaluate_js(f"appendLog('USER', '{safe_cmd}'); resetPTTButton();")
                    except Exception:
                        pass
                
                response_msg = execute_system_command(command)
                speak_and_log(response_msg)
                
                if active_window:
                    try:
                        active_window.evaluate_js("updateWakeWordStatus(true);")
                    except Exception:
                        pass
                        
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"[WAKE LISTENER] Speech service unavailable: {e}", flush=True)
            time.sleep(2)
        except Exception as e:
            print(f"[WAKE LISTENER ERROR] {e}", flush=True)
            time.sleep(1)

if __name__ == "__main__":
    api = JarvisAPI()
    
    # Start Voice Loop
    threading.Thread(target=voice_loop, daemon=True).start()
    
    # Start Real Telemetry Loop
    threading.Thread(target=update_telemetry_loop, daemon=True).start()

    active_window = webview.create_window(
        title="J.A.R.V.I.S. - Autonomous Tactical Assistant v4.0",
        url=DASHBOARD_FILE,
        width=1100,
        height=750,
        js_api=api
    )
    webview.start()