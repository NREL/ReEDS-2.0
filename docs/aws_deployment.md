### Instructions for deploying ReEDS Web app in AWS 

##### 1. Setting up EC2 instance and EBS volume

Please use the following table as a reference  to spin off EC2 instance and EBS volume for deploying ReEDS web app for production environment.

| Metadata | Value |
| -------- | ----- |
| Region   | US East (Ohio)|
| Name | ReEDS India |
| Tags | org = reeds-india <br/> billingId = 220038 <br/> owner = <>|
| OS Image | Amazon Linux 64 bit |
| Instance type | a1.4xlarge (for production) <br/> a1.large (for sandbox) |
| Generate key-pair (.pem) | Yes for SSH access |
| VPC | Use default VPC or create one |
| Subnet | Use default or create one |
| Auto-assign public IP | Yes |
| Firewall | - SSH <br/>  - Inbound from HTTP & HTTPS or from security group of load balancer <br/> - Outbound anywhere |
| EBS volume | 500 GB, gp3, 3000 IOPS, 128 MB/s for production <br/> 20GB, gp3, 3000 IOPS, 128 MB/s for sandbox |


#### 2. Donwloading required softwares in EC2 instance

1. Download git

    ```
    sudo yum install git
    ```

2. Install Node JS


    ```
    curl -sL https://rpm.nodesource.com/setup_14.x | sudo bash -
    sudo yum install -y nodejs
    ```

3. Install nginx
   
   ```
   sudo amazon-linux-extras install nginx1
   ```

4. Install GAMS, setup environment paths and copy license

    - Install GAMS

        ```
        sudo mkdir /opt/gams
        wget https://d37drm4t2jghv5.cloudfront.net/distributions/25.1.3/linux/linux_x64_64_sfx.exe -O /opt/gams/gams_linux.exe
        sudo chmod u+x /opt/gams/gams_linux.exe
        sudo /opt/gams/gams_linux.exe
        ```
    - Set environment paths

        Open up .bashrc file and copy paste following at the end of the file. To open the .bashrc file just use the command `/usr/bin/vim ~/.bash_profile`

        ```
        GAMS_DIR='/opt/gams/gams25.1_linux_x64_64_sfx'
        LD_LIBRARY_PATH='/opt/gams/gams25.1_linux_x64_64_sfx'
        export GAMS_DIR
        export LD_LIBRARY_PATH
        PATH=$PATH:$HOME/.local/bin:$HOME/bin:$GAMS_DIR:$LD_LIBRARY_PATH
        ```
    - Copy the license
    Request the license file from ReEDS team and copy the file in the right location.
    ```
    sudo cp gamslice.txt /opt/gams/gams25.1_linux_x64_64_sfx/gamslice.txt
    ```

#### 4. Clone the repositories in EC2 instance

Make sure you have access to ReEDS GitHub repositories. ReEDS is a set of two microservices. You need to clone the following repositories to be able to make changes and test it. Make sure you have an account in GitHub and reach out to ReEDS India team so that they can add you to the repository. Create a `reeds_india` folder and clone repositories inside. 

* ReEDS API + ReEDS: `git clone git@github.com:NREL/reeds_india_api.git`
* ReEDS UI: `git clone git@github.com:NREL/reeds_india_ui.git`

