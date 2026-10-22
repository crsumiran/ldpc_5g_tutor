#!/usr/bin/env bash
# Run every check in the hardware tutorial: Python golden models, RTL lint, RTL simulation.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build

echo "== Python golden models"
(cd model && python3 rotators.py && python3 layered_qc.py)

if command -v verilator >/dev/null; then
    echo "== RTL lint (verilator -Wall)"
    for top in rot_barrel rot_qsn rot_banyan rot_ibn3 rot_5g; do
        # UNOPTFLAT: the stage[] array looks like one looped signal; it is a
        # simulation-speed hint, not a real combinational loop.
        verilator --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL -Wno-UNOPTFLAT \
            -Irtl --top-module "$top" rtl/*.v
        echo "   $top: clean"
    done

    echo "== RTL simulation (verilator, ~2 min to compile the first time)"
    verilator --binary --timing -O3 -j 0 -Wno-fatal -Wno-lint -Wno-style -Wno-UNOPTFLAT \
        -Irtl --top-module tb_rotators -Mdir build/vl tb/tb_rotators.v rtl/*.v >build/verilator.log 2>&1
    build/vl/Vtb_rotators
else
    # iverilog works too, but the 384-lane netlists make it slow (tens of minutes)
    echo "== RTL simulation (iverilog; verilator not found)"
    iverilog -g2005 -o build/tb_rotators tb/tb_rotators.v rtl/*.v
    vvp -n build/tb_rotators
fi
