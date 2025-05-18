import email
import json
import os
import random
import re
import smtplib,ssl
import imaplib
import string
import time
import requests
from copy import deepcopy
# from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os.path import basename
from cerberus import Validator
from portal import create_app
from exchangelib import Credentials, Account,Configuration,DELEGATE,NTLM,FileAttachment
import boto3
from botocore.exceptions import NoCredentialsError,ClientError
import fitz
import threading 
from pdf2image import convert_from_path

# bucket_name = APP.config['S3_BUCKET']
# s3_client = boto3.client(
#     's3',
#     aws_access_key_id=APP.config['AWS_ACCESS_KEY_ID'],
#     aws_secret_access_key=APP.config['AWS_SECRET_ACCESS_KEY'],
#     endpoint_url='https://objectstore.e2enetworks.net',
# )
bucket_name = ''
s3_client = boto3.client(
    's3',
    aws_access_key_id='',
    aws_secret_access_key='',
    endpoint_url='',
)

def policy_remarks_validator(value):
    POLICY_REMARKS = {
        'ID': {'required': True, 'type': 'string'},
        'CONDITIONS': {'required': True, 'type': 'string'},
        'REMARKS': {'required': True, 'type': 'string'}
    }
    v = Validator(POLICY_REMARKS)
    if v.validate(value):
        return value
    else:
        raise ValueError(json.dumps(v.errors))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in APP.config['ALLOWED_EXTENSIONS']


def endorsement_validator(value):
    POLICY_REMARKS = {
        'ID': {'required': True, 'type': 'string'},
        'ENDORSEMENT_NO': {'required': True, 'type': 'string'},
        'ENDORSEMENT_NAME': {'required': True, 'type': 'string'},
        'REMARKS': {'required': True, 'type': 'string'}
    }
    v = Validator(POLICY_REMARKS)
    if v.validate(value):
        return value
    else:
        raise ValueError(json.dumps(v.errors))

def string_difference(str1, str2):
    count = 0
    if len(str1) == len(str2):
        for i in range(len(str1)):
            if str1[i] != str2[i]:
                count += 1
        return count
    return None

