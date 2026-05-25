@echo off
echo === STLink Driver Fix (ST Official -> WinUSB for OpenOCD) ===
echo.
echo This will replace the STLink USB driver with WinUSB.
echo OpenOCD and other open-source tools need this to access STLink.
echo.
echo STM32CubeIDE / STM32CubeProgrammer will still work after this change.
echo.
pause
echo.
"C:\Users\Administrator\Downloads\zadig.exe" -d 0483:3748 -R WinUSB
echo.
echo Done! You can now use STLink with OpenOCD.
echo Press any key to close...
pause >nul
