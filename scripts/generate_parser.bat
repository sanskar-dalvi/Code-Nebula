@echo off
REM 🚀 ANTLR C# Grammar Parser Generator for Windows

SETLOCAL

REM Check Java version
java -version 2> tmpver.txt
findstr "version \"17" tmpver.txt > nul
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Java 17 not found. Please install Java 17.
    del tmpver.txt
    EXIT /B 1
)
echo ✅ Java 17 found.
del tmpver.txt

SET SCRIPT_DIR=%~dp0
SET ANTLR_JAR=%SCRIPT_DIR%antlr-4.13-complete.jar
SET GRAMMAR_DIR=%SCRIPT_DIR%..\grammar
SET OUTPUT_DIR=%SCRIPT_DIR%..\generated\csharp

IF NOT EXIST %ANTLR_JAR% (
    echo ❌ %ANTLR_JAR% not found.
    echo ➡️  Download from: https://www.antlr.org/download/antlr-4.13-complete.jar
    EXIT /B 1
)

echo 🚀 Generating ANTLR Python3 parser...
IF NOT EXIST %OUTPUT_DIR% mkdir %OUTPUT_DIR%
echo ANTLR_JAR: %ANTLR_JAR%
echo GRAMMAR_DIR: %GRAMMAR_DIR%
echo OUTPUT_DIR: %OUTPUT_DIR%

java -Xmx500M -jar %ANTLR_JAR% ^
    -Dlanguage=Python3 -visitor ^
    -o %OUTPUT_DIR% ^
    %GRAMMAR_DIR%\CSharpLexer.g4 %GRAMMAR_DIR%\CSharpParser.g4

echo 📋 Copying base classes to output directory...
copy /Y %GRAMMAR_DIR%\CSharpLexerBase.py %OUTPUT_DIR%\CSharpLexerBase.py
copy /Y %GRAMMAR_DIR%\CSharpParserBase.py %OUTPUT_DIR%\CSharpParserBase.py

echo 📄 Creating __init__.py files...
echo """Generated parsers package""" > %OUTPUT_DIR%\..\__init__.py
echo """Generated C# parser and lexer modules""" > %OUTPUT_DIR%\__init__.py

echo 🔧 Fixing generated Python code (this -^> self)...
python %SCRIPT_DIR%fix_generated_python.py %OUTPUT_DIR%

echo ✅ Parser generated at %OUTPUT_DIR%
