' Script para iniciar o Jarvis automaticamente sem mostrar a janela do CMD
' Este arquivo deve ser colocado na pasta de Inicialização do Windows:
' C:\Users\SEU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
' 
' Ele chama o arquivo .bat que ativa o ambiente virtual e executa o Jarvis.

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\Projetos\jarvis\start_jarvis.bat" & Chr(34), 0
Set WshShell = Nothing
