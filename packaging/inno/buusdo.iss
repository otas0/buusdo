; buusdo Windows installer (GitHub Releases — unsigned by design)
; Build on Windows with Inno Setup 6+:
;   iscc /DMyAppVersion=0.1.0 packaging\inno\buusdo.iss
; Payload must be prepared by scripts/package_windows_inno.sh into dist\payload\

#define MyAppName "buusdo Graphics Enhancement Tool"
#define MyAppDirName "buusdo"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "buusdo Graphics Enhancement Tool"
#define MyAppURL "https://github.com/otas0/buusdo-Graphics-Enhancement-Tool"
#define MyAppExeName "buusdo.exe"

[Setup]
AppId={{A8F3C2E1-9B74-4D2A-8E11-BEEF00D00001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={localappdata}\Programs\{#MyAppDirName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=buusdo-setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\..\buusdo\assets\logo.ico
; No SignTool* keys — unsigned GitHub build on purpose.

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\..\dist\payload\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