def rectify_date(str1, date_format="%d/%m/%Y"):
    print('9999999999', str1)
    str1 = re.sub(' J01 ', ' 07 ', str1)
    mintp = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'apv': '04', 'may': '05', 'jun': '06', 'jul': '07',
             'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12', 'JAN': '01', 'FEB': '02', 'MAR': '03',
             'APR': '04', 'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11',
             'DEC': '12', 'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07',
             'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12', 'january': '01', 'february': '02',
             'march': '03', 'april': '04', 'may': '05', 'june': '06', 'july': '07', 'august': '08', 'september': '09',
             'october': '10', 'november': '11', 'december': '12', 'JANUARY': '01', 'FEBRUARY': '02', 'MARCH': '03',
             'APRIL': '04', 'MAY': '05', 'JUNE': '06', 'JULY': '07', 'AUGUST': '08', 'SEPTEMBER': '09', 'OCTOBER': '10',
             'NOVEMBER': '11', 'DECEMBER': '12', 'January': '01', 'February': '02', 'March': '03', 'April': '04',
             'May': '05', 'June': '06', 'July': '07', 'August': '08', 'September': '09', 'October': '10',
             'November': '11', 'December': '12', "ocr": "10", "our": "10", "0lr": "11", ")ito": "11", 'ocx': '10',
             'Ap1': '04'}
    wintp = {'s': '5', 'Z': '2', 'T': '1', 'S': '5', 'R': '2', 'Q': '0', 'O': '0', 'A': '4', 'G': '6', 'H': '4',
             'a': '2', 'o': '0', 'y': '4', 'z': '2', 'f': '5', 't': '1', 'b': '6', 'F': '5', 'B': '8', 'L': '1',
             'C': '0', 'D': '1', 'l': '1', 'I': '1', 'i': '1', 'j': '1', 'J': '7', 'P': '9', 'd': '0'}
    dob2 = ''
    dob3 = ''
    dob = ''
    year = ''
    datmon = ''
    Date = ''
    t3 = 0
    punm = ['.', '/', '-', ',', '!', ' ', '+', '*', '@', '#', "(", ")"]
    # print(str1[-1])
    str1 = str1.replace(' ', '', 9)
    # print(str1)
    if len(str1) == 11 and str1[2] == '/' and str1[-1] == '1' and int(str1[6:10]) in range(1945, 2022):
        str1 = str1[:10]
    if len(str1) == 9 and str1.isdigit() == True and str1[5:7] == '20' and int(str1[0:2]) < 32 and str1[2] == '1' and \
            str1[4] == '1' and str1[3] != 0:
        str1 = str1[0:2] + '/' + str1[3] + '/' + str1[5:9]
    if len(str1) == 7 and str1[2] == '/' and (str1[3:6]).isdigit() == True and str1[6] == ')':
        if int(str1[:2]) < 32 and int(str1[3:5]) < 13:
            str1 = str1.replace(')', '1', 9)
            str1 = str1[:5] + '/' + str1[5:]
    if len(str1) == 7 and str1[2] == '/' and str1[3].isdigit() == True and str1[4] == '/':
        str1 = str1[:3] + '0' + str1[3:]
    if len(str1) == 7 and str1[2] == '.' and str1[:2].isdigit() == True and str1[3:5].isdigit() == True and str1[
        5] == '.' and int(str1[3:5]) < 13 and str1[6] == '2':
        str1 = str1 + '020'
    if len(str1) == 9 and str1[5:9].isdigit() == True and int(str1[5:9]) > 1950 and str1[:2].isdigit() == True and int(
            str1[:2]) <= 31 and str1[4] == '/' and str1[3].isdigit() and str1[3] != 0 and str1[2] == '1':
        str1 = str1[:2] + '/' + str1[3:]
    if len(str1) == 8 and str1[:2].isdigit() == True and int(str1[:2]) <= 31 and str1[2:4].isdigit() == True and int(
            str1[2:4]) <= 12 and str1[4:6] == '20':
        str1 = str1[:2] + '/' + str1[2:4] + '/' + str1[4:]
    # print(str1)
    if len(str1) == 7 and str1[1] == '/' and str1[2:4].isdigit() and int(str1[2:4]) <= 12 and str1[4] == '1' and str1[
                                                                                                                 5:7].isdigit() and int(
            str1[5:7]) > 50:
        str1 = str1[:4] + '/' + str1[5:7]
    if len(str1) == 10 and str1[2] == '/' and str1[5] == '/' and (
            str1[:2].isdigit() == True and str1[3:5].isdigit() == True and str1[6:].isdigit() == True) and int(
            str1[8:]) > 70:
        str1 = str1[:6] + '19' + str1[8:]
    if len(str1) == 10 and str1[2] == '/' and str1[5] == '1' and (
            str1[:2].isdigit() == True and str1[3:5].isdigit() == True and str1[6:].isdigit() == True) and (
            int(str1[6:8]) == 19 and int(str1[8:]) > 40):
        str1 = str1[:5] + '/' + str1[6:]
    if len(str1) == 10 and str1[2] == '/' and str1[5] == '/' and (
            str1[:2].isdigit() == True and str1[3:5].isdigit() == True) and str1[6:9].isdigit() == True and str1[
        9] == ')' and str1[6:8] == '29':
        str1 = str1[:6] + '19' + str1[8] + '1'
    if len(str1) == 10 and str1[2] == '+' and str1[5] == '+' and (
            str1[:2].isdigit() == True and str1[3:5].isdigit() == True and str1[6:9].isdigit() == True) and str1[
        9] == '/':
        str1 = str1[:9] + '1'
    if len(str1) == 10 and str1[3] in punm and str1[6] in punm and str1[:3].isdigit() == True and str1[
                                                                                                  7:].isdigit() == True:
        str1 = str1[1:]
        str1 = str1[:6] + '20' + str1[7:]
    if len(str1) == 10 and str1[1] in punm and str1[5] in punm and str1[2:5].isalpha() == True and str1[
                                                                                                   2:5] in mintp and str1[
                                                                                                                     6:].isdigit() == True and \
            str1[0] == '0':
        str1 = '1' + str1
    if len(str1) == 11 and str1[:6].isdigit() == True and str1[6] == '/' and str1[7:].isdigit() == True and str1[
        2] == '1' and str1[3] == '1' and str1[7:9] == '19' and int(str1[:2]) < 32 and int(str1[4:6]) < 13:
        str1 = str1[:2] + str1[4:]
    if len(str1) == 12 and str1[:2].isdigit() == True and str1[2] == str1[7] == '/' and str1[8:10] == '19' and str1[
                                                                                                               10:].isdigit() == True and \
            str1[3] == str1[6] == '1' and str1[4:6].isdigit() == True:
        str1 = str1[:2] + '/' + str1[4:6] + '/' + str1[8:]
    if len(str1) == 6 and str1[1] == '0' and str1[3] in ['/', '|', '-', '_']:
        str1 = str1[:2] + '/0' + str1[2:]

    dob1 = str1
    for i in mintp:
        if i in dob1:
            dob2 = dob1.replace(i, mintp[i])
    if len(dob2) == 0:
        dob2 = dob1
    x = dob2.rfind('/')
    if len(dob2[x + 1:]) == 3 and (dob2[x + 1:]).isdigit() == True:
        if dob2[x + 1:] == '202' or dob2[x + 1:] == '220':
            year = '2020'
        for char in dob2[:x]:
            if char in wintp:
                datmon += wintp[char]
            elif char.isdigit() == True:
                datmon += char
        datmon3 = datmon
        datmon = ''
        # print(datmon3)
        for char in datmon3:
            if char not in punm:
                datmon += char
        t3 = 1
    if len(dob2[x + 1:]) == 4 and (dob2[x + 4]).isdigit() == False:
        if dob2[x + 1:] == '202' or dob2[x + 1:] == '220':
            year = '2020'
        for char in dob2[:x]:
            if char in wintp:
                datmon += wintp[char]
            elif char.isdigit() == True:
                datmon += char
        datmon3 = datmon
        datmon = ''
        for char in datmon3:
            if char not in punm:
                datmon += char
        t3 = 1

    if t3 == 0:
        for char in dob2:
            if char in wintp:
                dob3 += wintp[char]
            elif char.isdigit() == True:
                dob3 += char
        for char in dob3:
            if char not in punm:
                dob += char
        # print(f"dob : {dob}")
        b = 0
        datmon = dob[:2]
        for k in range(4):
            if k == 0:
                for i in range(1940, 2029):
                    if str(i) in dob[2:]:
                        year = str(i)
                        datmon1 = dob[2:].split(str(i))[0]
                        datmon += datmon1
                        b = 1
                        break
            if b == 1:
                break
            if k == 1:
                for i in range(40, 99):
                    if str(i) in dob[2:]:
                        if len(dob[2:].split(str(i))[-1]) == 0:
                            year = str(i)
                            datmon1 = dob[2:].split(str(i))[0]
                            datmon += datmon1
                            b = 1
                            break
            if b == 1:
                break
            if k == 2:
                for i in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09']:
                    if str(i) in dob[2:]:
                        if len(dob[2:].split(str(i))[-1]) == 0:
                            year = str(i)
                            datmon1 = dob[2:].split(str(i))[0]
                            datmon += datmon1
                            b = 1
                            break
            if b == 1:
                break
            if k == 3:
                for i in range(10, 29):
                    if str(i) in dob[2:]:
                        if len(dob[2:].split(str(i))[-1]) == 0:
                            year = str(i)
                            datmon1 = dob[2:].split(str(i))[0]
                            datmon += datmon1
                            b = 1
                            break
            if b == 1:
                break
        # print(year)
        if len(year) == 0 and len(dob) == 6:
            year = dob[3:5]
            datmon = dob[:3]
        if len(year) == 2:
            if int(year) > 40:
                year = '19' + year
            elif int(year) < 40:
                year = '20' + year
    month = ''
    date = ''
    if t3 == 1:
        year = '2020'
    if len(datmon) > 4 and datmon.isdigit() == True:
        if len(datmon) == 5 and datmon.isdigit() == True and datmon[2] == '1':
            if int(datmon[3:]) < 13 and int(datmon[:2]) < 32:
                date = datmon[:2]
                month = datmon[3:]
                if int(month) == 2 and int(date) > 27:
                    date = ''
        else:
            if int(datmon[-2:]) < 13 and int(datmon[-4:-2]) < 32:
                date = datmon[-4:-2]
                month = datmon[-2:]
                if int(date) == 0:
                    date = ''
                if int(month) == 0:
                    month = ''
    if len(datmon) == 4 and datmon.isdigit() == True:
        if int(datmon[2:]) < 13 and int(datmon[:2]) < 32:
            date = datmon[:2]
            month = datmon[2:]
            if int(date) == 0:
                date = ''
            if int(month) == 0:
                month = ''
            if int(month) == 2 and int(date) > 27:
                date = ''
        elif int(datmon[2:]) > 13 and int(datmon[:2]) < 32:
            date = datmon[:2]
            month = '0' + datmon[3]
            # if int(date)==0:
            #     date=''
            if int(month) == 0:
                month = ''
            if int(month) == 2 and int(date) > 27:
                date = ''
        elif int(datmon[2:]) < 13 and int(datmon[:2]) > 32:
            date = '30'
            month = datmon[2:]
            if int(date) == 0:
                date = ''
            if int(month) == 0:
                month = ''
            if int(month) == 2 and int(date) > 27:
                date = ''
    if len(datmon) == 3 and datmon.isdigit() == True:
        if int(datmon[1:]) < 13:
            if datmon[1] == '0':
                date = '0' + datmon[0]
                month = datmon[1:]
                # if int(date)==0:
                #     date=''
                if int(month) == 0:
                    month = ''
                # if int(month)==2 and int(date)>27:
                #     date=''
            elif int(datmon[:2]) < 32:
                date = datmon[:2]
                month = '0' + datmon[2]
                if int(date) == 0:
                    date = ''
                # if int(month)==0:
                #     month=''
                # if int(month)==2 and int(date)>27:
                #     date=''
            else:
                date = '0' + datmon[0]
                month = datmon[1:]
                # if int(date)==0:
                #     date=''
                if int(month) == 0:
                    month = ''
                # if int(month)==2 and int(date)>27:
                #     date=''
        elif int(datmon[1:]) > 13 and int(datmon[:2]) < 32:
            date = datmon[:2]
            month = '0' + datmon[2]
            if int(date) == 0:
                date = ''
            if int(month) == 0:
                month = ''
            # if int(month)==2 and int(date)>27:
            #     date=''
    if len(datmon) == 2 and datmon.isdigit() == True:
        date = '0' + datmon[0]
        month = '0' + datmon[1]
        if int(date) == 0:
            date = ''
        if int(month) == 0:
            month = ''
    Date = date + "/" + month + "/" + year
    modified_date = Date
    try:
        import datetime
        if type(year)==str and type(month)==str and type(date)==str:
            modified_date = datetime.datetime(year=int(float(year)), month=int(float(month)), day=int(float(date))).strftime(date_format)
    except Exception as e:
        LOG.error("Error while changing the date format")
        LOG.error(e, exc_info=True)
        modified_date = ""
    if len(date) == len(month) == len(year) == 0:
        Date = ''
    return modified_date


