#define MyAppName "MathMate"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MathMate Solver"
#define MyAppExeName "MathMate.exe"

[Setup]
AppId={{8E6F5B7A-4C2D-4A91-9B10-5F3E2D1A7C44}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

; Chỉ hỏi chọn thư mục cài đặt, bỏ qua trang chọn Start Menu & Tasks phụ
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
DirExistsWarning=auto
AppendDefaultDirName=yes

; Icon cho file Setup.exe và trình gỡ cài đặt (nằm ở thư mục gốc dự án)
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

OutputDir=..\installer_output
OutputBaseFilename=MathMate_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "vietnamese"; MessagesFile: "..\Vietnamese.isl"

[Dirs]
Name: "{app}\data"; Permissions: users-modify

[Icons]
; Tự tạo shortcut trên Desktop và Start Menu, trỏ tới {app}\MathMate.exe
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{commonprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"

[Run]
; Tự mở ứng dụng sau khi cài xong (chỉ chạy nếu MathMate.exe đã tải & giải nén thành công)
Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Description: "Khởi chạy {#MyAppName}"; Flags: nowait postinstall skipifsilent; Check: AppExeExists

[Code]
const
  GITHUB_OWNER = 'vantienngo39-del';
  GITHUB_REPO = 'MathMate';

function AppExeExists: Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\{#MyAppExeName}'));
end;

function DownloadAndInstallFromGitHub(const TargetAppDir: string): Boolean;
var
  ZipPath, ExtractDir, PsCmd: string;
  ErrCode: Integer;
begin
  Result := False;
  ZipPath := ExpandConstant('{tmp}\MathMate-win64-latest.zip');
  ExtractDir := ExpandConstant('{tmp}\mathmate_extracted');

  if FileExists(ZipPath) then
    DeleteFile(ZipPath);
  if DirExists(ExtractDir) then
    DelTree(ExtractDir, True, True, True);

  ForceDirectories(ExtractDir);
  ForceDirectories(TargetAppDir);

  PsCmd :=
    '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "' +
    '$ProgressPreference = ''SilentlyContinue''; ' +
    '$api = ''https://api.github.com/repos/' + GITHUB_OWNER + '/' + GITHUB_REPO + '/releases/latest''; ' +
    '$rel = Invoke-RestMethod -Uri $api -Headers @{''User-Agent''=''MathMate-Setup''} -TimeoutSec 20; ' +
    '$asset = $rel.assets | Where-Object { $_.name -like ''*.zip'' } | Select-Object -First 1; ' +
    'if (-not $asset) { exit 2 }; ' +
    'Invoke-WebRequest -Uri $asset.browser_download_url -OutFile ''' + ZipPath + ''' -TimeoutSec 180; ' +
    'Expand-Archive -Path ''' + ZipPath + ''' -DestinationPath ''' + ExtractDir + ''' -Force; ' +
    '$src = ''' + ExtractDir + '''; ' +
    '$dirs = Get-ChildItem -Path $src -Directory; ' +
    'if ($dirs.Count -eq 1 -and -not (Test-Path (Join-Path $src ''{#MyAppExeName}''))) { $src = $dirs[0].FullName }; ' +
    'Get-ChildItem -Path $src -Force | Where-Object { $_.Name -ne ''data'' } | ForEach-Object { Copy-Item -Path $_.FullName -Destination ''' + TargetAppDir + ''' -Recurse -Force }; ' +
    'exit 0"';

  if Exec('powershell.exe', PsCmd, '', SW_HIDE, ewWaitUntilTerminated, ErrCode) then
  begin
    if (ErrCode = 0) and FileExists(TargetAppDir + '\{#MyAppExeName}') then
      Result := True;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Ok: Boolean;
begin
  if CurStep = ssInstall then
  begin
    Ok := DownloadAndInstallFromGitHub(ExpandConstant('{app}'));
    if not Ok then
    begin
      MsgBox(
        'Không thể tải hoặc cài đặt bản mới từ GitHub Releases.' + #13#10 +
        'Hãy kiểm tra mạng Internet và đảm bảo repository đã có Release chứa file .zip.',
        mbError,
        MB_OK
      );
    end;
  end;
end;