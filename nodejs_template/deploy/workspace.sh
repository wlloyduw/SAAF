#!/bin/bash

response=$(curl -i -X POST "https://tutorial3r46878.azurewebsites.net/api/tutorial3r46878?code=f5XYSn7oOmiTgi1hxRAuJkjyeXidn1HKpy7el3390DKa5u6F3OSQVw==" -H "Content-Type: application/json" -d "")

echo $response
