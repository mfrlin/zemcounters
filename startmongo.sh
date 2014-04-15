mkdir -p ~/mongotest/data/db
mkdir ~/mongotest/log
touch ~/mongotest/log/mongo.log
mongod --port 27017 --replSet=foo --dbpath ~/mongotest/data/db --logpath ~/mongotest/log/mongo.log --smallfiles --fork
sleep 2
mongo --eval "rs.initiate()"
