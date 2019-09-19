function handler () {
  EVENT_DATA=$1
  echo "$EVENT_DATA" 1>&2;
  
  name=$(echo $EVENT_DATA | ./dependencies/jq-linux64.dms '.name' | tail -c +2 | head -c -2)
  RESPONSE="Hello $name!"
  echo $RESPONSE
}