def is_valid(or_inclusion="", and_inclusion="", and_exclusion="", line_item: dict = None, key="", category="", algorithm=""):
    if line_item is None:
        line_item = deepcopy({})
    or_inclusion = or_inclusion.split(",")
    and_inclusion = and_inclusion.split(",")
    and_exclusion = and_exclusion.split(",")
    key = str(line_item) + key
    print('or_inclusion',or_inclusion)
    print('and_inclusion',and_inclusion)
    print('and_exclusion',and_exclusion)
    print('key',key)

    if algorithm == "room":
        key = str(key).replace("/", "")
    result = False
    for word in and_exclusion:
        if word == "":
            continue
        if word in str(key).lower().replace(" ", ""):
            print(64, word, key)
            return False


    for word in and_inclusion:
        if word == "":
            continue
        if word not in str(key).lower().replace(" ", ""):
            print(70, word, key)
            print('ddkdkkd', and_inclusion,word)
            # print(beds, room, line_item)

            return False
    for word in or_inclusion:
        if word == "":
            result = True
            continue
        if word in str(key).lower().replace(" ", ""):
            return True
    print(or_inclusion, result)

    return result


def strip_non_ascii(normal_string):
    """ Returns the string without non ASCII characters"""
    stripped = (c for c in normal_string if 0 < ord(c) < 127)
    return ''.join(stripped)


