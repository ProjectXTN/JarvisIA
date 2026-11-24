' Abre a API do Jarvis (para o site) sem janela. Para abrir junto com o Windows,
' ponha um atalho deste arquivo em shell:startup (Win+R e digite isso).
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = folder
WshShell.Run Chr(34) & folder & "\start_api.bat" & Chr(34), 0
Set WshShell = Nothing
