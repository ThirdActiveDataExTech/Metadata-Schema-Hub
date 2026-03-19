#!/bin/sh

# Replace environment variables in config.js
envsubst < /app/dist/config.js > /app/dist/config.js.tmp
mv /app/dist/config.js.tmp /app/dist/config.js

# Start the server
exec node server.js
