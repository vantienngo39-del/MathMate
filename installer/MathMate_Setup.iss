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
Name: "desktopicon"; Description: "Tạo biểu tượng MathMate trên màn hình nền"; GroupDescription: "Các biểu tượng bổ sung:"; Flags: checkedonce

[Dirs]
Name: "{app}"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Khởi chạy {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function DownloadAndExtractRelease(): Boolean;
var
  AppDir, TempZip, PsFile, PsBody, PsArgs: string;
  ResultCode: Integer;
begin
  Result := False;
  AppDir := ExpandConstant('{app}');
  TempZip := ExpandConstant('{tmp}\{#AssetZipName}');
  PsFile := ExpandConstant('{tmp}\mathmate_install.ps1');

  PsBody :=
    '$ErrorActionPreference = "Stop"' + #13#10 +
    '[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12' + #13#10 +
    '$headers = @{ "User-Agent" = "MathMate-Setup" }' + #13#10 +
    '$rel = Invoke-RestMethod -Uri "https://api.github.com/repos/{#RepoOwner}/{#RepoName}/releases/latest" -Headers $headers' + #13#10 +
    '$asset = $rel.assets | Where-Object { $_.name -eq "{#AssetZipName}" } | Select-Object -First 1' + #13#10 +
    'if (-not $asset) { throw "Khong tim thay {#AssetZipName} trong Release" }' + #13#10 +
    'Invoke-WebRequest -Uri $asset.browser_download_url -OutFile "' + TempZip + '" -Headers $headers' + #13#10 +
    'if (Test-Path "' + AppDir + '") { Get-ChildItem -Path "' + AppDir + '" -Force | Remove-Item -Recurse -Force }' + #13#10 +
    'New-Item -ItemType Directory -Path "' + AppDir + '" -Force | Out-Null' + #13#10 +
    'Expand-Archive -Path "' + TempZip + '" -DestinationPath "' + AppDir + '" -Force';

  if not SaveStringToFile(PsFile, PsBody, False) then
  begin
    MsgBox('Không tạo được file script tạm để tải dữ liệu.', mbError, MB_OK);
    Exit;
  end;

  WizardForm.StatusLabel.Caption := 'Đang tải và giải nén {#AssetZipName}...';
  WizardForm.ProgressGauge.Style := npbstMarquee;
  try
    PsArgs := '-NoProfile -ExecutionPolicy Bypass -File "' + PsFile + '"';
    if Exec('powershell.exe', PsArgs, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0) then
    begin
      if FileExists(AppDir + '\{#MyAppExeName}') then
        Result := True
      else
        MsgBox('Giải nén xong nhưng không tìm thấy ' + AppDir + '\{#MyAppExeName}.', mbError, MB_OK);
    end
    else
    begin
      MsgBox('Tải hoặc giải nén thất bại (mã lỗi: ' + IntToStr(ResultCode) + ').', mbError, MB_OK);
    end;
  finally
    WizardForm.ProgressGauge.Style := npbstNormal;
    DeleteFile(PsFile);
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