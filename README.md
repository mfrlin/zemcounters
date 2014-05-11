zemcounters
===========

Distributed counters for a programming competition

requires Python3.3+ and MongoDB

For automatic failover to work at least 3 MongoDB instances should run together in a replica set.  
See `startmongo.sh` script for an example how to start 3 MongoDBs.

You start application server with `python zemcounters/server.py`. This will start a process for each core your computer has.
If you want more than one application server you need to set up a load balancer (preferably nginx) infront.

API:

`/<collection>/`  
regex for collection: `([\w]{1,128})`  
POST: Creates a counter in a collection and returns the location in `Location` header with status 201.  
MongoDB's namespace limitations apply here, so you are limited in amount of collections you can have.

`/<collection>/<counter_id>`  
regex for counter_id: `([a-zA-Z0-9]{24})`
GET: Returns the value of the counter via JSON.
POST: Increments the counter by 1.

`/<collection>/<counter_id>/<n>`  
POST: Increments the counter by n.

`/<collection>/<counter_id>/reset`  
POST: Resets the counter to 0.



