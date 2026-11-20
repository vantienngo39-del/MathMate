#define MyAppName "MathMate"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "vantienngo39-del"
#define MyAppExeName "MathMate.exe"
#define RepoOwner "vantienngo39-del"
#define RepoName "MathMate"
#define AssetZipName "MathMate-win64.zip"

[Setup]
AppId={{8D4F1B2E-7C3A-4E9B-A12F-55C90E4B71A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
AllowNoIcons=yes
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=installer_output
OutputBaseFilename=MathMate_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "vietnamese"; MessagesFile: "..\Vietnamese.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a MathMate icon on the desktop"; GroupDescription: "Biểu tượng bổ sung:"; Flags: checkedonce

[Dirs]
Name: "{app}"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function DownloadAndExtractRelease(): Boolean;
var
  AppDir, TempZip, PsScript, PsCmd: string;
  ResultCode: Integer;
begin
  Result := False;
  AppDir := ExpandConstant('{app}');
  TempZip := ExpandConstant('{tmp}\{#AssetZipName}');

  // Lấy link tải trực tiếp từ GitHub Releases API (ưu tiên bản latest, fallback sang tag v{#MyAppVersion})
  PsScript :=
    '$ErrorActionPreference = "Stop"; ' +
    '[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ' +
    '$headers = @{ "User-Agent" = "MathMate-Setup" }; ' +
    '$releaseUrl = "https://api.github.com/repos/{#RepoOwner}/{#RepoName}/releases/latest"; ' +
    'try { $rel = Invoke-RestMethod -Uri $releaseUrl -Headers $headers } ' +
    'catch { $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/{#RepoOwner}/{#RepoName}/releases/tags/v{#MyAppVersion}" -Headers $headers }; ' +
    '$asset = $rel.assets | Where-Object { $_.name -eq "{#AssetZipName}" } | Select-Object -First 1; ' +
    'if (-not $asset) { throw "File not found {#AssetZipName} trong GitHub Release." }; ' +
    'Invoke-WebRequest -Uri $asset.browser_download_url -OutFile "' + TempZip + '" -Headers $headers; ' +
    'if (Test-Path "' + AppDir + '") { Get-ChildItem -Path "' + AppDir + '" -Force | Remove-Item -Recurse -Force }; ' +
    'New-Item -ItemType Directory -Path "' + AppDir + '" -Force | Out-Null; ' +
    'Expand-Archive -Path "' + TempZip + '" -DestinationPath "' + AppDir + '" -Force';

  WizardForm.StatusLabel.Caption := 'Downloading {#AssetZipName} from GitHub Releases...';
  WizardForm.ProgressGauge.Style := npbstMarquee;
  try
    PsCmd := '-NoProfile -ExecutionPolicy Bypass -Command "' + PsScript + '"';
    if Exec('powershell.exe', PsCmd, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0) then
    begin
      if FileExists(AppDir + '\{#MyAppExeName}') then
        Result := True
      else
        MsgBox('Extraction complete, but the file cannot be found ' + AppDir + '\{#MyAppExeName}.', mbError, MB_OK);
    end
    else
    begin
      MsgBox('Failed to download or extract {#AssetZipName} (error code: ' + IntToStr(ResultCode) + '). Please check your network connection and the GitHub Release.', mbError, MB_OK);
    end;
  finally
    WizardForm.ProgressGauge.Style := npbstNormal;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    if not DownloadAndExtractRelease() then
      Abort;
  end;
end;