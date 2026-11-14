; Compilado por tools/criar_instalador.py, depois do pacote do PyInstaller.
#ifndef AppVersion
  #error Passe a versão pelo comando tools/criar_instalador.py.
#endif
#define ProjectRoot AddBackslash(SourcePath) + ".."
#define AppSource ProjectRoot + "\dist\Grafla"

[Setup]
AppId=ShardGem.Grafla
AppName=Grafla
AppVersion={#AppVersion}
AppPublisher=ShardGem
AppPublisherURL=https://github.com/ShardGem/Grafla
DefaultDirName={localappdata}\Programs\Grafla
DefaultGroupName=Grafla
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir={#ProjectRoot}\dist\installer
OutputBaseFilename=Grafla-{#AppVersion}-Windows-x64-Setup
SetupIconFile={#ProjectRoot}\src\grafla\resources\grafla.ico
UninstallDisplayIcon={app}\Grafla.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
VersionInfoVersion={#AppVersion}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Grafla"; Filename: "{app}\Grafla.exe"; WorkingDir: "{app}"; AppUserModelID: "ShardGem.Grafla"
Name: "{autodesktop}\Grafla"; Filename: "{app}\Grafla.exe"; WorkingDir: "{app}"; AppUserModelID: "ShardGem.Grafla"; Tasks: desktopicon

[Run]
Filename: "{app}\Grafla.exe"; Description: "Abrir o Grafla"; Flags: nowait postinstall skipifsilent
