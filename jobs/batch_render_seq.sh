#!/bin/bash
set -e
WORKSPACE=/home/ubuntu/render_workspace

for s in {1..25}; do
    mkdir -p $WORKSPACE/batch_output/seed_${s}
    if [ ! -f "$WORKSPACE/batch_output/seed_${s}/frame.png" ]; then
        if [ -f "$WORKSPACE/seed_${s}_metal.obj" ]; then
            timeout 600 blender -b --factory-startup -E CYCLES \
                -P $WORKSPACE/render_job.py \
                -- $WORKSPACE/seed_${s}_metal.obj \
                   $WORKSPACE/seed_${s}_gem.obj \
                   $WORKSPACE/batch_output/seed_${s}/ \
                > $WORKSPACE/batch_output/seed_${s}/render.log 2>&1
            echo "DONE seed_${s}"
        fi
    else
        echo "SKIPPED seed_${s} (already rendered)"
    fi
done

echo "ALL_DONE_SEQUENTIAL"
