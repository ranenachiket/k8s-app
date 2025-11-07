#Creating raspberry pi as a postgres db server

Step 1: Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

Step 2: Enable and start the service
sudo systemctl enable postgresql
sudo systemctl start postgresql

Step 3: Verify Service is running
sudo systemctl status postgresql

Step 4: Create database and user
sudo -u postgres psql
postgres=# CREATE USER admin WITH PASSWORD 'admin';
CREATE ROLE
postgres=# CREATE DATABASE orders OWNER admin;
CREATE DATABASE
postgres=#
postgres=# GRANT ALL PRIVILEGES ON DATABASE orders TO admin;
GRANT
\q

Step 5: Allow remote connections
Edit the config file: sudo vi /etc/postgresql/16/main/postgresql.conf
listen_addresses = '*'

Edit the file: sudo nano /etc/postgresql/16/main/pg_hba.conf
host    all             all             0.0.0.0/0               md5

Step 6: Restart service:
sudo systemctl restart postgresql

Step 7: Open Port 5432 (if using UFW)
sudo apt install ufw -y
sudo ufw allow 5432/tcp
sudo ufw enable



