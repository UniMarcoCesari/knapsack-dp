#!/bin/sh
# Compila il progetto in bin/. Il modulo Gurobi viene incluso solo se
# gurobi.jar è raggiungibile (variabile GUROBI_HOME o jar in lib/).
set -e
cd "$(dirname "$0")"

mkdir -p bin
javac -d bin $(find src -name '*.java')
echo "Core compilato in bin/"

GRB_JAR=""
[ -n "$GUROBI_HOME" ] && [ -f "$GUROBI_HOME/lib/gurobi.jar" ] && GRB_JAR="$GUROBI_HOME/lib/gurobi.jar"
[ -f lib/gurobi.jar ] && GRB_JAR="lib/gurobi.jar"

if [ -n "$GRB_JAR" ]; then
    javac -cp "bin:$GRB_JAR" -d bin $(find gurobi-src -name '*.java')
    echo "Modulo Gurobi compilato (jar: $GRB_JAR)"
else
    echo "Modulo Gurobi saltato (gurobi.jar non trovato: opzionale)"
fi
