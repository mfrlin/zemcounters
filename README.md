zemcounters
===========

Distributed counters for a programming competition

requires Python3.3+ and MongoDB

For automatic failover to work at least 3 MongoDB instances should run together in a replica set.  
See `startmongo.sh` script for an example how to start 3 MongoDBs.

You start application server with `python zemcounters/server.py`. This will start a process for each core your computer has.
If you want more than one application server you need to set up a load balancer (preferably nginx) infront.

API:

`/cnt/<collection>/`
regex for collection: `([\w]{1,128})`

POST: Creates a counter in a collection and returns the location in `Location` header with status 201.

MongoDB's namespace limitations apply here, so you are limited in amount of collections you can have.

`/cnt/<collection>/<counter_id>`
regex for counter_id: `([a-zA-Z0-9]{24})`

GET: Returns the value of the counter via JSON.

POST: Increments the counter by 1.

DELETE: Deletes the counter. Returns 1 via JSON if counter was deleted and 0 if there was no counter with this ID to be deleted.
This doesn't mean an error because if network error occurs counter can be deleted and then on retry 0 is returned.


`/cnt/<collection>/<counter_id>/<n>`

POST: Increments the counter by n.

`/cnt/<collection>/<counter_id>/reset`

POST: Resets the counter to 0.

TAILER:

If you need to poll counters constantly please use tailer because it scales so much better.

You can access tailer via `ws://hostname/tail/` you can optionally include counter id `/tail/<counter_id>`

Once connected you can subscribe and un subscribe by sending json via websocket. `{'<counter_id>': 's'}` subscribes you to the counter and `{'<counter_id>': 'u'}` un subscribes.
When counters are updated you get messages in format: `{'id': '<counter_id>', 'd': 1}` if the counter was deleted and `{'id': '<counter_id>', 'n': n}` with `n` being the new value of the counter.



