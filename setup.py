from cx_Freeze import setup, Executable

build_exe_options = {"packages": [
    "os", "sys", "logging", "dotenv", "pyodbc", "csv", "datetime", "PyQt5.QtWidgets"]}

setup(
    name="CustomMSSQLQueryApp",
    version="0.1",
    description="Custom MS SQL Query App",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base="Win32GUI")]
)
