### Instructions for deploying ReEDS in local environment

#### 1. Download essential softwares

Before you deploy please make sure you have following softwares installed in your computer.

* `Docker latest version`: Please visit  https://www.docker.com/get-started/ to download the Docker software. Choose your operating system (OS) type, download, and follow installation prompts.
* `Git bash`: Please visit the link https://git-scm.com/downloads to download gitbash and choose appropriate operating system
* `Anaconda` : Used to manage python environments. Please visit https://www.anaconda.com/ to download latest version of Anaconda. Optionally if you have miniconda that also works.
* `GAMS`: ReEDS uses GAMS to perform optimization. Please visit https://www.gams.com/ to install latest version of GAMS. Note this is not an opensource software you need to have LICENSE to use this. If you are already an NREL employee please reach out to ReEDS India team to get the LICENSE file. 
* `Node`: Node is used to run the front end application. Please visit https://nodejs.org/en/ to download the latest version of the code.


#### 2. Clone the repositories

ReEDS is a set of two microservices. You need to clone following repositories to be able to make changes and test it. Make sure you have an account in GitHub and reach out to ReEDS India team so that they can add you to the repository.

* ReEDS API + ReEDS: `git clone git@github.com:NREL/reeds_india_api.git`
* ReEDS UI: `git clone git@github.com:NREL/reeds_india_ui.git`

#### 3. Create a virtual environment

- Create a python virtual environment by running the following command.
``` cmd
    conda create -n reeds python==3.8
```

- Install the python requirements
``` cmd
    cd reeds_api
    conda activate reeds
    pip install -r requirements.txt
```

### 4. Preparing development database environment

If you are already using pre-setup database for ReEDS you can totally skip this. This section explains how you can setup development database using Docker. I am using MySQL as an example however you can use PostGres or SQLite if you prefer those.

- Use docker to spin off MySQL databse server by running following command. Feel free to change the volume path and password.

    ```
        docker run --name mysql1 -p 3306:3306 -v C:\Users\KDUWADI\Desktop\NREL_Projects\ReEDs\reeds_microservices\reeds_database:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=password -d mysql:latest
    ```

- Create `reeds` database. I prefer installing MySQL workbench and connecting to the database (https://www.mysql.com/products/workbench/)
- Connect to database server from MySQL workbench. Hostname: 127.0.0.1, Port: 3306, Username: root, Password: password
  
- Run following query to create database named `reeds`
  
    ```cmd
    create database reeds
    ``` 
- Let's create all the tables. To do this open file `reeds_india_api/reeds_server/web/create_db.py` and edit the db_connection_string. It should be something like this `mysql://root:password@localhost:3306/reeds`. Make sure to change the username, password and/or database name if necessary. After updating this file open up the command prompt and execute following commands.

    ```cmd
    cd reeds_india_api/reeds_server/web
    conda activate reeds
    python create_db.py
    ```

#### 5. Preparing development caching database environment

If you are already using pre-setup caching database for ReEDS you can totally skip this. This section explains how you can setup REDIS database using Docker for caching purpose.

- Use docker to spin off REDIS database

```cmd
docker run --name redis -d -p 6379:6379 redis
```

#### 6. Preparing environment file for ReEDS

Create a file named `.env` in `reeds_india_api\reeds-server` directory and copy paste following contents. Make sure to change the appropriate values.

```
JWT_KEY='test$%^ReEDS'
DB_CONN_STRING='mysql://root:password@localhost:3306/reeds'
NUM_OF_PROCESS=1
BASE_URL_RESET_PASSWORD='http://localhost:8080/change-password'
BASE_URL_USER_SIGNUP='http://localhost:8080/new-user'
BASE_URL_FOR_SIMULATION_STATUS='http://localhost:5002/notifications'
REEDS_SENDER=''
REEDS_SUPERUSER='reedssuperuser'
REEDS_SUPERUSER_PASSWORD='reedssuperpassword'
REEDS_SUPERUSER_EMAIL='reeds-india@nrel.gov'
NOTIFIERHOST='localhost'
NOTIFIERPORT='5002'
REDIS_HOST='localhost'
REDIS_PORT=6379
DEPLOY_MODE='local'
```

#### 7. Prepolulate the database with superuser and default scenarios

To prepopulate superuser and default scenarios first update the file `reeds_india_api\reeds_server\web\pre_populate_tables.py` to use correct db_connection_string `(e.g. mysql://root:password@localhost:3306/reeds)`.

Open up a command prompt and run following commands.

```cmd
cd reeds_india_api/reeds_server
conda activate reeds
python pre_populate_tables.py
```

#### 8. Deploy the services

1. First deploy the REST API by running the following command. Before you run the command make the path change in `reeds_india_api/reeds_server/logging.local.yaml` file.

    ```cmd
    cd reeds_india_api
    conda activate reeds
    python reeds_server/server.py
    ```

2. Second deploy the frontend dashboard. If this the first time running your frontend application install dependencies first.

    ```cmd
    cd reeds_ui
    npm install
    ```

    Run the server by executing following command
    ```cmd
    npm run serve
    ```

Visit `localhost:8080/login` and use the REEDS superuser username and password.

Good luck :wave:.


### Frequently asked questions (FAQ)

_Q1. What to do if you receive Docker Desktop - Access Denied error ?_

When using a Windows OS, if you are not part of the docker-users group, then you might get Docker Desktop – Access Denied error. To fix this error, run Computer Management as an administrator and navigate to Local Users* and Groups > Groups > docker-users. Right-click to add the user to the group. Log out and log back in for the changes to take effect. If you receive the same error warning when running a Linux OS, try the solution posted in this Stackoverflow article. If you are installing docker desktop in Windows and your Windows version supports a subsystem for Linux (WSL 2) , please refer to the steps outlined in this article.

_Q2. How to setup SSH for GitHub access ?_

- Generate SSH key if you have not done already: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key
- Add SSH key to the ssh-agent: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#adding-your-ssh-key-to-the-ssh-agent

_Q3. Getting error when using Python connect to MySQL_

This may be the issue with how you are installing python dependency for connecting to MySQL. Please use the command `conda install -c anaconda mysql-connector-python` to install MYSQL connector.

_Q4. How do I create separate user in MySQL ?_

Use the following commands. Do change username, password and database name.

```
CREATE USER 'newuser'@'%' IDENTIFIED BY 'newpassword';
GRANT ALL PRIVILEGES ON test_db.* to 'newuser'@'%';
```

