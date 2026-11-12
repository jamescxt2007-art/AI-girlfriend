# Your local AI companion

A beginner-friendly Streamlit chat app with a dark pink-and-purple theme,
editable name, four personalities, six built-in avatars, conversation starters,
chat downloads, and confirmed clear-chat. The companion is always labelled as AI.

Choose **Demo** for clearly labelled scripted replies, or **Ollama** for real AI
running on this computer. There is no paid API integration and no API key is needed.
Demo mode is selected by default and never contacts Ollama. Failed local AI requests
show an error; the app never silently substitutes scripted replies.

## Recommended model for this computer

Hardware inspected on 11 November 2026:

- Windows 11 Home, 64-bit; Intel Core i5-10300H (4 cores).
- About 8 GB system RAM (7.8 GB usable), with only 0.8 GB free during inspection.
- NVIDIA GeForce GTX 1650 with 4 GB VRAM; driver 610.91.
- About 107 GB free on drive C: before installation.

Start with **`qwen2.5:1.5b`**. The [current official model page](https://ollama.com/library/qwen2.5:1.5b)
lists a 986 MB download. Download size is not runtime memory use. This is a
conservative starting choice for your limited RAM and 4 GB GPU, not a promise of
particular speed. Close unused browser tabs, games, and other apps first.
Small models can repeat themselves, make mistakes, or follow personality instructions
imperfectly. GPU use can be checked with `ollama ps` after a reply.

## 1. Install Ollama (once)

If setup was already completed for you, skip to step 2.

1. Download the installer from [Ollama for Windows](https://ollama.com/download/windows).
2. Open the downloaded installer and follow its installation steps.
3. Open **Ollama** from the Windows Start menu. It runs a local service in the background.
4. Open a **new PowerShell terminal** so it sees the newly installed command.
5. Check:

   ```powershell
   ollama --version
   ```

If `ollama` is not recognized after reopening your terminal, try the full path:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" --version
```

If that works, use the full path in place of `ollama` below until your PATH updates.
The [official Windows guide](https://docs.ollama.com/windows) explains installation,
driver requirements, and model storage. Allow at least 4 GB for Ollama itself,
plus space for models.

For strictly local use, disable Ollama's cloud features. Run this once in PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("OLLAMA_NO_CLOUD", "1", "User")
```

Then quit Ollama using its system-tray menu and reopen it from Start. This setting
applies to the Ollama service, not to Streamlit's `.env` file.
See [Ollama's local-only setting](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features).
The app also rejects cloud-tagged models and remote entries in the model catalogue.

## 2. Download the local model (once)

With Ollama running, enter:

```powershell
ollama pull qwen2.5:1.5b
```

Wait for `success`. Internet is needed to download Ollama and the model, but local
chat works without an internet connection after setup. No sign-in, subscription,
or API key is required for this local model.

Check the downloaded model:

```powershell
ollama list
```

Optional terminal chat:

```powershell
ollama run qwen2.5:1.5b
```

Type a message; type `/bye` to leave that terminal chat. You do not need to leave
`ollama run` open for the Streamlit app; the Ollama background service is what matters.

## 3. Prepare the Python app

In VS Code choose **Terminal → New Terminal**, then:

```powershell
cd C:\coding_projects\AI_girlfriend
python --version
```

Use Python 3.11 or newer. If Python is missing, install it from
https://www.python.org/downloads/ and select **Add Python to PATH**.
Reopen the terminal after installation. If only `py` works, use it instead of
`python` when creating the environment.

If `.venv` does not exist yet, create it:

```powershell
python -m venv .venv
```

Install/update this app's packages:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No environment activation is necessary; this avoids PowerShell script-policy errors.
An old environment may still contain the OpenAI package from an earlier version;
this app no longer imports or calls it.

## 4. Start or restart the app

If Streamlit is already running in your terminal, press **Ctrl+C** first. Then:

```powershell
cd C:\coding_projects\AI_girlfriend
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Keep the terminal open. Open **http://localhost:8501** in your browser.
If that port is occupied by an old instance, append `--server.port 8502` and visit
http://localhost:8502 instead. Refresh the browser after restarting.

1. Demo mode starts automatically in a new session. Try `hello` to check the interface.
2. In **Settings → Connection & model**, select **Ollama — local AI (free, no API key)**.
3. Leave the model name as **`qwen2.5:1.5b`**.
4. Look for **Ollama connected** and **Active model: qwen2.5:1.5b**.
   Ready means installed and available to load, not necessarily already in GPU memory.
5. Type a message or click a conversation starter. A spinner appears during generation.
   The first reply may take longer while the model loads; requests allow up to 180 seconds.

The endpoint is fixed to **http://localhost:11434**. It is your local Ollama server,
not a hosted API. You do not need to open ports, change CORS settings, or expose
Ollama to your network. The app's HTTP client ignores proxy environment variables
for this local connection and does not follow redirects.

## Personalize and save your conversation

- Change the name, personality, or chat icon in **Settings → Personalize**. Names and personalities
  are included in the system instruction for every AI request. Presets are Cheerful,
  Thoughtful, Playful, and Supportive. The bio reflects the preset.
- On mobile, open the sidebar with the arrow at the top left.
- **Download conversation** saves the current chat as a plain-text file.
- **Clear chat** asks for confirmation; choose **Yes, clear** or **Cancel**.
- Switching demo/local modes starts a fresh chat. Download first if you want a copy.
- Changing the local model keeps the current local chat. Future replies use the new model.

History exists only during the browser session; refreshes may reset it. The app does
not automatically save chat files. Keep downloaded conversations private.
For local model context, each request includes the system instruction and up to the
12 latest messages, bounded to about 6,000 characters, always including the new message.
Ollama uses a 4,096-token context and up to 300 output tokens to limit memory use.
Older messages stay visible but may no longer influence replies. The model is kept
loaded for about two minutes after a reply, then can be unloaded by Ollama.

## Change the default model (optional)

The simplest way is to edit **Ollama model** in the sidebar. Use an exact installed
name from `ollama list`. The app does not download models automatically.

To save a default, copy `.env.example` to `.env` only if `.env` does not already exist:

```powershell
Copy-Item .env.example .env
```

Set `OLLAMA_MODEL=qwen2.5:1.5b` (or another installed local chat model) in `.env`
and restart Streamlit. Existing system environment values take precedence.
No secrets are needed. `.gitignore` still excludes `.env`, virtual environments,
Python caches, and Streamlit secrets. Never commit any old API keys.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Cannot connect to Ollama | Open Ollama from Start. Click **Refresh connection** in the app. |
| Ollama still does not respond | Run `ollama serve` in a separate PowerShell terminal and leave it open. |
| `ollama serve` says port is already in use | Ollama is probably already running; do not start a second instance. Try Refresh connection. |
| Model is not installed | Run `ollama pull qwen2.5:1.5b`, wait for success, then refresh. Match the sidebar name exactly. |
| Model missing after changing its name | Check `ollama list`, then enter an installed name or download that local model. |
| First reply is slow or times out | Close unused apps and retry after model loading. Run `ollama ps` to check CPU/GPU use. |
| Low memory or Ollama cannot complete a request | Close other apps. `ollama stop qwen2.5:1.5b` unloads this model; retry when memory is available. |
| No reply text | Retry or use a different local chat model; no demo reply will be inserted. |
| ModuleNotFoundError | Repeat the package-install command and use the exact `.venv` launch command. |

Errors do not add the failed turn to session history. Once ready, submit the message
again. Demo mode is available only when you deliberately select it.

## Project files and checks

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit app entry point |
| `companion_logic.py` | Demo replies, companion instructions, expression selection |
| `companion_ui.py` | Portrait layout, settings, chat display, expression transitions |
| `extract_portraits.py` | Recreates aligned expression PNGs from the preserved reference sheet |
| `ollama_local.py` | Local-only Ollama HTTP client, model validation, helpful errors |
| `style.css` | Profile and chat styling, mobile spacing |
| `.streamlit/config.toml` | Dark theme and disabled Streamlit usage statistics |
| `requirements.txt` | Streamlit, requests, python-dotenv |
| `.env.example` | Optional default model setting, no key |
| `.gitignore` | Excludes secrets and generated files |
| `test_app.py` | Offline UI and client regression tests |

Run the offline checks after installing packages:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

These tests simulate Ollama responses and never contact a paid service.
The integration uses Ollama's official [chat endpoint](https://docs.ollama.com/api/chat)
and [installed-models endpoint](https://docs.ollama.com/api/tags).

## Animated portrait

The default **Character view** is now **Full body**, using a head-to-toe cutout
from the original reference sheet. It uses a taller, larger character panel on
desktop and stays above the chat on mobile. In **Settings → Personalize**, choose
**Portrait** to return to the close-up with blinking and expression changes.
The full-body artwork has the reference sheet's fixed pose; it does not change its
face or simulate talking. The original reference image remains unchanged.

A prominent **Mika is typing…** status with animated dots appears while a reply
is being generated (using your configured name). Demo mode has a brief 0.7-second
pause so you can see it; real model replies have no added delay. The status clears
on success or error, and reduced-motion preferences disable the moving dots.

New sessions default to **Mika**. The heading, message sender, browser title, and
typing indicator follow your configured name. Existing session names and chat history
are preserved. The virtual AI character disclosure is in **Settings → About**;
connection, provider, and model details are in **Settings → Connection & model**.

The portrait appears beside the chat on desktop, and above it on narrow screens.
It moves gently as a whole. An optional brief blink uses a separate closed-eye
artwork frame every few seconds while happy; it never stretches the face.
Disable it with **Settings → Personalize → Blink occasionally**.
Your system/browser **Reduce motion** preference disables idle movement, blinking, and fades.
Use the **Happy**, **Thoughtful**, and **Playful** buttons in **Settings → Personalize**
to preview expressions without changing your chat. While a reply is generated,
the portrait becomes thoughtful and the status says **Mika is typing…** (or your
chosen name). Successful Playful-preset replies can use the playful expression;
other replies and errors return to happy. This is simple styling, not emotion detection.

Message bubbles no longer repeat the old `[Scripted demo reply]` prefix. Demo mode
is still labelled above the chat and in settings. The character remains honestly
identified as virtual AI in About. The artwork is animated 2D, not a 3D model;
true 3D would require a separate rigged character asset and a 3D renderer.

The three portraits in `assets/character/` have matching transparent 420 × 420
canvases and share a head-top alignment and shoulder baseline. They were extracted
from `mika-reference.png`, which is preserved unchanged. No image service or paid
API was used. See `assets/character/README.md` for details and recreation instructions.
They are already prepared; you do not need to crop anything yourself.

After this update, restart Streamlit using step 4 above and refresh the browser.
If dependencies need updating, run the package-install command in step 3 first.
Pillow is included for the image-extraction script; your existing Ollama model and
connection have not been replaced or reconfigured. A restart or browser refresh
can reset session-only history, so download your conversation first if you want a copy.
