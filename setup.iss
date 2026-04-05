; ==============================================================================
; DownloaderPRO - Windows Installer Script (Inno Setup 6)
; ==============================================================================

#define AppName "DownloaderPRO"
#define AppVersion "3.0.0"
#define AppPublisher "double-uRB"
#define AppURL "https://github.com/double-uRB/DownloaderPRO"
#define AppExeName "YouTubeDownloaderPro.exe"
#define AppIcon "assets\logo.ico"

[Setup]
; App Metadata
AppId={{D1A2E3B4-C5D6-E7F8-G9H0-I1J2K3L4M5N6}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Installation Paths
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
DefaultGroupName={#AppName}

; Privileges & Architectures
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Appearance
SetupIconFile={#AppIcon}
Compression=lzma2/solid
SolidCompression=yes
WizardStyle=modern
OutputBaseFilename=DownloaderPRO_Setup_v{#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy all files from PyInstaller --onedir output
Source: "dist\YouTubeDownloaderPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copy the helper script to be used during installation
Source: "download_tools.py"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppIcon}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppIcon}"; Tasks: desktopicon

[Run]
; Launch the app after install (optional)
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\tools"

[Code]
var
  DownloadPage: TOutputProgressWizardPage;
  GPUDetectionPage: TOutputMsgWizardPage;
  DetectedGPU: String;

// Helper to run a command and capture its output
function GetCommandOutput(Executable, Arguments: String): String;
var
  FileName, TmpFile: String;
  ResultCode: Integer;
begin
  FileName := 'cmd.exe';
  TmpFile := ExpandConstant('{tmp}\output.txt');
  Arguments := '/C ' + Executable + ' ' + Arguments + ' > "' + TmpFile + '"';
  
  if ExecShell('open', FileName, Arguments, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    LoadStringFromFile(TmpFile, Result);
    Result := Trim(Result);
  end;
end;

// Initialize the GPU detection
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  DownloadCmd: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Initial call to detect GPU via helper
    Log('Detecting GPU...');
    DetectedGPU := GetCommandOutput('python', ExpandConstant('"{tmp}\download_tools.py" --detect-gpu'));
    Log('GPU Detected: ' + DetectedGPU);

    // Create and Show Progress Page
    DownloadPage := CreateOutputProgressPage('Downloading Required Tools', 
      'Please wait while we download hardware-optimized binaries for your system (' + DetectedGPU + ').');
    DownloadPage.Show;
    
    try
      // In a real Inno script, we would use a library like 'Inno Download Plugin'
      // or parse the stdout of download_tools.py to update the progress bar.
      // Here we will run the Python helper which handles the heavy lifting.
      
      DownloadCmd := ExpandConstant('python "{tmp}\download_tools.py" --download-tools --install-dir "{app}\tools"');
      
      DownloadPage.SetProgress(0, 100);
      DownloadPage.SetText('Downloading FFmpeg, Aria2c, and yt-dlp...', '');
      
      // Execute the helper. Using Exec here. For real progress integration,
      // we would use a custom DLL to read the pipe, but for this implementation
      // we'll run the process and assume internal verification.
      if not Exec('python', ExpandConstant('"{tmp}\download_tools.py" --download-tools --install-dir "{app}\tools"'),
        '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
      begin
        MsgBox('Failed to download required tools. Setup will now abort.', mbError, MB_OK);
        Abort;
      end;
      
      // Register Scheduled Task for yt-dlp
      Exec('schtasks', ExpandConstant('/Create /SC WEEKLY /TN "DownloaderPRO_YTDLP_Update" /TR "\"{app}\tools\yt-dlp.exe\" -U" /F'),
        '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

    finally
      DownloadPage.Hide;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Remove scheduled task
    Exec('schtasks', '/Delete /TN "DownloaderPRO_YTDLP_Update" /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    
    // Optional: Ask user to delete settings
    if MsgBox('Do you want to delete your settings and download history as well?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\DownloaderPRO'), True, True, True);
    end;
  end;
end;
