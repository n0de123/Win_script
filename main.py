import json
import subprocess
from pathlib import Path

INSTALL_DIR_NAME = "exe for install"
CONFIG_NAME = "config.json"
OUTPUT_PS1_NAME = "install_all.ps1"

DEFAULT_CONFIG = {
    "defaults": {
        "exe_args_try": [
            ["/S"],
            ["/silent"],
            ["/verysilent"],
            ["/quiet"],
            ["/qn"]
        ],
        "msi_args": ["/qn", "/norestart"]
    },
    "rules": [],
    "install_order": []
}


def create_install_dir_and_config(base_dir: Path) -> Path:
    install_dir = base_dir / INSTALL_DIR_NAME
    install_dir.mkdir(parents=True, exist_ok=True)

    cfg_path = base_dir / CONFIG_NAME
    if not cfg_path.exists():
        cfg_path.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2),
            encoding="utf-8"
        )

    return install_dir


def generate_powershell_script(base_dir: Path) -> Path:

    install_dir = base_dir / INSTALL_DIR_NAME
    cfg_path = base_dir / CONFIG_NAME

    if not install_dir.exists():
        raise FileNotFoundError("Install folder not found")

    if not cfg_path.exists():
        raise FileNotFoundError("Config file not found")

    ps1 = f"""
$ErrorActionPreference = 'Stop'

function Is-Admin {{
  $p = New-Object Security.Principal.WindowsPrincipal(
    [Security.Principal.WindowsIdentity]::GetCurrent()
  )
  return $p.IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
  )
}}

function Read-Config($path) {{
  return (Get-Content -Raw $path | ConvertFrom-Json)
}}

function Get-ExeArgs($cfg, $fileName) {{

  foreach ($rule in $cfg.rules) {{

    if ($rule.match.type -eq "exact" -and
        $fileName -ieq $rule.match.value) {{
        return ,$rule.args
    }}

    if ($rule.match.type -eq "contains" -and
        $fileName.ToLower().Contains(
            $rule.match.value.ToLower()
        )) {{
        return ,$rule.args
    }}
  }}

  return $null
}}

function Try-ExeInstall($exe, $attempts) {{

  foreach ($args in $attempts) {{

    try {{

      if ($args.Count -gt 0) {{
        Write-Host "Trying: $($args -join ' ')"
      }}
      else {{
        Write-Host "Trying without arguments" -ForegroundColor Yellow
      }}

      $p = Start-Process `
            -FilePath $exe `
            -ArgumentList $args `
            -Wait `
            -PassThru

      if ($p.ExitCode -eq 0 -or $p.ExitCode -eq 3010) {{
        Write-Host "Success"
        return $true
      }}

      Write-Host "Exit code: $($p.ExitCode)" -ForegroundColor Yellow

    }} catch {{
      Write-Host $_.Exception.Message -ForegroundColor Yellow
    }}
  }}

  return $false
}}


$BaseDir = "{str(base_dir).replace('"','`"')}"
$InstallDir = Join-Path $BaseDir "{INSTALL_DIR_NAME}"
$ConfigPath = Join-Path $BaseDir "{CONFIG_NAME}"


Write-Host "==== Auto Setup Started ===="
Write-Host "Time: $(Get-Date)"
Write-Host ""


if (-not (Is-Admin)) {{
  Write-Host "Not running as Administrator" -ForegroundColor Yellow
}}

$cfg = Read-Config $ConfigPath


$msiFiles = Get-ChildItem $InstallDir -Filter *.msi -File
$exeFiles = Get-ChildItem $InstallDir -Filter *.exe -File


$AllFiles = @()

if ($cfg.install_order.Count -gt 0) {{

  foreach ($name in $cfg.install_order) {{
    $p = Join-Path $InstallDir $name
    if (Test-Path $p) {{
      $AllFiles += Get-Item $p
    }}
  }}

  foreach ($f in ($msiFiles + $exeFiles)) {{
    if ($AllFiles.FullName -notcontains $f.FullName) {{
      $AllFiles += $f
    }}
  }}

}}
else {{
  $AllFiles = ($msiFiles + $exeFiles) | Sort-Object Name
}}


foreach ($file in $AllFiles) {{

  if ($file.Extension -eq ".msi") {{

    Write-Host "Installing MSI: $($file.Name)"

    $args = @("/i", $file.FullName) + $cfg.defaults.msi_args

    $p = Start-Process `
          -FilePath "msiexec.exe" `
          -ArgumentList $args `
          -Wait `
          -PassThru

    Write-Host "Exit code: $($p.ExitCode)"
    Write-Host ""
    continue
  }}


  if ($file.Extension -eq ".exe") {{

    Write-Host "Installing EXE: $($file.Name)"

    $customArgs = Get-ExeArgs $cfg $file.Name

    if ($customArgs) {{

      Write-Host "Using config arguments"

      $p = Start-Process `
            -FilePath $file.FullName `
            -ArgumentList $customArgs `
            -Wait `
            -PassThru

      Write-Host "Exit code: $($p.ExitCode)"
      Write-Host ""
      continue
    }}


    $attempts = @()

    foreach ($a in $cfg.defaults.exe_args_try) {{
      $attempts += ,$a
    }}

    $attempts += ,@()

    $ok = Try-ExeInstall $file.FullName $attempts

    if (-not $ok) {{
      Write-Host "Manual install may be required" -ForegroundColor Yellow
    }}

    Write-Host ""
  }}
}}


Write-Host "==== Setup Finished ===="
Write-Host "Time: $(Get-Date)"
"""

    ps1_path = base_dir / OUTPUT_PS1_NAME
    ps1_path.write_text(ps1.strip() + "\n", encoding="utf-8")
    return ps1_path


def run_powershell(ps1_path: Path):

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(ps1_path)
    ]

    subprocess.run(cmd, check=False)


def menu():

    base_dir = Path.cwd()

    print("=== PC Setup Tool ===")
    print("")
    print("1) Create install folder and config")
    print("2) Generate installer and run it")
    print("3) Exit")
    print("")

    choice = input("Choice: ").strip()


    if choice == "1":

        create_install_dir_and_config(base_dir)

        print("Folder and config created")
        print("Put your installers in 'exe for install'")
        return


    if choice == "2":

        create_install_dir_and_config(base_dir)

        ps1 = generate_powershell_script(base_dir)

        print(f"Script created: {ps1}")

        run = input("Run now? (y/n): ").lower()

        if run in ("y", "yes"):
            run_powershell(ps1)

        return


    if choice == "3":
        return


    print("Invalid choice")



if __name__ == "__main__":
    menu()
