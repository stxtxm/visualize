; Visualisateur Psychédélique - Windows Installer (NSIS)
; Build: makensis installer.nsi

Unicode True
RequestExecutionLevel admin

!define PRODUCT_NAME "Visualisateur Psychédélique"
!define PRODUCT_VERSION "0.2.2"
!define PRODUCT_PUBLISHER "stxtxm"
!define PRODUCT_WEB_SITE "https://github.com/stxtxm/visualize"
!define PRODUCT_DIR "$PROGRAMFILES64\${PRODUCT_NAME}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "Visualisateur_Psychedelique_Setup_${PRODUCT_VERSION}.exe"
InstallDir "${PRODUCT_DIR}"
ShowInstDetails show
ShowUnInstDetails show

; Modern UI
!include "MUI2.nsh"
!include "FileFunc.nsh"

; Interface Settings
!define MUI_ABORTWARNING
;!define MUI_ICON "icon.ico"   ; Uncomment when icon.ico exists
;!define MUI_UNICON "icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP ""
!define MUI_WELCOMEFINISHPAGE_BITMAP ""
!define MUI_COMPONENTSPAGE_NODESC

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "French"

Section "Install" SecInstall
    SetOutPath "$INSTDIR"

    ; Copy all portable files
    File /r "dist\Visualisateur_Psychedelique_portable\*.*"

    ; Copy ffmpeg binaries alongside the exe
    File /nonfatal "ffmpeg_bin\ffmpeg.exe"
    File /nonfatal "ffmpeg_bin\ffprobe.exe"
    File /nonfatal "ffmpeg_bin\ffplay.exe"

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\Visualisateur_Psychedelique.exe" "" "$INSTDIR\Visualisateur_Psychedelique.exe" 0
    CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\Visualisateur_Psychedelique.exe" "" "$INSTDIR\Visualisateur_Psychedelique.exe" 0

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry for Add/Remove Programs
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
    ; Remove shortcuts
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
    Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
    RmDir "$SMPROGRAMS\${PRODUCT_NAME}"

    ; Remove app files
    RmDir /r "$INSTDIR"

    ; Remove registry key
    DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
SectionEnd