def remove_file_after_wait(file_path):
    time.sleep(10)
    if os.path.exists(file_path):
        os.remove(file_path)


def word_in_both(str1, str2, word):
    return (word.lower() in str1.lower() and word.lower() in str2.lower()) or (word.lower() not in str1.lower() and word.lower() not in str2.lower())

# def text_concat(json_data):
#     json_data=json_data.get('lines')
#     print('json_data',json_data)
#     text = " ".join([str(json_data[i].get('text')) for i in range(len(json_data))])
#     return text
#


def text_concat(json_data):
    text = " ".join([str(text.get('text')) for text in json_data])

    return text


def get_random_characters(string_length=3):
    return ''.join(random.choice(string.ascii_letters) for x in range(string_length))


def get_random_numbers(string_length=3):
    return ''.join(random.choice(string.digits) for x in range(string_length))


def send_mail(to_address: str, body: str, subject: str, msg_id=None, files=None):
    if not APP.config["SEND_MAILS"]:
        return
    smtpObj = smtplib.SMTP(APP.config["SMTP_SERVER"], port=APP.config["SMTP_PORT"])
    print(smtpObj)
    print(APP.config["SMTP_SERVER"])
    if str(APP.config["SMTP_SERVER"]).lower().__contains__("office365"):
        smtpObj.starttls()
    password = Encryption().decrypt(APP.config["PASS"])
    smtpObj.login(APP.config["EMAIL"], password)
    body += "<p>Regards,</p><p>iAssist BOT</p>"
    msg = MIMEMultipart()
    msg['subject'] = subject
    msg['from'] = APP.config["EMAIL"]
    msg['to'] = to_address
    msgtext1 = MIMEText(
        body, 'html')
    if bool(msg_id):
        msg = create_reply(msg_id, msg)
    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)
    LOG.debug(str(msg))
    msg.attach(msgtext1)
    smtpObj.send_message(msg,APP.config["EMAIL"], to_address)
    LOG.info(f"Mail sent to {to_address} \n {body}")


