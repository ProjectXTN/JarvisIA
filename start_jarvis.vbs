' Abre o Jarvis sem mostrar a janela do console.
' Para abrir junto com o Windows, ponha um atalho deste arquivo em:
'   shell:startup   (Win+R e digite isso)
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = folder
WshShell.Run Chr(34) & folder & "\start_jarvis.bat" & Chr(34), 0
Set WshShell = Nothing
