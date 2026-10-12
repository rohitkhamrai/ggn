#!/bin/bash
set -e
WORKSPACE=/home/ubuntu/render_workspace

for s in 1 2 3 4 5 6 7 8 9 10; do
    mkdir -p $WORKSPACE/batch_output/seed_${s}
    (
        timeout 600 blender -b --factory-startup -E CYCLES \
            -P $WORKSPACE/render_job.py \
            -- $WORKSPACE/seed_${s}_metal.obj \
               $WORKSPACE/seed_${s}_gem.obj \
               $WORKSPACE/batch_output/seed_${s}/ \
            > $WORKSPACE/batch_output/seed_${s}/render.log 2>&1
        echo "DONE seed_${s}"
    ) &
done

wait
echo "ALL_DONE"
ls $WORKSPACE/batch_output/*/frame.png 2>/dev/null
