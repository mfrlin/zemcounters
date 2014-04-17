mkdir -p ~/mongotest/data/db1
mkdir ~/mongotest/data/db2
mkdir ~/mongotest/data/db3
mkdir ~/mongotest/log
touch ~/mongotest/log/mongo1.log
touch ~/mongotest/log/mongo2.log
touch ~/mongotest/log/mongo3.log

mongod --port 27017 --replSet=foo --dbpath ~/mongotest/data/db1 --logpath ~/mongotest/log/mongo1.log --smallfiles --fork
mongod --port 27018 --replSet=foo --dbpath ~/mongotest/data/db2 --logpath ~/mongotest/log/mongo2.log --smallfiles --fork
mongod --port 27019 --replSet=foo --dbpath ~/mongotest/data/db3 --logpath ~/mongotest/log/mongo3.log --smallfiles --fork
sleep 2
mongo --eval "rs.initiate()"
sleep 2
mongo --eval "rs.add('virtual-work:27018')"
mongo --eval "rs.add('virtual-work:27019')"


