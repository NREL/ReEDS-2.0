FOR /F "tokens=*" %%g IN ('git rev-parse --abbrev-ref HEAD') do (SET VAR=%%g)
cd ..
cd ..
cd ..
git ls-tree -r %VAR% --name-only > tracked_files_list.txt
cd docs\source\documentation_tools
python generate_new_sources.py