# MMD Character Importer Build Repo

This repository is the GitHub-uploadable source/build package for MMD Character Importer.
It intentionally excludes large generated outputs and the large Blender fallback zip.

## Fresh Windows Build

1. Install Python 3.12.
2. Create and activate a virtual environment:

`powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
`

3. Install build dependencies:

`powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
`

4. Download required heavyweight build assets:

`powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_build_assets.ps1
`

5. Build the one-file release:

`powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_mmd_character_importer_exe.ps1 -Python .\.venv\Scripts\python.exe
`

The output is written to elease\MMDCharacterImporter.exe.

## Notes

- lender-4.5.10-windows-x64.zip is required by the build script but is excluded from git because it is larger than GitHub's normal file limit.
- external_tools\vtfcmd and the required VC runtime DLLs are included directly because they are needed for icon and VTF generation.
- Garry's Mod is still required on the machine that runs the importer because StudioMDL and gmad are distributed with Garry's Mod.
- The source project updates this folder by running 	ools\sync_github_upload.ps1.

The original project README is copied to docs\MMDCharacterImporter_README.md.