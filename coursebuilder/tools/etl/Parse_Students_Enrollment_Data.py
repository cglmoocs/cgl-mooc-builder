import io
import json
import codecs
import time

def parse_info(data, f, temp):
    for students in data["rows"]:
        name = students["name"].replace(",", "")
        if not students["key.name"] in temp:
            #Age, Motivation, Profession
            age = "" if not students["age"] else students["age"]
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
            is_enrolled = "true" if students["is_enrolled"] else "false"
            enrolled_on = "" if not students["enrolled_on"] else students["enrolled_on"].replace("\n", " ")

            #referral
            referral = "" if not students.get("referral", "") else students.get("referral", "")

            temp.append(students["key.name"])

            mining_string = ("\""+name+"\",\""+
                students["user_id"]+"\",\""+
                students["key.name"]+"\",\""+
                age+"\",\""+
                country+"\",\""+
                profession+"\",\""+
                edu+"\",\""+
                referral+"\",\""+
                enrolled_on+"\",\""+"1\"\n")

            f.write(mining_string.encode("utf-8"))

# Open a file to write.
# The parsed information will be written to this file.
# TODO: Put the file path here.
f = open("BigDataMOOC_Enrollment_"+time.strftime("%m.%d.%Y")+".csv", 'wb')
f.write("name,user_id,email,age,country,profession,education,referral,enrolled_on,count\n")
temp = []

# Open and read json files. The file that is going to be read and parsed.
# TODO: Put your file path here.
json_data = open("C:\\Users\\moocs\\coursedata\\xinfo\\files\\Student.json", "rb")
data = json.load(json_data)
json_data.close()

# Parse and write to file.
parse_info(data, f, temp)

f.close()