# def create_reply(msg_id, msg):
#     imap = imaplib.IMAP4_SSL(APP.config["IMAP_SERVER"])
#     password = Encryption().decrypt(APP.config["PASS"])
#     imap.login(APP.config["EMAIL"], password)
#     try:
#         imap.select(APP.config['MAIL_SEARCH_DIR'])
#         typ, data = imap.uid('SEARCH', None, '(HEADER Message-ID %s)' % msg_id)
#         # typ, data = imap.search(None, 'ALL')
#         # print(data)
#         ids_list = data[0].split()
#         if not len(ids_list) > 0:
#             return msg
#         num = ids_list[0]
#         print(num)
#         typ1, data1 = imap.uid('fetch', num, '(RFC822)')
#         # print(typ1)
#         # print(data1)
#         # if data1 == [None]:
#         #     continue
#         # print(data1[0])
#         original = email.message_from_string(data1[0][1].decode('utf-8'))
#         for part in original.walk():
#             if (part.get('Content-Disposition')
#                     and part.get('Content-Disposition').startswith("attachment")):
#                 part.set_type("text/plain")
#                 part.set_payload("Attachment removed: %s (%s, %d bytes)"
#                                  % (part.get_filename(),
#                                     part.get_content_type(),
#                                     len(part.get_payload(decode=True))))
#                 del part["Content-Disposition"]
#                 del part["Content-Transfer-Encoding"]
#         # msg["Message-ID"] = email.utils.make_msgid()
#         msg["In-Reply-To"] = original["Message-ID"]
#         msg["References"] = original["Message-ID"]
#         msg["Subject"] = "Re: " + original["Subject"]
#         msg["To"] = original["Reply-To"] or original["From"]
#
#         return msg
#     except Exception as e:
#         LOG.error("Error while sending a reply")
#         LOG.error(e, exc_info=True)
#     return msg

def create_reply(msg_id, msg):
    mail_id = APP.config["EMAIL"]
    password = Encryption().decrypt(APP.config["PASS"])
    credentials = Credentials(mail_id, password)
    server = ''
    config = Configuration(server=server, credentials=credentials)
    account = Account(mail_id, credentials=credentials, autodiscover=False, config=config, access_type=DELEGATE)
    try:
        inbox_data = account.inbox / 'icici_mails'
        inbox_data = inbox_data.filter(message_id=msg_id)
        print(inbox_data)
        Number_of_mails = inbox_data.filter(is_read=False).count()
        if not Number_of_mails > 0:
            return msg
        part=inbox_data[0]
        #print('data',part)
        # for attachment in part.attachments:
        #     part.detach(attachment)
        msg["Message-ID"] = email.utils.make_msgid()
        msg["In-Reply-To"] = part.message_id
        msg["References"] = part.message_id
        msg["Subject"] = "Re: " + part.subject
        msg["To"] = part.sender.email_address
        return msg
    except Exception as e:
        LOG.error("Error while sending a reply")
        LOG.error(e, exc_info=True)
    return msg

