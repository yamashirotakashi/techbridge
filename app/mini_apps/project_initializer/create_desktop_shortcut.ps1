# create_desktop_shortcut.ps1
# PJINIT Desktop Shortcut Creation Script

Write-Host "=== PJINIT Desktop Shortcut Creation ===" -ForegroundColor Green

# Get Desktop Path
$DesktopPath = [Environment]::GetFolderPath("Desktop")
Write-Host "Desktop Path: $DesktopPath" -ForegroundColor Cyan

# Project Directory
$ProjectDir = "C:\Users\tky99\DEV\techbridge\app\mini_apps\project_initializer"
$PythonCommand = "python main.py"

# Shortcut File Path
$ShortcutPath = Join-Path $DesktopPath "PJINIT.lnk"

Write-Host "Creating shortcut..." -ForegroundColor Cyan
Write-Host "Path: $ShortcutPath" -ForegroundColor Yellow

try {
    # Create WScript.Shell object
    $WshShell = New-Object -ComObject WScript.Shell
    
    # Create shortcut object
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    
    # Configure shortcut
    $Shortcut.TargetPath = "cmd.exe"
    $Shortcut.Arguments = "/k cd /d `"$ProjectDir`" && $PythonCommand"
    $Shortcut.WorkingDirectory = $ProjectDir
    $Shortcut.Description = "PJINIT - Project Initializer v1.0"
    $Shortcut.WindowStyle = 1  # Normal window
    
    # Set icon (search for Python icon)
    $PythonExe = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonExe) {
        $Shortcut.IconLocation = $PythonExe.Source + ",0"
    }
    
    # Set hotkey (Ctrl+Alt+P)
    $Shortcut.Hotkey = "CTRL+ALT+P"
    
    # Save shortcut
    $Shortcut.Save()
    
    Write-Host "Shortcut created successfully" -ForegroundColor Green
    Write-Host "File: $ShortcutPath" -ForegroundColor Cyan
    Write-Host "Hotkey: Ctrl+Alt+P" -ForegroundColor Yellow
    Write-Host "Command: cd $ProjectDir then $PythonCommand" -ForegroundColor Cyan
    
    # Test shortcut
    Write-Host "" 
    Write-Host "=== Shortcut Information ===" -ForegroundColor Green
    if (Test-Path $ShortcutPath) {
        $ShortcutInfo = $WshShell.CreateShortcut($ShortcutPath)
        Write-Host "Target: $($ShortcutInfo.TargetPath)" -ForegroundColor White
        Write-Host "Arguments: $($ShortcutInfo.Arguments)" -ForegroundColor White
        Write-Host "Working Directory: $($ShortcutInfo.WorkingDirectory)" -ForegroundColor White
        Write-Host "Hotkey: $($ShortcutInfo.Hotkey)" -ForegroundColor White
        Write-Host "Description: $($ShortcutInfo.Description)" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "=== Usage ===" -ForegroundColor Green
    Write-Host "1. Double-click the PJINIT icon on desktop" -ForegroundColor White
    Write-Host "2. Or press Ctrl+Alt+P to launch" -ForegroundColor White
    Write-Host "3. Command prompt will open and PJINIT will start" -ForegroundColor White
    
} catch {
    Write-Error "Shortcut creation error: $($_.Exception.Message)"
    exit 1
}

Write-Host ""
Write-Host "=== PJINIT Shortcut Creation Complete ===" -ForegroundColor Green