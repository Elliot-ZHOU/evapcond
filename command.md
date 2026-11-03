$p = Join-Path (Get-Location) "packaging\build_windows.bat"
$t = [IO.File]::ReadAllText($p)
$t = $t.Replace("`r`n", "`n").Replace("`n", "`r`n")
[IO.File]::WriteAllText($p, $t)
packaging\build_windows.bat