def remove_special_characters(t):
    print(t,'ttttt')
    if t == None:
        return None
    return re.sub("[^A-Za-z0-9 _]","",t)


def upload_to_aws(local_path, s3_prefix):
    bucket_name = APP.config['S3_BUCKET']
    s3 = boto3.client(
        's3',
        aws_access_key_id=APP.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=APP.config['AWS_SECRET_ACCESS_KEY'],
        endpoint_url='',
    )


    print('Uploading:', local_path, 'to', s3_prefix)

    try:
        for root, dirs, files in os.walk(local_path):
            for file in files:
                local_file = os.path.join(root, file)
                s3_file = os.path.join(s3_prefix, os.path.relpath(local_file, local_path))
                s3.upload_file(local_file, bucket_name, s3_file)
                print('Uploaded:', local_file, 'as', s3_file)

        print('Upload Successful')
        return True
    except FileNotFoundError:
        print('The file was not found')
        return False
    except NoCredentialsError:
        print('Credentials not available')
        return False

def image_sas_url(claim_number):
    combined_url = []
    session = boto3.Session(
        aws_access_key_id = APP.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key = APP.config['AWS_SECRET_ACCESS_KEY'],
    )
    s3 = session.client('s3', verify=False)
    bucket_name = APP.config['S3_BUCKET']
    resp = s3.list_objects_v2(Bucket=bucket_name, Prefix=str(claim_number))
    for i in range(len(resp.get('Contents'))):
        key = resp.get('Contents')[i].get('Key')
        if str(key).__contains__(claim_number) and str(key).replace('/', "") != claim_number:
            location = 'ap-south-1'
            s3_client = boto3.client(
                's3',
                region_name=location,
                aws_access_key_id="",
                aws_secret_access_key="",
            )
            url = s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': bucket_name, 'Key': key, },
                ExpiresIn=100,
            )
            combined_url.append(url)
    return combined_url


# resp = s3_client.list_objects_v2(Bucket="medicalproject", Prefix="jsons/2206202313023737053/")
# for i in range(len(resp.get('Contents'))):
#     key = resp.get('Contents')[i].get('Key')
#     print(key)

def get_file_from_s3(object_key):
    resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=object_key)
    content = resp.get('Contents',[])
    all_keys = []
    if content:
        for i in range(len(resp.get('Contents'))):
            key = resp.get('Contents')[i].get('Key')
            all_keys.append(key)
    return all_keys


def copy_files_from_s3(object_key, file_name, backup_filename):
    key = object_key + file_name
    backup_key = object_key + backup_filename
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    file_content = response['Body'].read()

    with open(backup_filename, 'wb') as file:
        file.write(file_content)
    s3_client.upload_file(backup_filename, bucket_name, backup_key)
    os.remove(backup_filename)

def download_file_from_s3_to_local(file_key,file_location):
    # s3_client.download_file("medicalproject", i, abs_path + (i.split("/")[-1]))
    s3_client.download_file("medicalproject", file_key, file_location)


def upload_file_to_s3(objectkey, local_file_path, filename):
    key = objectkey + filename
    s3_client.upload_file(local_file_path, bucket_name, key)
    print(f"{filename} updated to s3")


def get_data_from_s3(object_key, file_name):
    key = object_key + file_name
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    file_content = response['Body'].read()
    return file_content


def copy_final_data_to_json(object_key, file_name, final_bill_data):
    key = object_key + file_name

    if file_name.split(".")[-1] == "json":
        modified_json_str = json.dumps(final_bill_data)
    else:
        modified_json_str = final_bill_data

    modified_json_str = json.dumps(final_bill_data)
    s3_client.put_object(
        Body=modified_json_str,
        Bucket=bucket_name,
        Key=key
    )

    print("copy final data to json is done")


def get_presigned_url(object_key, file_name, expire_time=100,pdf_content=False):
    # objectkey should be folder/claimid/
    file_key = object_key + file_name
    if pdf_content:
        url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket_name, 'Key': file_key, 'ResponseContentType': 'application/pdf' },
            ExpiresIn=expire_time,
        )
    else:
        url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket_name, 'Key': file_key, },
            ExpiresIn=expire_time,
    )
    return url

room_type_picked_from_api = ""
def set_room_type_from_api(value):
    global room_type_picked_from_api
    room_type_picked_from_api = value

