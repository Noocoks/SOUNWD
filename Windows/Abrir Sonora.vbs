Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = "pyw -3"
command = "py -3 --version"
result = shell.Run(command, 0, True)
If result <> 0 Then
  MsgBox "Sonora necesita Python 3.10 o superior." & vbCrLf & vbCrLf & "Pulsa Aceptar para abrir la página oficial e instalarlo. Después vuelve a hacer doble clic aquí.",  vbExclamation, "Sonora · Primer inicio"
  shell.Run "https://www.python.org/downloads/"
  WScript.Quit
End If
shell.CurrentDirectory = root
shell.Run pythonw & " """ & root & "\bootstrap.py""", 0, False