If you see issue with SSH follow the instruction here [https://docs.github.com/en/authentication/connecting-to-github-with-ssh](https://docs.github.com/en/authentication/connecting-to-github-with-ssh) to setup SSH for GitHub.

#### 5. Create a python virtual environment inside the `reeds_india` folder
- Create environment
    ```
    python3 -m venv env
    source env/bin/activate
    ```

- Install the python requirements
    ``` cmd
    source env/bin/activate
    cd reeds_india_api
    pip install -r requirements.txt
    ```

#### 6. Setting up Elastic Cache

Use following metadata for spinning of AWS Elastic Cache

| Metadata | Value |
| -------- | ----- |
| Node type | cache.t4g.small (for production) </br> cache.t4g.micro (for sandbox) |
| Encryption | Enabled both at rest and in flight |
| Token | Enabled (please save the token somewhere safe) |
| Backups | No |
| AZ | 1 |
| Replica | No |
| Failover | Disable |
| Cluster mode | No |

Optional testing connection to REDIS CLI. Follow instructions here https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/GettingStarted.ConnectToCacheNode.html 

Connection testing using redis-cli

```
sudo yum install gcc jemalloc-devel openssl-devel tcl tcl-devel clang wget
sudo wget http://download.redis.io/redis-stable.tar.gz
sudo tar xvzf redis-stable.tar.gz
cd redis-stable
sudo CC=clang make BUILD_TLS=yes
src/redis-cli -h master.reedsindia.gdnhhn.usw1.cache.amazonaws.com --tls -a <token> -p 6379
```

#### 7. Setting up AWS s3 bucket

1. Create a simple bucket no encrption required only used for storing logs
2. Create a IAM role for EC2 instance by visiting IAM section and clicking on role
3. Crete a IAM policy to send email using AWS SES give only sen email access to IAM policy
4. Attach IAM policy to IAM role 
5. Attach the role to EC2 instance and you are good to go

#### 8. Setting up MySQL or Postgres database 

1. Launch MySQL RDS instance (db.t2.micro for sandbox) or NREL PostgresSQL server (for production)
2. Connect to MySQL workbench or PgAdmin tool to view database
3. Instructions for MySQL workbench setup

   - Start a new connection, and select Standard TCP/IP over SSH for the Connection Method.
   - Enter the following details about the EC2 instance for the SSH settings:
        ```
        SSH Hostname: Enter the public DNS name of the EC2 instance.
	    SSH Username: Enter the user name for your EC2 instance. For example, "ec2-user" is the user name for EC2 Linux machines.
	    SSH Key File: Select the private key that was used when the EC2 instance was created.
        ```
    -  Enter the following details for the MySQL instance settings:
        ```
        MySQL Hostname: Enter the RDS DB instance endpoint.
		MySQL Server port: Enter 3306 (or the custom port that you use).
		Username: Enter the master user name of the RDS DB instance.
		Password: Enter the master password of the RDS DB instance.
        ```
    - Choose Test Connection: After the connection is successful, enter a connection name, and save the connection.

4. If you run into issues installing mysql clinet try one of the following (https://pypi.org/project/mysqlclient/)
   
   ```
   sudo yum install python3-devel mysql-devel
   pip install mysqlclient
   ```

5. Create the database name `reeds`
   
```
create database reeds
```

#### 9. Setting up AWS Simple Email Service

- Visit AWS SES and register this email `reeds-india@nrel.gov`.
- Create a IAM policy for accessing SES from EC2 instance and attach it to the role created previously
  
#### 10. Creating .env file for deployment 

Create a file named `.env` in `reeds_india_api\reeds-server` directory and copy paste following contents. Make sure to change the appropriate values.

```
JWT_KEY='test$%^ReEDS'
DB_CONN_STRING='mysql://root:password@localhost:3306/reeds'
NUM_OF_PROCESS=1
BASE_URL_RESET_PASSWORD='http://localhost:8080/change-password'
BASE_URL_USER_SIGNUP='http://localhost:8080/new-user'
BASE_URL_FOR_SIMULATION_STATUS='http://localhost:5002/notifications'
REEDS_SENDER='reeds-india@nrel.gov'
REEDS_SUPERUSER='reedssuperuser'
REEDS_SUPERUSER_PASSWORD='reedssuperpassword'
REEDS_SUPERUSER_EMAIL='reeds-india@nrel.gov'
NOTIFIERHOST='localhost'
NOTIFIERPORT='5002'
REDIS_HOST='localhost'
REDIS_PORT=6379
DEPLOY_MODE='local'
AWS_REGION='us-west-1'
S3_BUCKET='reeds-india'
LOG_FOLDER='/home/ec2-user/reeds-india/logs'
```

#### 11. Creating initial tables in database

* Let's create all the tables. To do this open file `reeds_india_api/reeds_server/web/create_db.py` and edit the db_connection_string. It should be something like this `mysql://root:password@localhost:3306/reeds` for MySQL appropriatly uncomment the connection string for other type of databases.. Make sure to change the username, password and/or database name if necessary. After updating this file open up the command prompt and execute following commands.

    ```cmd
    cd reeds_india_api/reeds_server/web
    conda activate reeds
    python create_db.py
    ```

#### 12. Prepoluating database with superuser 

To prepopulate superuser and default scenarios first update the file `reeds_india_api\reeds_server\web\pre_populate_tables.py` to use correct db_connection_string `(e.g. mysql://root:password@localhost:3306/reeds)`.

Open up a command prompt and run following commands.

```cmd
cd reeds_india_api/reeds_server
conda activate reeds
python pre_populate_tables.py
```
 
#### 13. Deploy the services

Refer to https://github.com/KapilDuwadi/free_code_snippets/blob/main/docs/ec2_instance.md for launching the long running server in the background. You would need to create a separate screen.

1. First deploy the REST API by running the following command. Before you run the command make the path change in `reeds_india_api/reeds_server/logging.aws.yaml`  file.

    ```cmd
    cd reeds_india_api
    conda activate reeds
    python reeds_server/server.py
    ```

2. Second deploy the frontend dashboard. If this the first time running your frontend application install dependencies first. Update the config.js inside `reeds_ui/src/config.js` to change the URLS. It should look something like this.

    ```
    export default {
        apiURL: 'http://13.57.16.146/api',
        notificationURL: 'http://13.57.16.146/notifications'
    }
    ```

    ```cmd
    cd reeds_ui
    npm install
    ```

    Run the server by executing following command
    ```cmd
    npm run serve
    ```

Visit `<public-ip>:8080/login` and use the REEDS superuser username and password. Note you may have to change security rule to allow 8080 port for testing.


#### Using NGINX to deploy frontend

1. Useful nginx commands
   
    ```
    sudo service nginx start
    sudo service nginx stop
    sudo service nginx status
    sudo service nginx reload
    sudo service nginx restart
    ```

2. Build the vue application. To do this cd into cloned `reeds_ui` repo and run the following command.
   ```
   sudo npm install
   sudo npm run build
   ```

3. Copy the build files into the right directory
   
   ```
   sudo cp -R dist \usr\share\nginx\dist
   sudo chown -R root:root \usr\share\nginx\dist
   ```

4. Edit the nginx conf file (this works for sandbox, production might require slight modification.)
    
    ```
    server {
        listen       80;
        listen       [::]:80;
        server_name  _;
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        error_page 404 /404.html;
        location /api/ {
                proxy_pass http://localhost:5001;
        }
        location /notifications/ {
                proxy_pass http://localhost:5002;
        }
        location / {
                root /usr/share/nginx/dist;
        
        <other contents>
    }
    ```

5. You may need to add A record and C name record depending on how are you providing domain name.

Good luck :wave:.






