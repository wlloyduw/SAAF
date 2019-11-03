#!/usr/bin/env python3

import boto3
import os
import sys
import json
import shutil
import subprocess
from threading import Thread

sys.path.append('./tools')
from report_generator import report

s3_client = boto3.client('s3')

def pull_file(client, bucket, k, local, delete):
    dest_pathname = os.path.join(local, k)
    if not os.path.exists(os.path.dirname(dest_pathname)):
        os.makedirs(os.path.dirname(dest_pathname))
        print("Directory Created: " + str(os.path.dirname(dest_pathname)))
    client.download_file(bucket, k, dest_pathname)
    print("Pulled File: " + str(k))

#
# Download all files from an S3 bucket, delete them after they are downloaded.
#
# @author https://stackoverflow.com/questions/31918960/boto3-to-download-all-files-from-a-s3-bucket/51745132#51745132
# @author Robert Cordingly
#
def download_dir(prefix, local, bucket, delete, client=s3_client):
    """
    params:
    - prefix: pattern to match in s3
    - local: local path to folder in which to place files
    - bucket: s3 bucket with target contents
    - client: initialized s3 client object
    """
    keys = []
    dirs = []
    next_token = ''
    base_kwargs = {
        'Bucket':bucket,
        'Prefix':prefix,
    }
    while next_token is not None:
        kwargs = base_kwargs.copy()
        if next_token != '':
            kwargs.update({'ContinuationToken': next_token})
        results = client.list_objects_v2(**kwargs)
        contents = results.get('Contents')
        for i in contents:
            k = i.get('Key')
            if k[-1] != '/':
                keys.append(k)
            else:
                dirs.append(k)
        next_token = results.get('NextContinuationToken')
    for d in dirs:
        dest_pathname = os.path.join(local, d)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
            print("Directory Created: " + str(os.path.dirname(dest_pathname)))
        
    # Create worked threads to both download and delete files from s3.
    threadList = []
    for k in keys:
        thread = Thread(target=pull_file, args=(client, bucket, k, local, delete))
        thread.start()
        threadList.append(thread)
    for i in range(len(threadList)):
            threadList[i].join()

    # Clear S3 Bucket:
    if (delete):
        print("Clearing S3...")
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket)
        bucket.objects.all().delete()

# Clear previous cache...
if (os.path.isdir("./.s3cache")):
    print("Clearing previous cache...")
    shutil.rmtree('./.s3cache')
os.makedirs("./.s3cache")

#Input parameteres
bucketName = 'saafdump'
experimentfile = './experiments/exampleExperiment.json'
delete = False
if (len(sys.argv) != 4):
    print("Please supply parameteres! Usage:\n./s3pull.py {S3 BUCKET NAME} {PATH TO EXPERIMENT JSON} {0/1 CLEAR BUCKET?}")
elif (len(sys.argv) == 4):
    bucketName = sys.argv[1]
    experimentfile = sys.argv[2]
    if (sys.argv[3] == '1'):
        delete = True

    # Download files from s3 and delete from s3...
    download_dir('', './.s3cache', bucketName, delete)

    # Load Json Files as Python dictionaries.
    print("Files downloaded. Loading and generating report...")
    run_list = []
    for filename in os.listdir('./.s3cache'):
        if filename.endswith(".json"):
            try:
                run = json.load(open('./.s3cache/' + str(filename)))
                run_list.append(run)
            except Exception as e:
                print("Error loading: " + './.s3cache/' + str(filename) + " with exception " + str(e))
                pass
        else:
            continue

    print(str(run_list))

    # Create report text and save to csv file.
    print("Generating Report...")
    expName = os.path.basename(experimentfile)
    expName = expName.replace(".json", "")
    exp = json.load(open(experimentfile))
    partestResult = report(run_list, exp, True)

    try:
        csvFilename = "./history" + "/" + "async-" + str(bucketName) + "-" + str(
            expName)
        if (os.path.isfile(csvFilename + ".csv")):
            duplicates = 1
            while (os.path.isfile(csvFilename + "-" + str(duplicates) + ".csv")):
                duplicates += 1
            csvFilename += "-" + str(duplicates)
        csvFilename += ".csv"
        text = open(csvFilename, "w")
        text.write(str(partestResult))
        text.close()

        print("Opening results...")
        if sys.platform == "linux" or sys.platform == "linux2":
            # linux
            subprocess.call(["xdg-open", csvFilename])
        elif sys.platform == "darwin":
            # MacOS
            subprocess.call(["open", csvFilename])
        elif sys.platform == "win32":
            # Windows...
            print("File created: " + str(csvFilename))
            pass
        else:
            print("Partest complete. " + str(csvFilename) + " created.")
    except Exception as e:
        print("Exception occurred: " + str(e))
        pass