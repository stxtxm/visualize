; Visualisateur Psychédélique - Windows Installer (NSIS)
; Simplified — no Modern UI dependency, works with any NSIS install.
; Build: makensis installer.nsi

Unicode True
RequestExecutionLevel admin

!define PRODUCT_NAME "Visualisateur Psychédélique"
!define PRODUCT_VERSION "0.3.0"
!define PRODUCT_PUBLISHER "stxtxm"
!define PRODUCT_WEB_SITE "https://github.com/stxtxm/visualize"
!define PRODUCT_DIR "$PROGRAMFILES64\${PRODUCT_NAME}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "Visualisateur_Psychedelique_Setup_${PRODUCT_VERSION}.exe"
InstallDir "${PRODUCT_DIR}"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
    SetOutPath "$INSTDIR"

    File /r "dist\Visualisateur_Psychedelique_portable\*.*"
    File /nonfatal "ffmpeg_bin\ffmpeg.exe"
    File /nonfatal "ffmpeg_bin\ffprobe.exe"
    File /nonfatal "ffmpeg_bin\ffplay.exe"

    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\Visualisateur_Psychedelique.exe"
    CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\Visualisateur_Psychedelique.exe"

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
