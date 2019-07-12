function handler () {
  EVENT_DATA=$1
  echo "$EVENT_DATA" 1>&2;

  BUCKET_NAME=testbucket
  OBJECT_NAME=testworkflow-2.0.1.jar
  TARGET_LOCATION=/opt/test/testworkflow-2.0.1.jar

  JSON_STRING=$( jq -n \
                    --arg bn "$BUCKET_NAME" \
                    --arg on "$OBJECT_NAME" \
                    --arg tl "$TARGET_LOCATION" \
                    '{bucketname: $bn, objectname: $on, targetlocation: $tl}' )


  RESPONSE="Echoing request: '$EVENT_DATA' - Headers: '$HEADERS' - URL: 'http://${AWS_LAMBDA_RUNTIME_API}/2018-06-01/runtime/invocation/next' - JSON Example: '$JSON_STRING'"
  echo $RESPONSE
}