#!/bin/bash

# Run compile_results.py over a folder of folders.
# Generate an R workspace with all CSV files imported.
#
# Note: May only work in MacOS

root=$1

# Generate R Script
script=${root}/import.r
rm ${script}
touch ${script}

echo "setwd(\"${root}\")" >> ${script}
echo "rm(list = ls())" >> ${script}

echo "import <- function() {" >> ${script}

for dir in $root/*/     # list directories in the form "/tmp/dirname/"
do
    dir=${dir%*/}      # remove the trailing "/"

    # Run compile_results.py on file.
    ./compile_results.py ${dir} ./experiments/basicExperiment.json
    killAll Numbers

    #Rename and properly format CSV file.
    rename=$(basename $dir)
    source=${dir}/compiled-results-basicExperiment.csv
    target=${dir}/${rename}.csv

    mv $source $target

    # Remove first 4 lines and remove last line.
    tail -n +5 $target > ${target}.tmp && mv ${target}.tmp $target
    sed -i '' -e '$ d' ${target}

    dataFrame=$(echo "$rename" | tr - _)
    echo "  $dataFrame <<- read.csv(\"$target\", header = TRUE)" >> ${script}
done  

echo "}" >> ${script}
echo "import()" >> ${script}

echo "save.image(\"${root}data.RData\")" >> ${script}

Rscript ${script}
open ${root}data.RData