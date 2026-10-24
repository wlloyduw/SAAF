#
# Define your FaaS Function here. The bootstrap passes the request JSON as the
# first argument and returns everything written to standard out as the response,
# so write any logging to standard error.
#
function handler () {
  EVENT_DATA=$1
  echo "$EVENT_DATA" 1>&2;

  # Import the module and collect data
  Inspector
  inspectAll

  # Add custom message and finish the function
  name=$(echo "$EVENT_DATA" | "$SAAF_JQ" -r '.name // empty' 2> /dev/null || true)
  if [ -n "$name" ]; then
    addAttribute "message" "Hello $name!"
  else
    addAttribute "message" "Hello World!"
  fi

  inspectAllDeltas
  finish
}
