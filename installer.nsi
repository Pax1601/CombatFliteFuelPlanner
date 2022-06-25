# define name of installer
OutFile "767FA18FuelPlanner_installer.exe"
 
# define installation directory
InstallDir "$PROGRAMFILES\767squadron"
 
# For removing Start Menu shortcut in Windows 7
RequestExecutionLevel admin
 
page components
page instfiles
 
Section "Common files"
	CreateDirectory "$INSTDIR"
	SectionIn RO ; Read only, always installed 
	WriteUninstaller "$INSTDIR\uninstall_767FA18FuelPlanner.exe" # Create the uninstaller
SectionEnd

Section "767 squadron F/A-18 Hornet Fuel Planner"
	CreateDirectory "$INSTDIR"
 
    # set the installation directory as the destination for the following actions
    SetOutPath "$INSTDIR"
	# define what to install and place it in the output path
	File /nonfatal /a /r "dist\767FA18FuelPlanner" 
	SetOutPath "$INSTDIR\767FA18FuelPlanner"
	CreateShortcut "$DESKTOP\767 squadron F/A-18 Hornet Fuel Planner.lnk" "$INSTDIR\767FA18FuelPlanner\main.exe" "" "$INSTDIR\767FA18FuelPlanner\icon\icon.ico" 0
	
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\767FA18FuelPlanner" \
                 "DisplayName" "767 squadron F/A-18 Hornet Fuel Planner"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MPIX Labela 767FA18FuelPlanner" \
					 "UninstallString" "$\"$INSTDIR\uninstall_767FA18FuelPlanner.exe$\""
SectionEnd
 
# uninstaller section start
Section "uninstall"
 
    # first, delete the uninstaller
    Delete "$INSTDIR\uninstall_767FA18FuelPlanner.exe"
	
	RMDir /r "$INSTDIR\767FA18FuelPlanner"
 
    # second, remove the link from the start menu
    Delete "$SMPROGRAMS\uninstall_767FA18FuelPlanner.lnk"
	Delete "$DESKTOP\767 squadron F/A-18 Hornet Fuel Planner.lnk.lnk"
	Delete "$DESKTOP\uninstall_767FA18FuelPlanner.lnk" 
	
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\767 squadron F/A-18 Hornet Fuel Planner"
    RMDir $INSTDIR
# uninstaller section end
SectionEnd