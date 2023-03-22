### Information about various useful git commands and procedures

#### 1. Procedure for pushing changes to central git repository

This section describes the procedure for pushing changes made locally to the central git repository (repo). The following commands should be run within Git Bash and within the appropriate repo branch (or another application that allows git to be used in a command-line interface)

1. First pull down any changes made to the central repo. 
   
    ```cmd
    git pull
    ```

2. Check the status of the repository to see which files have been modified, added, or deleted locally.

    ```cmd
    git status
    ```

3. If it is not clear whether a certain modified file needs to be added, committed, and pushed to the central repo, then we can check what changes were made.

    ```cmd
    git diff [insert file name]
    ```

4. Add all of the files that were modified or created and that need to be committed and pushed to the central repo. (Not all modified or created files necessarily need to be added - see step 3). 

    ```cmd
    git add [insert file name]
    ```

5. Once all the necessary files are added, commit those files to the central repo.

    ```cmd
    git commit -m "[insert message about the commit]"
    ```

6. Push the files to the central repo.
    ```cmd
    git push
    ```