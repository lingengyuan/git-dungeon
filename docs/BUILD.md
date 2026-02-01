# Git Dungeon Build Instructions

## Quick Build

### Prerequisites

```bash
# Install build dependencies
pip install -e .

# Install PyInstaller (for packaging)
pip install pyinstaller

# Optional: Install UPX for compression
apt-get install upx  # Linux
brew install upx     # macOS
```

### Build Commands

```bash
# Standard build (PyInstaller)
chmod +x scripts/build.sh
./scripts/build.sh pyinstaller

# With UPX compression (smaller size)
./scripts/build.sh pyinstaller yes

# Nuitka build (smaller but slower)
./scripts/build.sh nuitka
```

## Output

```
dist/
├── git-dungeon          # Linux executable (~25-50MB)
├── GitDungeon.exe       # Windows executable
├── src/                 # Source code
├── docs/                # Documentation
└── README.md
```

## Manual Build

```bash
# PyInstaller
pyinstaller --onefile --windowed pyinstaller.spec

# Nuitka (standalone)
python -m nuitka --standalone --onefile src/main_cli.py
```

## Platform-Specific

### Linux → AppImage

```bash
# After building
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage dist git-dungeon.AppImage
```

### macOS → DMG

```bash
# Use create-dmg or similar
brew install create-dmg
create-dmg --volname "Git Dungeon" --window-size 400 300 --icon-size 100 \
    --icon "Git Dungeon" 150 150 --app-drop-link 250 150 \
    dist/ Git\ Dungeon.dmg
```

### Windows → NSIS

```bash
# Use NSIS for installer
makensis installer.nsi
```

## Troubleshooting

### "Module not found" errors

Make sure all dependencies are installed:
```bash
pip install -e .
```

### Large file size

Try UPX compression:
```bash
./scripts/build.sh pyinstaller yes
```

### Slow build

Nuitka builds are slower but produce smaller executables. PyInstaller is faster to build.

## Size Comparison

| Method | Size | Build Time |
|--------|------|------------|
| PyInstaller | ~50MB | Fast |
| PyInstaller + UPX | ~25MB | Fast |
| Nuitka | ~30MB | Slow |
