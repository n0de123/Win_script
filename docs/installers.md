# Common Silent Install Switches

This file lists known silent install parameters.

## MSI (Windows Installer)
Always works:

msiexec /i file.msi /qn /norestart

## NSIS Installers
Usually:

/S

## Inno Setup

/VERYSILENT /SUPPRESSMSGBOXES /NORESTART

or

/S

## InstallShield

/quiet /s

## Chrome

/silent /install

## 7-Zip

/S

## VLC

/S

## Visual C++ Redistributable

/quiet /norestart

## .NET Runtime

/quiet /norestart
