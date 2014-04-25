import os
import io
import re
import json
import codecs
import time
import zipfile
from zipfile import ZipFile
import shlex
import MySQLdb
import pexpect

#
# Parse Events JSON data and write it to a file
#
def parse_events(data, f):
    for events in data["rows"]:
        source = "" if not events["source"] else events["source"]
        key = "" if not events["key"] else events["key"].replace("\n", " ")
        data = "" if not events["data"] else events["data"].replace("\r\n", " ").replace('"', "'")
        recorded_on = "" if not events["recorded_on"] else events["recorded_on"]

        if source == "visit-page":
            extra = re.search("'duration':([0-9]+),'location':'https:\/\/.+\/(.+?)[^a-z](?:(?:unit|name)=([a-zA-Z0-9\._]*|[0-9]+))*(?:&lesson=([0-9]+).*)*", data)

        duration = extra.group(1)
        tag = extra.group(2)
        unit_value = extra.group(3)
        lesson_value = extra.group(4)
        if not duration:
            duration = ""
        if not tag:
            tag = ""
        if not unit_value:
            unit_value = ""
        if not lesson_value:
            lesson_value = ""
        if re.search("[0-9]+", unit_value) and lesson_value == "":
            lesson_value = '1'

        string = (events["user_id"]+","+
            recorded_on+","+
            source+","+
            key+",\""+
            duration+"\",\""+
            tag+"\",\""+
            unit_value+"\",\""+
            lesson_value+"\",\""+
            data+"\"\n")
        f.write(string.encode("utf-8"))

#
# Parse Students JSON data and write it to a file
#
def parse_info(data, f, temp):
    for students in data["rows"]:
        name = students["name"].replace(",", "")
        if not students["key.name"] in temp:
            #Age, Motivation, Profession
            age = "0" if not students["age"] else students["age"]
            motivation = "" if not students["motivation"] else students["motivation"].replace("\r\n", " ")
            profession = "" if not students["profession"] else students["profession"].replace("\n", " ")

            #City, State, Country
            city = "" if not students["city"] else students["city"].replace("\n", " ")
            state = "" if not students["state"] else students["state"].replace("\n", " ")
            country = "" if not students["country"] else students["country"].replace("\n", " ")

            #Scores, Key
            scores = "" if not students["scores"] else students["scores"].replace('"', "'")
            key = "" if not students["key"] else students["key"].replace("\n", " ")

            #Organization, Education
            org = "" if not students["organization"] else students["organization"].replace("\n", " ")
            edu = "" if not students["education"] else students["education"].replace("\n", " ")

            #is_enrolled, Enrolled_on
            is_enrolled = '1' if students["is_enrolled"] else '0'
            enrolled_on = "" if not students["enrolled_on"] else students["enrolled_on"].replace("\n", " ")

            #referral
            referral = "" if not students.get("referral", "") else students.get("referral", "")

            temp.append(students["key.name"])
            string = ("\""+name+"\","+
                "\"\","+
                "\""+students["user_id"]+"\","+
                "\"\","+
                "\""+students["key.name"]+"\","+
                "\"\","+
                "\""+age+"\","+
                "\""+motivation+"\","+
                "\""+city+"\","+
                "\""+state+"\","+
                "\""+country+"\","+
                "\""+profession+"\","+
                "\""+is_enrolled+"\","+
                "\""+scores+"\","+
                "\""+org+"\","+
                "\""+edu+"\","+
                "\""+referral+"\","+
                "\""+enrolled_on+"\","+
                "\"\""+
                "\n")

            f.write(string.encode("utf-8"))


#
# Download datastore data from GAE
# TODO:
# Put your own app_id in the cmd
#
current_time = time.strftime("%m.%d.%Y_%H.%M.%S")
cmd = "python ./cgl-mooc-builder/tools/etl/coursedata.py download datastore / your_app_id your_app_id.appspot.com --archive_path ./coursedata/your_app_id_"+current_time+".zip --datastore_types Student,EventEntity"
child = pexpect.spawn(cmd, timeout=1000)
i = child.expect(['.*Email: ', pexpect.EOF, pexpect.TIMEOUT])
if i == 0:
    # TODO: your Google email and App specific password
    print('match')
    child.sendline('YOUR_GOOGLE_EMAIL_HERE')
    child.expect('Password: ')
    child.sendline('YOUR_APP_SPECIFIC_PASSWORD_HERE')
    child.interact()
