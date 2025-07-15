#!/bin/bash

# Loop through all files ending with .txt in the current directory
for file in *.txt; do
  # Check if the file actually exists to prevent errors if no .txt files are found
  if [ -f "$file" ]; then
    # Construct the new filename by replacing .txt with .tsv
    new_file="${file%.txt}.tsv"
    # Rename the file
    mv "$file" "$new_file"
    echo "Renamed '$file' to '$new_file'"
  fi
done

echo "All .txt files have been renamed to .tsv (if found)."
