#!/bin/bash
# AWS Lambda parallel client testing script
# requires curl, the gnu parallel package, the bash calculator, jq for json processing, and the awscli
#
# script requires packages:
# apt install parallel bc jq awscli curl
#
# To use this parallel test script, create files to provide your function name and AWS gateway URL
# file: parurl        Provide URL from AWS-Gateway
# file: parfunction   Provide AWS Lambda function name on a single line text file
#
totalruns=$1
threads=$2
vmreport=$3
contreport=$4
containers=()
cuses=()
ctimes=()

#########################################################################################################################################################
#  callservice method - uses separate threads to call AWS Lambda in parallel
#  each thread captures results of one service request, and outputs CSV data...
#########################################################################################################################################################
callservice() {
  totalruns=$1
  threadid=$2
  #host=10.0.0.124
  #port=8080
  onesecond=1000
  filename="parurl"
  while read -r line
  do
    parurl=$line
  done < "$filename"

  filename="parfunction"
  while read -r line
  do
    parfunction=$line
  done < "$filename"

  if [ $threadid -eq 1 ]
  then
    echo "run_id,thread_id,uuid,cputype,cpusteal,vmuptime,pid,cpuusr,cpukrn,elapsed_time,sleep_time_ms,new_container"
  fi
  for (( i=1 ; i <= $totalruns; i++ ))
  do
    # JSON object to pass to Lambda Function
    json={"\"name\"":"\"Fred\u0020Smith\",\"param1\"":1,\"param2\"":2,\"param3\"":3}

    time1=( $(($(date +%s%N)/1000000)) )

    ####################################
    # CURL invocation with $parurl variable
    ####################################
    #output=`curl -H "Content-Type: application/json" -X POST -d  $json $parurl 2>/dev/null`

    ####################################
    # Uncomment for AWS Lambda CLI function invocation with $parfunction variable
    ####################################
    output=`aws lambda invoke --invocation-type RequestResponse --function-name $parfunction --region us-east-1 --payload $json /dev/stdout | head -n 1 | head -c -2 ; echo`

    ####################################
    # Uncomment for CURL invocation with inline URL
    ####################################
    #output=`curl -H "Content-Type: application/json" -X POST -d  $json {place URL here} 2>/dev/null`

    # grab end time
    time2=( $(($(date +%s%N)/1000000)) )

    # parsing when /proc/cpuinfo is requested
    uuid=`echo $output | jq '.uuid'`
    cpuusr=`echo $output | jq '.cpuUsr'`  
    cpukrn=`echo $output | jq '.cpuKrn'`
    pid=`echo $output | jq '.pid'`
    cputype="unknown"
    cpusteal=`echo $output | jq '.vmcpusteal'`
    vuptime=`echo $output | jq '.vmuptime'`
    newcont=`echo $output | jq '.newcontainer'`
    
    elapsedtime=`expr $time2 - $time1`
    sleeptime=`echo $onesecond - $elapsedtime | bc -l`
    sleeptimems=`echo $sleeptime/$onesecond | bc -l`
    echo "$i,$threadid,$uuid,$cputype,$cpusteal,$vuptime,$pid,$cpuusr,$cpukrn,$elapsedtime,$sleeptimems,$newcont"
    echo "$uuid,$elapsedtime,$vuptime,$newcont" >> .uniqcont
    if (( $sleeptime > 0 ))
    then
      sleep $sleeptimems
    fi
  done
}
export -f callservice

#########################################################################################################################################################
#  The START of the Script
#########################################################################################################################################################
runsperthread=`echo $totalruns/$threads | bc -l`
runsperthread=${runsperthread%.*}
date
echo "Setting up test: runsperthread=$runsperthread threads=$threads totalruns=$totalruns"
for (( i=1 ; i <= $threads ; i ++))
do
  arpt+=($runsperthread)