elif i == 1:
    print('EOF')
elif i == 2:
    print('TIMEOUT')
    child.close()
    exit(1)

if child.isalive():
    child.close()

if child.isalive():
    print('Child process did not exited gracefully')
else:
    print('Child process exited gracefully')

#
# Create a folder and unzip data files
#
os.mkdir("/"+current_time)
zip_ref = zipfile.ZipFile("./coursedata/your_app_id_"+current_time+".zip", 'r')
zip_ref.extractall("./coursedata/"+current_time)
zip_ref.close()

# Open files to write: one for Enrollment, one for Events
# Students_Enrollment_Sp2014_<MM.DD.YYYY_hh.mm.ss>.csv
# Students_Events_Sp2014_<MM.DD.YYYY_hh.mm.ss>.csv
# TODO: your output filename
output_CSV_Enrollment = "Students_Enrollment_Sp2014_"+current_time+".csv"
output_CSV_Events = "Students_Events_Sp2014_"+current_time+".csv"
f = open("./coursedata/"+output_CSV_Enrollment, 'wb')
f.write("name,role,user_id,university_id,email,university_email,age,motivation,city,state,country,profession,is_enrolled,scores,organization,education,referral,enrolled_on,class\n")
f2 = open("./coursedata/"+output_CSV_Events, "wb")
f2.write("user_id,recorded_on,source,key,duration,tag,unit_value,lesson_value,data\n")

# Open and read JSON files
# Parse the JSON file and write the data into CSV files
# TODO: make sure the path is correct
json_data = open("./coursedata/"+current_time+"/files/Student.json", "rb")
data = json.load(json_data)
json_data.close()
temp = []
parse_info(data, f, temp)
f.close()

# TODO: make sure the path is correct
json_data_Events = open("./coursedata/"+current_time+"/files/EventEntity.json", "rb")
data_Events = json.load(json_data_Events)
json_data_Events.close()
parse_events(data_Events, f2)
f2.close()

try:
    # Connect to MySQL
    # Write/replace students and events data in tables
    # TODO:
    # Put your host, user, passwd, and database name here
    con = MySQLdb.connect(host="localhost", user="root", passwd="your_password", db="your_database_name")
    cur = con.cursor()
    # TODO: make sure the file path is correct
    cur.execute('LOAD DATA LOCAL INFILE "./coursedata/'+output_CSV_Enrollment+'" IGNORE INTO TABLE Students COLUMNS TERMINATED BY "," OPTIONALLY ENCLOSED BY \'"\' LINES TERMINATED BY "\n" IGNORE 1 LINES')

    cur.execute('TRUNCATE TABLE Events')
    # TODO: make sure the file path is correct
    cur.execute('LOAD DATA LOCAL INFILE "./coursedata/'+output_CSV_Events+'" REPLACE INTO TABLE Events COLUMNS TERMINATED BY "," OPTIONALLY ENCLOSED BY \'"\' LINES TERMINATED BY "\n" IGNORE 1 LINES')

    # Output a CSV Events report
    # and close the database connection
    # TODO: make sure the file path of the output file is correct
    cur.execute("SELECT 'Name and Email', 'Class', 'Role', 'Unit', 'Duration' UNION ALL SELECT concat(s.name, ' (', s.email, ')'), s.class, s.role, e.unit_value, sum(e.duration) INTO OUTFILE '/tmp/Events_Report"+current_time+".csv' fields terminated by ',' lines terminated by '\n' from Students s, Events e where s.user_id = e.user_id AND source='visit-page' AND e.tag='unit' group by s.university_id, e.unit_value")

except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    exit(1)

finally:
    if con:
        con.close()

#
# Move the report to coursedata folder
# TODO: make sure the path is correct
os.rename("/tmp/Events_Report"+current_time+".csv", "/root/mycourse/coursedata/Events_Report_"+current_time+".csv")

#
# Remove the downloaded zip file
# TODO: make sure the path is correct
os.remove('./coursedata/your_app_id_'+current_time+'.zip')

