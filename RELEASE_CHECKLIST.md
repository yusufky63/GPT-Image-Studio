# Release Checklist

- [ ] Install dependencies on Windows
- [ ] Run `python -m pytest -q`
- [ ] Launch with `python main.py`
- [ ] Test Generate at a standard resolution
- [ ] Test 3840×2160 generation
- [ ] Test Edit / Reference
- [ ] Test Expand / Outpaint
- [ ] Test Local Resize / Crop
- [ ] Confirm History & Costs persist after restart
- [ ] Confirm API key persists via Windows Credential Manager
- [ ] Run `scripts\build_exe.bat`
- [ ] Launch `dist\GPT-Image-Studio.exe`
- [ ] Test a real API generation from the EXE
- [ ] Publish only after the Windows EXE smoke test passes
