<#
.SYNOPSIS
    Builds the "without Blender" MMD Character Importer Windows executable.

.DESCRIPTION
    Thin wrapper around build_mmd_character_importer_exe.ps1 that forces -NoBlender and a distinct
    output name (GmodSimpleMMDCharacterImporter_NoBlender). The resulting binary does NOT bundle the
    ~380 MB Blender zip, so it stays small enough for distribution channels with a tight size cap
    (e.g. the 200 MB L4D2 Workshop limit). On first run the app detects that Blender is not bundled
    and prompts the user to download the official Blender 4.5.10 zip or browse to a local copy
    (with checksum verification). The "with Blender" build is produced by running
    build_mmd_character_importer_exe.ps1 directly with the Blender zip present at the repo root.

.NOTES
    Both binaries share the SAME first-run download/browse logic; the program decides whether to use
    the bundled Blender or prompt by checking whether the zip is bundled (core.blender_is_bundled()).
#>
param(
    [string]$Python = "python",
    [string]$Name = "GmodSimpleMMDCharacterImporter_NoBlender",
    [switch]$UseUPX,
    [switch]$Console,
    [switch]$OneDir
)

$ErrorActionPreference = "Stop"
$MainScript = Join-Path $PSScriptRoot "build_mmd_character_importer_exe.ps1"
if (-not (Test-Path -LiteralPath $MainScript -PathType Leaf)) {
    throw "Cannot find the main build script: $MainScript"
}

# Forward to the main build script with -NoBlender. Splatting only the switches that were set keeps
# their default ($false) semantics intact in the callee.
$forward = @{
    Python    = $Python
    Name      = $Name
    NoBlender = $true
}
if ($UseUPX) { $forward.UseUPX = $true }
if ($Console) { $forward.Console = $true }
if ($OneDir) { $forward.OneDir = $true }

Write-Host "Building the WITHOUT-Blender variant as '$Name' (Blender prompted/downloaded at first run)..."
& $MainScript @forward
