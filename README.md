# GPT Image Studio v1.0.2

Windows-first desktop application for OpenAI GPT Image models.

## Features

- Text-to-image generation
- Direct image reference/editing
- Expand / Outpaint workflow
- Local Resize / Crop / Stretch without API usage
- Landscape, Portrait, Square and Custom orientations
- Aspect-ratio presets: 16:9, 21:9, 3:2, 4:3, 1:1, 3:4, 2:3, 9:16
- Custom `WIDTHxHEIGHT` resolution
- 3840×2160 and 2160×3840 4K presets
- GPT Image 2.5 Sunburst, GPT Image 2.5 Flare, GPT Image 2
- `auto`, `low`, `medium`, `high`, `xhigh`, `max` quality selection with model validation
- PNG / JPEG / WebP
- JPEG/WebP compression control
- Opaque / Transparent / Auto backgrounds
- 0–3 partial generation previews
- Real elapsed-time loading state (no fake percentage)
- Cancel control
- Live operation log
- Local SQLite generation history
- Token usage and calculated API cost when usage is returned
- Windows Credential Manager API-key storage
- Source image drag & drop
- Output metadata and preview
- Configurable output folder (default: Pictures\GPT Image Studio)
- Open Image / Open Folder / Save As buttons
- Save Preview button for the image currently visible in Preview
- Save verification before reporting success
- Windows EXE build script
- Automated tests before EXE build

## Modes

### Generate
Create a new image from a prompt.

### Edit / Reference
Send an existing PNG/JPEG/WebP directly to OpenAI together with an edit instruction. No separate image-analysis pass is required.

### Expand / Outpaint
Send an existing image and request a different target canvas/aspect ratio. GPT Image generates coherent surrounding content instead of simply stretching the source.

### Local Resize / Crop
Runs entirely on the computer with Pillow and does not call OpenAI:
- Fit
- Crop
- Stretch

## Recommended settings

For maximum-quality 4K landscape artwork:

- Model: `gpt-image-2.5-sunburst`
- Quality: `max`
- Orientation: Landscape
- Aspect ratio: 16:9
- Resolution: 3840×2160
- Format: PNG
- Background: Opaque
- Partial previews: 2

Use Flare when generation speed matters more.

## Install from source

Python 3.11+ recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Open **Settings**, enter the OpenAI API key, then save it. The key is stored using Windows Credential Manager rather than in the JSON settings file.

## Build Windows EXE

Run:

```text
scripts\build_exe.bat
```

The script installs dependencies, runs tests, and builds `dist\GPT-Image-Studio.exe` with PyInstaller.

## Local data

Settings/history: `%LOCALAPPDATA%\GPTImageStudio`

Generated images default to: `%USERPROFILE%\Pictures\GPT Image Studio`

## Cost tracking

When OpenAI returns token usage, GPT Image Studio records token usage and calculated USD cost. If usage is unavailable, the application displays `Unavailable` rather than inventing a value.

Pricing constants are isolated in `app/pricing.py`; verify current OpenAI pricing before publishing a release.

## Privacy

Prompts and generation metadata are stored locally in SQLite. Generated files are stored locally. Image generation/editing sends the prompt and any selected source image to the OpenAI API.

## Not included

Mask editing is intentionally not included.

## License

MIT