done
#########################################################################################################################################################
# Launch threads to call AWS Lambda in parallel
#########################################################################################################################################################
parallel --no-notice -j $threads -k callservice {1} {#} ::: "${arpt[@]}"
newconts=0
recycont=0
recyvms=0

#########################################################################################################################################################
# Begin post-processing and generation of CSV output sections
#########################################################################################################################################################


#########################################################################################################################################################
# Generate CSV output - group by container
# Reports unique number of containers used or created
#########################################################################################################################################################
if [[ ! -z $contreport && $contreport -eq 1 ]]
    then
      rm -f .origcont
fi

filename=".uniqcont"
while read -r line
do
    uuid=`echo $line | cut -d',' -f 1`
    time=`echo $line | cut -d',' -f 2`
    host=`echo $line | cut -d',' -f 3`
    isnewcont=`echo $line | cut -d',' -f 4`
    alltimes=`expr $alltimes + $time`
    #echo "Uuid read from file - $uuid"
    # if uuid is already in array
    found=0
    (( newconts += isnewcont))


    ##
    ## Process the contreport flag, to generate or compare against the .origcont file
    ##

    # First populate array of unique containers
    for ((i=0;i < ${#containers[@]};i++)) {
        if [ "${containers[$i]}" == "${uuid}" ]; then
            (( cuses[$i]++ ))
            ctimes[$i]=`expr ${ctimes[$i]} + $time`
            found=1
        fi
    }

    ## Add unfound container to array
    if [ $found != 1 ]; then
        containers+=($uuid)
        chosts+=($host)
        cuses+=(1)
        ctimes+=($time)
    fi

    # Populate array of unique hosts
    hfound=0
    for ((i=0;i < ${#hosts[@]};i++)) {
        if [ "${hosts[$i]}" == "${host}"  ]; then
            (( huses[$i]++ ))
            htimes[$i]=`expr ${htimes[$i]} + $time`
            hfound=1
        fi
    }
    if [ $hfound != 1 ]; then
        hosts+=($host)
        huses+=(1)
        htimes+=($time)
        #hcontainers+=($uuid)
    fi
done < "$filename"

##
##  Determine count of recycled containers...
##
# Append containers to .origcont file with contreport flag set to 1...
if [[ ! -z $contreport && $contreport -eq 1 ]]
then
  for ((i=0;i < ${#containers[@]};i++)) {
    echo "${containers[$i]}" >> .origcont
  }  
fi

## if state = 2 compare against file to obtain total count of recycled containers used
if [[ ! -z $contreport && $contreport -eq 2 ]]
then
  for ((i=0;i < ${#containers[@]};i++)) 
  {
    # read the origcont file and compare current containers to old containers in .origcont
    # increment a counter every time we find a recycled container
    # to calculate newcontainer, containers - recycledcontainers
    filename=".origcont"
    breakoutcont=0
    while read -r line
    do
      if [ "${containers[$i]}" == "${line}" ]
      then
          (( recycont ++ ))
    	  breakoutcont=1
          break;
      fi
    done < "$filename"
    # if breakoutcont==0 then:
    # add container to newcont file if its not already there... (function call) 
  }
fi

runspercont=`echo $totalruns / ${#containers[@]} | bc -l`
runsperhost=`echo $totalruns / ${#hosts[@]} | bc -l`
avgtime=`echo $alltimes / $totalruns | bc -l`
rm .uniqcont
echo "uuid,host,uses,totaltime,avgruntime_cont,uses_minus_avguses_sq"
total=0
for ((i=0;i < ${#containers[@]};i++)) {
  avg=`echo ${ctimes[$i]} / ${cuses[$i]} | bc -l`
  stdiff=`echo ${cuses[$i]} - $runspercont | bc -l` 
  stdiffsq=`echo "$stdiff * $stdiff" | bc -l` 
  total=`echo $total + $stdiffsq | bc -l`
  echo "${containers[$i]},${chosts[$i]},${cuses[$i]},${ctimes[$i]},$avg,$stdiffsq"
}

#########################################################################################################################################################
# Generate CSV output - group by VM host
# hosts[] is the array of VM ids - where the VM id is the boot time in seconds since epoch (Jan 1 1970)
#########################################################################################################################################################

stdev=`echo $total / ${#containers[@]} | bc -l`

# hosts info
currtime=$(date +%s)
echo "Current time of test=$currtime"
echo "host,host_up_time,uses,containers,totaltime,avgruntime_host,uses_minus_avguses_sq"
total=0
if [[ ! -z $vmreport && $vmreport -eq 1 ]]
then
  rm -f .origvm 
fi

# Loop through list of hosts - generate summary data
for ((i=0;i < ${#hosts[@]};i++)) {
  avg=`echo ${htimes[$i]} / ${huses[$i]} | bc -l`
  stdiff=`echo ${huses[$i]} - $runsperhost | bc -l` 
  stdiffsq=`echo "$stdiff * $stdiff" | bc -l` 
  total=`echo $total + $stdiffsq | bc -l`
  ccount=0
  uptime=`echo $currtime - ${hosts[$i]} | bc -l`
  for ((j=0;j < ${#containers[@]};j++)) {
      if [ ${hosts[$i]} == ${chosts[$j]} ]
      then
          (( ccount ++ ))
      fi
  } 
  echo "${hosts[$i]},$uptime,${huses[$i]},$ccount,${htimes[$i]},$avg,$stdiffsq"

  ##  Determine count of recycled hosts...
  ## 
  ##  Generate .origvm file to support determing infrastructure recycling stats
  ##
  if [[ ! -z $vmreport && $vmreport -eq 1 ]] 
  then
    echo "${hosts[$i]}" >> .origvm 
  fi
  if [[ ! -z $vmreport && $vmreport -eq 2 ]]
  then
    ##echo "compare vms - check for recycling"
    # read the file and compare current VMs to old VMs in .origvm
    # increment a counter every time we find a recycled VM
    # to calculate newhosts, hosts - recycledhosts
    filename=".origvm"
    breakoutvm=0
    while read -r line
    do
      ##echo "compare '${hosts[$i]}' == '${line}'"
      if [ ${hosts[$i]} == ${line} ]
      then
          (( recyvms ++ ))
          breakoutvm=1
          break;
      fi
    done < "$filename"
    # if breakoutvm==0 then:
    # add vm to .newvm file if its not already there... (function call) 
  fi
}
stdevhost=`echo $total / ${#hosts[@]} | bc -l`

#########################################################################################################################################################
# Generate CSV output - report summary, final data
#########################################################################################################################################################
#
# 
#
echo "containers,newcontainers,recycont,hosts,recyvms,avgruntime,runs_per_container,runs_per_cont_stdev,runs_per_host,runs_per_host_stdev"
echo "${#containers[@]},$newconts,$recycont,${#hosts[@]},$recyvms,$avgtime,$runspercont,$stdev,$runsperhost,$stdevhost"
