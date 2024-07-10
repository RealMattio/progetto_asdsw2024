#!/bin/bash

# Trova tutti i processi che ascoltano su porte di rete
listening_processes=$(lsof -i -n -P | grep LISTEN)

# Se non ci sono processi in ascolto, esce
if [ -z "$listening_processes" ]; then
    echo "Nessun processo in ascolto trovato."
    exit 0
fi

# Estrai i PID dei processi in ascolto
pids=$(echo "$listening_processes" | awk '{print $2}' | sort -u)

# Uccide ogni processo trovato
for pid in $pids; do
    echo "Uccisione del processo PID: $pid"
    kill -9 $pid
done

echo "Tutti i processi in ascolto sono stati uccisi."
