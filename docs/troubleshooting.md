# Troubleshooting

## Installer opens GUI instead of silent
The installer probably uses custom arguments.
Find them with:

installer.exe /?
installer.exe --help

Then add them in config.json.

## Permission denied / Access refused
Run the tool as Administrator.

## PyInstaller fails with pathlib error
Run:

python -m pip uninstall pathlib

## Some installers fail
Check install_all.ps1 output for exit codes.

3010 = reboot required (not an error).

## Antivirus blocks exe
Add exception or build locally.
