#!/bin/bash

# AWS Lambda parallel client testing script
# requires curl, the gnu parallel package, the bash calculator, jq for json processing, and the awscli
#
# script requires packages:
# apt install parallel bc jq awscli curl
#
# To use this parallel test script, create files to provide your function name and AWS gateway URL
# file: parurl        Provide URL from AWS-Gateway
# file: function   Provide AWS Lambda function name on a single line text file
#
totalruns=$1
threads=$2
vmreport=$3
contreport=$4
containers=()
cuses=()
ctimes=()
csstimes=()
clatency=()
price_gbsec=.00001667
memory_mb=3008
memory_gb=$(echo $memory_mb / 1000 | bc -l)

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


  function=$(cat ./config.json | jq '.functionName' | tr -d '"')

  if [ "$threadid" -eq 1 ]
  then
    echo "run_id,thread_id,uuid,cputype,cpusteal,vmuptime,pid,cpuusr,cpukrn,elapsed_time,server_runtime,latency,sleep_time_ms,new_container"
  fi
  for (( i=1 ; i <= totalruns; i++ ))
  do
    # JSON object to pass to Lambda Function
    #json={"\"name\"":"\"Fred\u0020Smith\",\"param1\"":1,\"param2\"":2,\"param3\"":3}
    json={"\"name\"":"\"\",\"calcs\"":1000000,\"sleep\"":0,\"loops\"":25}
    #json={"\"name\"":"\"\",\"calcs\"":1000000,\"sleep\"":0,\"loops\"":25}
    json=$(cat config.json | jq -c '.payload')

    time1=( $(($(date +%s%N)/1000000)) )

    ####################################
    # CURL invocation with $parurl variable
    ####################################
    #output=`curl -H "Content-Type: application/json" -X POST -d  $json $parurl 2>/dev/null`

    ####################################
    # Uncomment for AWS Lambda CLI function invocation with $function variable
    ####################################
    output=$(aws lambda invoke --invocation-type RequestResponse --function-name "$function" --region us-east-1 --payload "$json" /dev/stdout | head -n 1 | head -c -2 ; echo)
    
    ####################################
    # Uncomment for Google Cloud CLI function invocation with $function variable
    ####################################
    #output=`gcloud functions call $function --data $json | head -n 1 | head -c -2 ; echo`
    
    ####################################
    # Uncomment for IBM Cloud CLI function invocation with $function variable
    ####################################
    #cat $json > input.temp
    #output=`ibmcloud fn action invoke $function -P input.temp -r | head -n 1 | head -c -2 ; echo`
    #rm input.temp

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
    cputype=`echo $output | jq '.cpuType'`
    cputype=${cputype// /_}
    cpusteal=`echo $output | jq '.vmcpusteal'`
    vuptime=`echo $output | jq '.vmuptime'`
    hostname=`echo $output | jq '.vmID'`
    newcont=`echo $output | jq '.newcontainer'`
    ssruntime=`echo $output | jq '.runtime'`
    
    elapsedtime=`expr $time2 - $time1`
    sleeptime=`echo $onesecond - $elapsedtime | bc -l`
    latency=`echo $elapsedtime - $ssruntime | bc -l`
    sleeptimems=`echo $sleeptime/$onesecond | bc -l`
    echo "$i,$threadid,$uuid,$cputype,$cpusteal,$vuptime,$pid,$cpuusr,$cpukrn,$elapsedtime,$ssruntime,$latency,$sleeptimems,$newcont"
    echo "$uuid,$elapsedtime,$ssruntime,$latency,$vuptime,$newcont,$cputype,$hostname" >> .uniqcont
    if (( $sleeptime > 0 ))
    then
      sleep "$sleeptimems"
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
#seq -w 0 1000 | parallel --no-notice -j10 -N 252 -q -I,, --pipe parallel --no-notice -j100 -k callservice {1} {} ::: "${arpt[@]}"
#seq -w 0 1000 | parallel --no-notice -j10 -N 252 -q -I,, --pipe parallel --no-notice -j100 -k callservice {1} {#} ::: "${arpt[@]}"
#'parallel -j0 -N 252 --pipe parallel -j0
# parallel -j10 -q -I,, --pipe parallel -j0 touch pict{}.jpg
# orig

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
    sstime=`echo $line | cut -d',' -f 3`
    latency=`echo $line | cut -d',' -f 4`
    host=`echo $line | cut -d',' -f 5`
    isnewcont=`echo $line | cut -d',' -f 6`
    cputype=`echo $line | cut -d',' -f 7` 
    hostname=`echo $line | cut -d',' -f 8`
    alltimes=`expr $alltimes + $time`
    allsstimes=`expr $allsstimes + $sstime`
    alllatency=`expr $alllatency + $latency`
    allcpusteal=`expr $allcpusteal + $cpusteal`
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
            csstimes[$i]=`expr ${csstimes[$i]} + $sstime`
            clatency[$i]=`expr ${clatency[$i]} + $latency`
            ccpusteal[$i]=`expr ${ccpusteal[$i]} + $cpusteal`
            found=1
        fi
    }

    ## Add unfound container to array
    if [ $found != 1 ]; then
        containers+=($uuid)
        chosts+=($hostname)
	cuptime+=($host)
        ccputype+=($cputype)
        cuses+=(1)
        ctimes+=($time)
        csstimes+=($sstime)
        clatency+=($latency)
        ccpusteal+=($cpusteal)
    fi

    # Populate array of unique hosts
    hfound=0
    for ((i=0;i < ${#hosts[@]};i++)) {
        if [ "${hosts[$i]}" == "${hostname}"  ]; then
            (( huses[$i]++ ))
            htimes[$i]=`expr ${htimes[$i]} + $time`
            hsstimes[$i]=`expr ${hsstimes[$i]} + $sstime`
            hlatency[$i]=`expr ${hlatency[$i]} + $latency`
            hcpusteal[$i]=`expr ${hcpusteal[$i]} + $cpusteal`
            hfound=1
        fi
    }
    if [ $hfound != 1 ]; then
        hosts+=($hostname)
        huptime+=($host)
        huses+=(1)
        hcputype+=($cputype)
        htimes+=($time)
        hsstimes+=($sstime)
        hlatency+=($latency)
        hcpusteal+=($cpusteal)
        #hcontainers+=($uuid)
    fi

    # Populate array of unique CPU types
    cpufound=0
    for ((i=0;i < ${#cpuTypes[@]};i++)) {

        if [ "${cpuTypes[$i]}" == "${cputype}"  ]; then
            (( cpuuses[$i]++ ))
            cputimes[$i]=`expr ${cputimes[$i]} + $time`
            cpusstimes[$i]=`expr ${cpusstimes[$i]} + $sstime`
            cpulatency[$i]=`expr ${cpulatency[$i]} + $latency`
            cpucpusteal[$i]=`expr ${cpusteal[$i]} + $cpusteal`
            cpufound=1
        fi

    }
    if [ $cpufound != 1 ]; then
        cpuTypes+=($cputype)
        cpuuses+=(1)
        cputimes+=($time)
        cpusstimes+=($sstime)
        cpulatency+=($latency)
        cpucpusteal+=($cpusteal)
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
runspercont=`printf '%.*f\n' 3 $runspercont`
runsperhost=`echo $totalruns / ${#hosts[@]} | bc -l`
runsperhost=`printf '%.*f\n' 3 $runsperhost`
avgtime=`echo $alltimes / $totalruns | bc -l`
avgtime=`printf '%.*f\n' 0 $avgtime`
avgsstime=`echo $allsstimes / $totalruns | bc -l`
avgsstime=`printf '%.*f\n' 0 $avgsstime`
avglatency=`echo $alllatency / $totalruns | bc -l`
avglatency=`printf '%.*f\n' 0 $avglatency`
avgcpusteal=`echo $allcpusteal / $totalruns | bc -l`
avgcpusteal=`printf '%.*f\n' 0 $avgcpusteal`
allsstimes_sec=`echo $allsstimes / 1000 | bc -l`
totalcost=`echo "$allsstimes_sec * $price_gbsec * $memory_gb" | bc -l`
totalcost=`printf '%.*f\n' 4 $totalcost`
rm .uniqcont
echo "uuid,host,cputype,uses,totaltime,avgruntime_cont,avgsstuntime_cont,avglatency_cont,uses_minus_avguses_sq"
total=0
for ((i=0;i < ${#containers[@]};i++)) {
  avg=`echo ${ctimes[$i]} / ${cuses[$i]} | bc -l`
  avg=`printf '%.*f\n' 0 $avg`
  ssavg=`echo ${csstimes[$i]} / ${cuses[$i]} | bc -l`
  ssavg=`printf '%.*f\n' 0 $ssavg`
  latencyavg=`echo ${clatency[$i]} / ${cuses[$i]} | bc -l`
  latencyavg=`printf '%.*f\n' 0 $latencyavg`
  stdiff=`echo ${cuses[$i]} - $runspercont | bc -l` 
  stdiffsq=`echo "$stdiff * $stdiff" | bc -l` 
  total=`echo $total + $stdiffsq | bc -l`
  echo "${containers[$i]},${chosts[$i]},${ccputype[$i]},${cuses[$i]},${ctimes[$i]},$avg,$ssavg,$latencyavg,$stdiffsq"
}

#########################################################################################################################################################
# Generate CSV output - group by VM host
# hosts[] is the array of VM ids - where the VM id is the boot time in seconds since epoch (Jan 1 1970)
#########################################################################################################################################################

stdev=`echo $total / ${#containers[@]} | bc -l`
stdev=`printf '%.*f\n' 3 $stdev`

# hosts info
currtime=$(date +%s)
echo "Current time of test=$currtime"
echo "host,host_cpu,host_up_time,uses,containers,totaltime,avgruntime_host,avgssruntime_host,avglatency_host,uses_minus_avguses_sq,avgcpusteal"
total=0
if [[ ! -z $vmreport && $vmreport -eq 1 ]]
then
  rm -f .origvm 
fi

# Loop through list of hosts - generate summary data
for ((i=0;i < ${#hosts[@]};i++)) {
  avg=`echo ${htimes[$i]} / ${huses[$i]} | bc -l`
  avg=`printf '%.*f\n' 0 $avg`
  ssavg=`echo ${hsstimes[$i]} / ${huses[$i]} | bc -l`
  ssavg=`printf '%.*f\n' 0 $ssavg`
  avgcpusteal=`echo ${hcpusteal[$i]} / ${huses[$i]} | bc -l`
  avgcpusteal=`printf '%.*f\n' 0 $avgcpusteal`
  latencyavg=`echo ${hlatency[$i]} / ${huses[$i]} | bc -l`
  latencyavg=`printf '%.*f\n' 0 $latencyavg`
  stdiff=`echo ${huses[$i]} - $runsperhost | bc -l` 
  stdiffsq=`echo "$stdiff * $stdiff" | bc -l` 
  total=`echo $total + $stdiffsq | bc -l`
  ccount=0
  uptime=`echo ${huptime[$i]} | cut -d'"' -f 2`
  #echo "$currtime - $uptime"
  uptime=`echo $currtime - $uptime | bc -l`
  #uptime=`echo $currtime - ${huptime[$i]} | bc -l`
  for ((j=0;j < ${#containers[@]};j++)) {
      if [ ${hosts[$i]} == ${chosts[$j]} ]
      then
          (( ccount ++ ))
      fi
  } 
  echo "${hosts[$i]},${hcputype[$i]},$uptime,${huses[$i]},$ccount,${htimes[$i]},$avg,$ssavg,$latencyavg,$stdiffsq,$avgcpusteal"

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
stdevhost=`printf '%.*f\n' 3 $stdevhost`

#########################################################################################################################################################
# Generate CSV output - group by CPU Types
#########################################################################################################################################################

# CPU Types info
echo "cputype,uses,totaltime,avgruntime_per_cpu,avgssruntime_per_cpu,avglatency_per_cpu"
total=0
#echo "CHECK IF DELETE ORIGVM"
#if [[ ! -z $vmreport && $vmreport -eq 1 ]]
#then
#  echo "DELETING ORIGVM !!!"
#  rm -f .origvm 
#fi

# Loop through CPU Types and make summary data
for ((i=0;i < ${#cpuTypes[@]};i++)) {
  cpuavg=`echo ${cputimes[$i]} / ${cpuuses[$i]} | bc -l`
  cpuavg=`printf '%.*f\n' 0 $cpuavg`
  cpussavg=`echo ${cpusstimes[$i]} / ${cpuuses[$i]} | bc -l`
  cpussavg=`printf '%.*f\n' 0 $cpussavg`
  cpulatency=`echo ${cpulatency[$i]} / ${cpuuses[$i]} | bc -l`
  cpulatency=`printf '%.*f\n' 0 $cpulatency`
  echo "${cpuTypes[$i]},${cpuuses[$i]},${cputimes[$i]},$cpuavg,$cpussavg,$cpulatency"
}


#########################################################################################################################################################
# Generate CSV output - report summary, final data
#########################################################################################################################################################
#
# 
#
echo "containers,newcontainers,recycont,hosts,recyvms,avgruntime,avgssruntime,avglatency,runs_per_container,runs_per_cont_stdev,runs_per_host,runs_per_host_stdev,totalcost"
echo "${#containers[@]},$newconts,$recycont,${#hosts[@]},$recyvms,$avgtime,$avgsstime,$avglatency,$runspercont,$stdev,$runsperhost,$stdevhost,\$$totalcost"
