function handler () {
  EVENT_DATA=$1
  echo "$EVENT_DATA" 1>&2;

  RESPONSE="Hello $(echo $EVENT_DATA | ./dependencies/jq-linux64.dms '.name')!"
  echo $RESPONSE
}