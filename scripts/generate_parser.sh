#!/usr/bin/env bash

# 🚀 ANTLR C# Grammar Parser Generator
# Make sure Java 17 and antlr-4.13-complete.jar are installed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANTLR_JAR="$SCRIPT_DIR/antlr-4.13-complete.jar"
GRAMMAR_DIR="$SCRIPT_DIR/../grammar"
OUTPUT_DIR="$SCRIPT_DIR/../generated/csharp"

echo "🔍 Checking Java version..."
java_version=$(java -version 2>&1 | grep 'version "17')
if [ -z "$java_version" ]; then
  echo "❌ Java 17 not found. Please install Java 17."
  exit 1
fi
echo "✅ Java 17 found."

if [ ! -f "$ANTLR_JAR" ]; then
  echo "❌ $ANTLR_JAR not found."
  echo "➡️  Download from: https://www.antlr.org/download/antlr-4.13-complete.jar"
  exit 1
fi

echo "🚀 Generating ANTLR Python3 parser..."
mkdir -p "$OUTPUT_DIR"
echo "ANTLR_JAR: $ANTLR_JAR"
echo "GRAMMAR_DIR: $GRAMMAR_DIR"
echo "OUTPUT_DIR: $OUTPUT_DIR"

java -Xmx500M -cp "$ANTLR_JAR" org.antlr.v4.Tool \
  -Dlanguage=Python3 -visitor \
  -o "$OUTPUT_DIR" \
  "$GRAMMAR_DIR/CSharpLexer.g4" "$GRAMMAR_DIR/CSharpParser.g4"

echo "✅ Parser generated at $OUTPUT_DIR"
