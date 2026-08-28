; Visualize - Windows Installer (NSIS)
; Simplified — no Modern UI dependency, works with any NSIS install.
; Build: makensis installer.nsi

Unicode True
RequestExecutionLevel admin

!define PRODUCT_NAME "Visualize"
!define PRODUCT_VERSION "0.3.10"
!define PRODUCT_PUBLISHER "stxtxm"
!define PRODUCT_WEB_SITE "https://github.com/stxtxm/visualize"
!define PRODUCT_DIR "$PROGRAMFILES64\${PRODUCT_NAME}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "Visualize_Setup_${PRODUCT_VERSION}.exe"
InstallDir "${PRODUCT_DIR}"

; Installer + uninstaller icons
Icon "assets\icon.ico"
UninstallIcon "assets\icon.ico"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
    SetOutPath "$INSTDIR"

    File /r "dist\Visualize_portable\*.*"
    File /nonfatal "ffmpeg_bin\ffmpeg.exe"
    File /nonfatal "ffmpeg_bin\ffprobe.exe"
    File /nonfatal "ffmpeg_bin\ffplay.exe"

    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\Visualize.exe" "" "$INSTDIR\Visualize.exe" 0
    CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\Visualize.exe" "" "$INSTDIR\Visualize.exe" 0

    WriteUninstaller "$INSTDIR\Uninstall.exe"

    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
    Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
    RmDir "$SMPROGRAMS\${PRODUCT_NAME}"
    RmDir /r "$INSTDIR"
    DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
SectionEnd
