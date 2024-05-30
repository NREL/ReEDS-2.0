#!/bin/sh
branch=$(git rev-parse --abbrev-ref HEAD)
cd ..
cd ..
cd ..
git ls-tree -r $branch --name-only > tracked_files_list.txt
cd docs/source/documentation_tools
python generate_new_sources.py