def get_room_type_from_api(default_value=""):
    global room_type_picked_from_api
    return room_type_picked_from_api or default_value

def finalListtoBilljson(input_data):
    # maincategory_value = input_data[0]['maincategory'].split('~~')[1]
    
    output_data = {}
    

    for key, item in input_data[0]['final_list'].items():
        new_category = item['new_category'].split('~~')[1]
        if new_category not in output_data:
            output_data[new_category] = {}
            current_key = 1
        output_data[new_category][current_key] = {
            'Item': item['finalparticular'],
            'Qty': item['noOfUnits'],
            'Rate': item['tariffcost'],
            'Amount': item['bill_calculated'],
            'Datetime': item['date'],
        }
        
        current_key += 1
    
    # Calculate the sum of Rate and Amount values
    # rate_sum = sum(float(item['tariffcost']) for item in input_data[0]['final_list'].values())
    # amount_sum = sum(float(item['bill_calculated']) for item in input_data[0]['final_list'].values())

    # output_data[maincategory_value][str(len(input_data[0]['final_list']) + 1)] = {
    #     "DateTime": "Sub Total",
    #     "Rate": f"{rate_sum:.2f}",
    #     "Amount": f"{amount_sum:.2f}"
    # }
    return output_data


def remove_bounding_box(json_obj):
    if isinstance(json_obj, dict):
        if "bounding_box" in json_obj:
            del json_obj["bounding_box"]
        for key, value in json_obj.items():
            json_obj[key] = remove_bounding_box(value)
    elif isinstance(json_obj, list):
        for i in range(len(json_obj)):
            json_obj[i] = remove_bounding_box(json_obj[i])
    return json_obj


def get_auth_token():
  url = ""

  payload = json.dumps({
    "username": "",
    "password": ""
  })
  headers = {
    'Content-Type': 'application/json',
    'Cookie': 'session=eyJfcGVybWFuZW50Ijp0cnVlfQ.ZeavDw.73CGVI2JiL7lbaZieHHuufYrmqI'
  }

  response = requests.request("POST", url, headers=headers, data=payload)
  if response.status_code == 200:
      data = response.json()
      token = data['access_token']
  return token


def get_classification(file_path):
    token = get_auth_token()
    url = ""

    payload = {'type_id': 'medical'}
    files = [
        ('file[]', (file_path.split('/')[-1], open(file_path, 'rb'), 'application/pdf'))
    ]
    headers = {
        'Authorization': f'JWT {token}'
    }

    response = requests.post(url, headers=headers, data=payload, files=files)
    if response.status_code == 200:
        data = response.json()

        filename = os.path.basename(file_path)

        dir_name = os.path.dirname(file_path).replace('\\', '/')
        dir_name = dir_name.replace('uploads/', '')
        dir_name = dir_name.replace('/', '')

        key = f"{dir_name}{filename}"
        doc_classification_key = f"{dir_name}{filename}_1"

        value = data.get(key, {}).get('documents_classification', {}).get(doc_classification_key)
        print(value)
    return value


class PdfToImage ():
    @staticmethod
    def pdf_to_img(pdf_file_path, download_folder, folder_name, index):
        images = convert_from_path(pdf_file_path)
        i = index
        for image in images:
            file_path_im = os.path.join(download_folder, folder_name, f"{folder_name}{i}.jpg")
            i += 1
            if not os.path.exists(file_path_im):
                os.makedirs(os.path.dirname(file_path_im), exist_ok=True)

            # Save the image as JPEG
            image.save(file_path_im, 'JPEG')

            # Start the thread to save the image
            threading.Thread(target=image.save, args=(file_path_im, 'JPEG')).start()

        return len(images)
    

def ms_icr(filepath):
    endpoints = ["",
                 ""]
    for url in endpoints:
        try:
            payload = {}
            files = [
                ('file_upload', (os.path.join(filepath),
                 open(filepath, 'rb'), 'image/jpeg'))
            ]
            headers = {}
            response = requests.request(
                "POST", url, headers=headers, data=payload, files=files)
            data = response.json()
            lines = data['lines']
            lines_data = data.get('lines', [])
            return lines
 
        except requests.exceptions.RequestException as error:
            pass
            # LOG.info(f"New ICR Endpoint {url} error: {error}")
    return {"error": "All New ICR Endpoints Are Down"}