import threading , queue
import time
from flask import request, Blueprint, jsonify, send_file, render_template, redirect, url_for,make_response
import flask, flask_login, os, re, datetime, ast, uuid, json, threading
from flask import session
from werkzeug.utils import secure_filename
from portal import create_app
from portal.packages.intelligence import unzipping_file, classification_logic, select_interpretation_config, main_interpretation_run
from google.cloud import firestore
from portal.packages.rule_response import get_prompt
from pdf2image import convert_from_path
from PIL import Image
import sys
from os.path import basename
import cv2
import json
from docx import Document
from io import BytesIO
from bs4 import BeautifulSoup

# from firebase import firebase
# import firebase_admin
# from firebase_admin import credentials , firestore


# config = {
#     "apiKey": "AIzaSyAmK6i6Uo96yMzdJ0y_bDG9qXeMEFviwdM",
#     "authDomain": "conffigurator-94278.firebaseapp.com",
#     "projectId": "configurator-94278",
#     "storageBucket": "configurator-94278.appspot.com",
#     "messagingSenderId": "1058344132866",
#     "appId": "1:1058344132866:web:e39872d1e18fb6183e621b",
#     "measurementId": "G-0BKV6LTGFG"
# }

# firebase = firebase(config)


import firebase_admin
from firebase_admin import credentials , firestore
from .helpers import get_file_from_s3, upload_file_to_s3, PdfToImage, get_classification, ms_icr, remove_bounding_box, text_concat

app = create_app()

# file_path = r'C:\Users\rochi\Downloads\configurator_ui\portal\configurator-94278-firebase-adminsdk-9ot57-e0014d1ed8.json'
file_path = os.getcwd() + "/portal/configurator-94278-firebase-adminsdk-9ot57-e0014d1ed8.json"
cred = credentials.Certificate(file_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return None
    
def get_rule_data_by_id(ref_id, file_path):
    data = read_json_file(file_path)
    if data:
       return data
    return None

bp = Blueprint("for_demo", __name__, url_prefix='/configurator', template_folder='./templates', static_folder='./static')



@bp.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    r.headers["server"] = ""
    return r


@bp.before_request
def before_request():
    flask.session.permanent = True
    bp.permanent_session_lifetime = datetime.timedelta(minutes=10)
    flask.session.modified = True
    flask.g.user = flask_login.current_user


@bp.route('/', methods=["GET", "POST"])
def index():
    if request.method == "OPTIONS":
        return 403
    else:
        all_files = os.listdir(str(app.config['RULE_JSON']))
        print(all_files)
        ref_no, ref_name, ref_date, ref_status = [], [], [], []
        for i in range(len(all_files)):
            json_file = str(app.config['RULE_JSON']) + "/" + str(all_files[i])
            if str(json_file).__contains__(".json"):
                f = open(json_file)
                data = json.load(f)
                ref_no.append(data["ref_id"])
                ref_name.append(data["rule_name"])
                ref_date.append(data["rule_created"])
                if str(data["rule_status"]) == "active":
                    # ref_status.append('<div class="badge badge-opacity-success">Active</div>')
                    ref_status.append('checked')
                else:
                    ref_status.append('')
        ret_data = {
            "ref_no": ref_no,
            "ref_name": ref_name,
            "ref_date": ref_date,
            "ref_status": ref_status,
        }
        

        return render_template("main.html", ret_data=ret_data)




# @bp.route('/create_rule', methods=["GET", "POST"])
# def create_rule():
#     if request.method == "OPTIONS":
#         return 403
#     else:
#         all_files = os.listdir(str(app.config['INT_JSON']))
#         print(all_files)
#         int_type = []
#         for i in range(len(all_files)):
#             json_file = str(app.config['INT_JSON']) + "/" + str(all_files[i])
#             if str(json_file).__contains__(".json"):
#                 int_type.append(str(all_files[i]).replace(".json", ""))
        
        
#         collection_ref = db.collection('rules')
#         documents = collection_ref.stream()

#         firestore_data = []
#         for doc in documents:
#             firestore_data.append(doc.to_dict())

#         ret_data = {
#             "int_type": int_type,
#             "firestore_data": firestore_data
#         }
#         print("!!!!!!!!!!!!!!!!!success!!!!!!!!!!!!!!!!!!")
#         # ret_data = {
#         #     "int_type": int_type
#         # }
#         return render_template("create_rule.html", ret_data=ret_data)


@bp.route('/update_rules/<ref_id>', methods=["GET", "POST"])
@bp.route('/update_rules', methods=["GET", "POST"], defaults={'ref_id': None})
def update_rules():
    data = request.json()
    print(f"the data here is {data}")

@bp.route('/configurator/edit_rule/<string:ref_id>', methods=['GET', 'POST'])
def edit_rule(ref_id):
    rule_data = get_rule_data_by_id(ref_id,f"E:\projects\configurator-UI-demo\\rule_json\{ref_id}.json")  # Function to get rule data
    all_doc_types = ["generic", "discharge summary", "pharmacy bill", "lab report", "pre auth", "bills", "policy"]  # List all possible document types
    print(rule_data,"cehck rule dataaaaaa")
    return render_template('edit_rule.html', rule_data=rule_data, all_doc_types=all_doc_types)

# new code 


@bp.route('/create_rule/<ref_id>', methods=["GET", "POST"])
@bp.route('/create_rule', methods=["GET", "POST"], defaults={'ref_id': None})
def create_rule(ref_id):
    if request.method == "OPTIONS":
        return 403
    else:
        all_files = os.listdir(str(app.config['INT_JSON']))
        print(all_files)
        int_type = []
        for i in range(len(all_files)):
            json_file = str(app.config['INT_JSON']) + "/" + str(all_files[i])
            if str(json_file).__contains__(".json"):
                int_type.append(str(all_files[i]).replace(".json", ""))

        # Retrieve data from Firestore for the specified ref_id
        doc_ref = db.collection('rules').document(ref_id)
        doc = doc_ref.get()
        firestore_data = doc.to_dict() if doc.exists else {}
        print(f"firestore data ->  {firestore_data}" )
        ret_data = {
            "int_type": int_type,
            "firestore_data": firestore_data
        }

        return render_template("create_rule.html", ret_data=ret_data)



# new code 

@bp.route('/create_int', methods=["GET", "POST"])
def create_int():
    if request.method == "OPTIONS":
        return 403
    else:
        return render_template("create_int.html")


@bp.route('/createPDF', methods=["GET", "POST"])
def createPDF():
    if request.method == "OPTIONS":
        return 403
    else:
        folder_path = app.config['RULE_JSON']
        json_files = [os.path.splitext(f)[0] for f in os.listdir(folder_path) if f.endswith('.json')]
        return render_template("createPDF.html", json_files=json_files)



@bp.route('/final_create_rule', methods=["GET", "POST"])
def final_create_rule():
    data_final_json = {}
    rule_json = {}
    doc_type_json = {}
    type_json = {}
    if request.method == "OPTIONS":
        return 403
    else:
        try:
        
            data = ast.literal_eval(request.get_data().decode("utf-8"))
            print(data,"cehkkkkk sttuss")
        
            # app = create_app()
            
            ref_id = str(uuid.uuid4())
            final_json = {}
            final_all_json = {}
            for i in range(len(data[0])):
                temp_json = {}
                for j in range(len(data[1][i])):
                    temp_json[str(data[1][i][j])] = data[2][i]
                final_json[data[0][i]] = temp_json
            print(final_json,"lets ee this")
            final_all_json["data"] = final_json
            final_all_json["ref_id"] = ref_id
            final_all_json["rule_name"] = str(data[3]) or str(data[2])
            final_all_json["rule_status"] = "active"
            final_all_json["rule_created"] = str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            with open(str(app.config['RULE_JSON']) + "/" + str(final_all_json["rule_name"]) + '.json', 'w') as f:
                json.dump(final_all_json, f)
            print(final_all_json)
            data_final_json = final_all_json["data"]
            print(data_final_json,'gotchaaa')
            i = 0
            
            for rule_key,rule_valuess in data_final_json.items():
                i = i + 1
                rule_json[f"doc_type_{i}"] = rule_key
                f = 0
                d = 0
                type_json = rule_valuess
                for rule_key1,rule_values1 in type_json.items():
                    
                    print(rule_values1,"check the document types")
                    for rule_value1 in rule_values1:
                        d = d+1 
                        rule_json[f"data_type_{i}_{d}"] = rule_value1
                for rule_values in rule_valuess:
                    print(rule_values,"got rules ")
                    f = f + 1
                    rule_json[f"data_{i}_{f}"] = rule_values
            print(rule_json, "check whats this ")
                    # for rule_vale in rule_values:
                    #     print(rule_vale,"check the doctyep")
                
            return redirect(url_for('for_demo.index'))
        except:
            data = ast.literal_eval(request.get_data().decode("utf-8"))
            rule_name = data["rule_name"]
            print(rule_name,"cehck rule anme ")
            data = data["data"]
            
            print(data,"cehck data after edit")
            ref_id = str(uuid.uuid4())
            final_json = {}
            final_all_json = {}

            # Iterate over each document type and its conditions
            for doc_type, conditions in data.items():
                temp_json = {}

                # Iterate over each condition and its badges
                for condition, badges in conditions.items():
                    # Directly assign the list of badges to the condition
                    temp_json[condition] = badges

                final_json[doc_type] = temp_json

            final_all_json["data"] = final_json
            final_all_json["ref_id"] = ref_id
            final_all_json["rule_name"] =  rule_name
            final_all_json["rule_status"] = "active"
            final_all_json["rule_created"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            # Write the final JSON to a file
            with open(f"{app.config['RULE_JSON']}/{final_all_json['rule_name']}.json", 'w') as f:
                json.dump(final_all_json, f, indent=4)
            
                
            return redirect(url_for('for_demo.index'))



# @bp.route('/final_create_int', methods=["GET", "POST"])
# def final_create_int():
#     if request.method == "OPTIONS":
#         return 403
#     else:
#         data = ast.literal_eval(request.get_data().decode("utf-8"))
#         print("the data here is  -> " , data)
        
#         ref_id = str(uuid.uuid4())
#         file_name = str(data[3]).replace(" ", "_")
#         final_json = {}
#         final_detailed_json = {}
#         final_all_json = {}
#         for i in range(len(data[0])):
#             temp_json = {}
#             for j in range(len(data[1][i])):
#                 temp_json[str(data[1][i][j])] = str(data[2][i][j])
            
#             final_json[data[0][i]] = temp_json 
#         final_all_json["data"] = final_json
#         final_all_json["ref_id"] = ref_id
#         final_all_json["int_name"] = str(data[3])
#         final_all_json["int_status"] = "active"
#         final_all_json["int_created"] = str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
#         with open(str(app.config['INT_JSON']) + "/" + str(file_name) + '.json', 'w') as f:
#             json.dump(final_all_json, f)
        
#         doc_ref = db.collection('configurator-interpretation').document(ref_id)
#         doc_ref.set(final_all_json)
        
#         print(f"the data is sent to firestore { doc_ref } ")
        
#         return jsonify({'status': 'success', 'ref_id': ref_id})


@bp.route('/final_create_int', methods=["GET", "POST"])
def final_create_int():
    final_data_json = {}
    if request.method == "OPTIONS":
        return 403
    else:
        data = ast.literal_eval(request.get_data().decode("utf-8"))
        print("the data here is  -> " , data)
       
        ref_id = "onlysinglerefid"
        file_name = str(data[3]).replace(" ", "_")
        final_json = {}
        final_detailed_json = {}
        final_all_json = {}
        doctument_json ={}
        document_vales = {}
        data_dict = {}
        for i in range(len(data[0])):
            temp_json = {}
            for j in range(len(data[1][i])):
                temp_json[str(data[1][i][j])] = str(data[2][i][j])
           
            final_json[data[0][i]] = temp_json
        final_all_json["data"] = final_json
        final_all_json["ref_id"] = ref_id
        final_all_json["int_name"] = str(data[3])
        final_all_json["int_status"] = "active"
        final_all_json["int_created"] = str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
       
        with open(str(app.config['INT_JSON']) + "/" + str(file_name) + '.json', 'w') as f:
            json.dump(final_all_json, f)

        object_key = f"configurator_int_json/"
        upload_file_to_s3(object_key, str(app.config['INT_JSON']) + "/" + str(file_name) + '.json', f"{str(file_name)}.json")
        print("all flattened not ",final_all_json)
        final_data_json = final_all_json["data"]
        print(final_data_json)
        i = 0
        for data_key,data_value in final_data_json.items():
            i = i +1
            doctument_json[f"doc_type_{i}"] = data_key
            document_vales[f"data_{i}"] = data_value
       
        print(document_vales,"check values")
        print(doctument_json,"check before firebase ")
       
        doc_ref = db.collection('configurator-interpretation').document(ref_id)
        doctument_json.update(document_vales)
        cleaned_data = remove_empty_strings(doctument_json)
        # cleaned_data = {key: value for key, value in doctument_json.items() if value != {''} and (not isinstance(value, dict) or any(v != '' for v in value.values()))}
        print(cleaned_data,"check")
        doc_ref.set(cleaned_data)
       
 
        print(f"the data is sent to firestore { doc_ref } ")
       
        return jsonify({'status': 'success', 'ref_id': ref_id})
 

def remove_empty_strings(data):
    cleaned_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            nested_cleaned = remove_empty_strings(value)
            if nested_cleaned:
                cleaned_data[key] = nested_cleaned
        elif key != '' and value != '':
            cleaned_data[key] = value
    return cleaned_data


@bp.route('/get_data', methods=['GET'])
def get_data():
    
    # name = request.args.get('n')
    req_id = request.args.get('refIdForBackendReq')
    # print(f"The name is {name}")
    print(f"The id is {req_id}")
    
    try:
        doc_ref = db.collection('configurator-interpretation').document(req_id)
        
        # query_name = doc_ref.where('int_name', '==', name)
        
        # results_name = query_name.get()

        doc_data = doc_ref.get().to_dict()
        # query_req_id = doc_ref.where('req_id', '==', req_id)
        print(f" the query req id is -> {doc_data}  ")
        # results_req_id = doc_data.get()
        # print("the results req id is ->" , results_req_id)
        # data_name = {doc.id: doc.to_dict() for doc in results_name}
        # data_req_id = {doc.id: doc.to_dict() for doc in results_req_id}
        # print("the data req id is ->" , data_req_id)
        
        # merged_data = {**data_req_id}
        # print(f"the merged data is -> {merged_data}")
        return jsonify(doc_data)
    
    except Exception as e:
        return jsonify({"error": str(e)})





@bp.route('/get_int_json', methods=["GET", "POST"])
def get_int_json():
    if request.method == "OPTIONS":
        return 403
    else:
        data = ast.literal_eval(request.get_data().decode("utf-8"))
        print(data)
        json_file = str(app.config['INT_JSON']) + "/" + str(data[0]) + '.json'
        f = open(json_file)
        json_data = json.load(f)
        # for key,val in json_data['data'].items():
        #     print(key)
        #     print(val)
        return {"data": json_data}


@bp.route('/send_file', methods=["GET", "POST"])
def send_file():
    if request.method == "OPTIONS":
        return 403
    else:
        ref_id = str(uuid.uuid4())
        if 'file' not in request.files:
            resp = jsonify({'message': 'No file part in the request', 'ref_id': ref_id})
            resp.status_code = 400
            return resp
        file = request.files['file']
        if file.filename == '':
            resp = jsonify({'message': 'No file selected for uploading', 'ref_id': ref_id})
            resp.status_code = 400
            return resp
        final_file_name = re.sub('[^a-zA-Z0-9 \n\.]', '', str(file.filename))
        main_path = str(app.config['UPLOAD_FOLDER']) + "/" + str(ref_id)
        file_path = str(main_path) + "/" + secure_filename(str(final_file_name).replace(" ", ""))
        if not os.path.exists(main_path):
            os.makedirs(main_path)
        file.save(file_path)
        unzip_path = str(app.config['UNZIP_FOLDER']) + "/" + str(ref_id)
        if not os.path.exists(unzip_path):
            os.makedirs(unzip_path)
        result_path = str(app.config['RESULT_JSON']) + "/" + str(ref_id)
        if not os.path.exists(result_path):
            os.makedirs(result_path)
        unzipping_file(file_path, unzip_path)
        class_result = classification_logic(unzip_path)
        fin_res = select_interpretation_config(str(app.config['INT_JSON']), class_result)
        # print("fin_res",fin_res)
        merged_json = main_interpretation_run(app, fin_res, result_path)
       
        print(merged_json,"category.json")
        with open(merged_json, 'r') as interpretation_file:
            interpretation_data = json.load(interpretation_file)
            # interpretation_data = interpretation_data["data"]
       
        
        form_row = os.path.join(app.config['RULE_JSON'] , "youngstar.json" ) 
        
        with open( form_row , 'r') as rule_file:
            rule_data = json.load(rule_file)
        rule_data_final = rule_data["data"]
        check_response = get_prompt(interpretation_data,rule_data_final)
        print(check_response,"finalresponse")
        print(f"******%%%%%%%%%%%% {interpretation_data}******")
        # threading.Thread(target=main_interpretation_run,args=(app, fin_res, result_path,),).start()
        
        final_data = {
            "rule_data" : check_response,
            "interpretation_data": interpretation_data
        }
        return final_data

@bp.route('/claim_details', methods=['GET', 'POST'])
def claim_details():
    
    
    response_data = {
    }


    # If it's an AJAX request (e.g., from your JavaScript code)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)

    # If it's a regular request, render the HTML template
    return render_template("summary_table.html", response_data=response_data)


def change_resolution(input_image_path, output_image_path, basewidth, baseheight):
    # img = Image.open(input_image_path)
    # # baseheight = data["baseheight"]
    # # basewidth = data["basewidth"]
    # hpercent = (baseheight / float(img.size[1]))
    # wsize = int((float(img.size[0]) * float(hpercent)))
    # wpercent = (basewidth / float(img.size[0]))
    # hsize = int((float(img.size[1]) * float(wpercent)))
    # print(wsize, hsize)
    # img = img.resize((wsize, hsize), Image.ANTIALIAS)
    # img.save(output_image_path)
    image = cv2.imread(input_image_path, 1)
    resized_image = cv2.resize(image, (basewidth, baseheight))
    cv2.imwrite(output_image_path, resized_image)


def save_image_of_pdf(page,length_of_files_present,i,save_path,folder,q1):
    page.save(os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + '.jpg')), 'JPEG')
    # img = cv2.imread(os.path.join(save_path, str(i + length_of_files_present) + '.jpg'))
    change_resolution(os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + ".jpg")),
                      os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + ".jpg")),2300, 2700)
    data = {
        "result":"ok"
    }
    q1.put(data)

def converting_to_image(file_name, save_path, folder):
    file_name_temp = []
    my_image_name = str(file_name).replace(".PDF", "").replace(".pdf", "")
    length_of_files_present = len(os.listdir(save_path))

    print(length_of_files_present)

    ##print("Started")
    ##my_image_name1 = my_image_name.split("\\")[-1]
    ##print(my_image_name1)
    doc_name = []
    # import tempfile
    # with tempfile.TemporaryDirectory() as tempdir:
    start = time.time()
    pages = convert_from_path(file_name)
    print("convert",time.time() - start)
    print("Started Image Extraction....")
    no_of_pages = len(pages)
    print("pages : ", no_of_pages)
    queue_variables = {}
    for i in range(len(pages)):
        queue_variables["new_data_" + str(i)] = queue.Queue()
        ##file_name_temp.append(str(my_image_name) + '-' + str(i) + '.jpeg')
        ##pages[i].save(save_path + str(i) + '.jpeg', 'JPEG')
        ##file_name_temp.append(save_path + str(i) + '.jpeg')
        # filepath = os.path.join(folder, str(i + length_of_files_present) + ".jpg")
        # pages[i].save(os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + '.jpg')), 'JPEG')
        # # img = cv2.imread(os.path.join(save_path, str(i + length_of_files_present) + '.jpg'))
        # change_resolution(os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + ".jpg")),
        #                   os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + ".jpg")),
        #                   2300, 2700)
        threading.Thread(target=save_image_of_pdf,args=(pages[i],length_of_files_present,i,save_path,folder,queue_variables["new_data_" + str(i)],)).start()
    for i in range(len(pages)):
        result = queue_variables["new_data_" + str(i)].get()


    print('completed imaging')
    # print(doc_name)
    ##file_name_temp.append(os.path.join(save_path,str(i) + '.jpeg'))
    # return hospital, doc





UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/uploadPdf', methods=['POST'])
def upload_file_pdf():
    try:
        ref_id = str(uuid.uuid4())
        print("Pdf Uploaded id is: ",ref_id)
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']
        json_file_name = request.form['selected_json']

        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        if file and file.filename.endswith('.pdf'):

            final_file_name = re.sub('[^a-zA-Z0-9 \n\.]', '', str(file.filename))
            main_path = str(app.config['UPLOAD_FOLDER']) + "/" + str(ref_id)
            file_path = str(main_path) + "/" + secure_filename(str(final_file_name).replace(" ", ""))
            if not os.path.exists(main_path):
                os.makedirs(main_path)
            file.save(file_path)
            converted_images = "images"

            no_pages = PdfToImage.pdf_to_img(file_path,main_path,converted_images,index=1)
            i = 1
            EXTRACTED_FOLDER = 'save_extracted'
            if not os.path.exists(EXTRACTED_FOLDER):
                os.makedirs(EXTRACTED_FOLDER)
            app.config['EXTRACTED_FOLDER'] = EXTRACTED_FOLDER
            
            output_directory_path = os.path.join(str(app.config['EXTRACTED_FOLDER']), str(ref_id))
            if not os.path.exists(output_directory_path):
                os.makedirs(output_directory_path)

            # Also creating all bill json
            all_bill_json_path = os.path.join(output_directory_path, 'all_bill.json')
            all_bill_json = ms_icr(file_path)
            rm_bounding_bx = remove_bounding_box(all_bill_json)
            modified_json_string = json.dumps(rm_bounding_bx, indent=2)

            with open(all_bill_json_path, "w") as output_file:
                output_file.write(modified_json_string)

            bills_json = {}
            dischargesummary = {}
            pharmacybill = {}
            policy = {}
            bills_counter = 1
            dischargesummary_counter = 1
            pharmacybill_counter = 1
            policy_counter = 1
            for page in range(no_pages):
                filepath = os.path.join(main_path, str(converted_images), str(converted_images) + str(i) + ".jpg")
                print(filepath)
                classify = get_classification(filepath)

                if classify == "bills" or classify == "billdetails":
                    extraction_data_bills = ms_icr(filepath)
                    remove_bounding_box_data_bills = text_concat(extraction_data_bills)
                    key_bills = f"bills_{bills_counter}"
                    bills_json[key_bills] = remove_bounding_box_data_bills
                    bills_counter += 1

                if classify == "dischargesummary":
                    extraction_data_dischargesummary = ms_icr(filepath)
                    remove_bounding_box_data_dischargesummary = text_concat(extraction_data_dischargesummary)
                    key_dischargesummary = f"dischargesummary_{dischargesummary_counter}"
                    dischargesummary[key_dischargesummary] = remove_bounding_box_data_dischargesummary
                    dischargesummary_counter += 1
                
                if classify == "pharmacybill":
                    extraction_data_pharmacybill = ms_icr(filepath)
                    remove_bounding_box_data_pharmacybill = text_concat(extraction_data_pharmacybill)
                    key_pharmacybill = f"pharmacybill_{pharmacybill_counter}"
                    pharmacybill[key_pharmacybill] = remove_bounding_box_data_pharmacybill
                    pharmacybill_counter += 1

                if classify == "policydocs" or classify == "policy" or classify == "authorizationletter" :
                    extraction_data_policy = ms_icr(filepath)
                    remove_bounding_box_data_policy = text_concat(extraction_data_policy)
                    key_policy = f"policy_{policy_counter}"
                    policy[key_policy] = remove_bounding_box_data_policy
                    policy_counter += 1
                    
                i += 1
            if bills_json:
                output_file_path_for_bill1 = os.path.join(output_directory_path, 'bills.json')
                with open(output_file_path_for_bill1, "w") as output_file:
                    json.dump(bills_json, output_file, indent=4)

            if dischargesummary :
                output_file_path_for_bill2 = os.path.join(output_directory_path, 'discharge_summary.json')
                with open(output_file_path_for_bill2, "w") as output_file:
                    json.dump(dischargesummary, output_file, indent=4)

            if pharmacybill :
                output_file_path_for_bill3 = os.path.join(output_directory_path, 'pharmacy_bill.json')
                with open(output_file_path_for_bill3, "w") as output_file:
                    json.dump(pharmacybill, output_file, indent=4)

            if policy :
                output_file_path_for_bill4 = os.path.join(output_directory_path, 'policy.json')
                with open(output_file_path_for_bill4, "w") as output_file:
                    json.dump(policy, output_file, indent=4)
            result_path = str(app.config['RESULT_JSON']) + "/" + str(ref_id)
            if not os.path.exists(result_path):
                os.makedirs(result_path)
            class_result = classification_logic(output_directory_path)
            fin_res = select_interpretation_config(str(app.config['INT_JSON']), class_result)
            # print("fin_res",fin_res)
            merged_json = main_interpretation_run(app, fin_res, result_path)
        
            print(merged_json,"category.json")
            with open(merged_json, 'r') as interpretation_file:
                interpretation_data = json.load(interpretation_file)
                # interpretation_data = interpretation_data["data"]
        
            
            form_row = os.path.join(app.config['RULE_JSON'], json_file_name + '.json')
            if not os.path.exists(form_row):
                return jsonify({'error': 'Error in selecting json file'})

            with open( form_row , 'r') as rule_file:
                rule_data = json.load(rule_file)
            rule_data_final = rule_data["data"]
            check_response = get_prompt(interpretation_data,rule_data_final)
            print(check_response,"finalresponse")
            print(f"******%%%%%%%%%%%% {interpretation_data}******")
            # threading.Thread(target=main_interpretation_run,args=(app, fin_res, result_path,),).start()
            
            final_data = {
                "rule_data" : check_response,
                "interpretation_data": interpretation_data
            }
            print(final_data)
            # return final_data
            return jsonify(final_data)
        else:
            return jsonify({'error': 'Only PDF files are allowed'})
    except Exception as e:
        return jsonify({'error': f'Error: {e}'})
    
@bp.route('/viewPDF', methods = ['GET'])
def viewPDf():
    try:
        rule_data_json = request.args.get("rule_data")
        interpretation_data_json = request.args.get("interpretation_data")

        # Convert JSON strings back to Python dictionaries
        rule_data = json.loads(rule_data_json)
        interpretation_data = json.loads(interpretation_data_json)

        final_data = {
            "rule_data": rule_data,
            "interpretation_data": interpretation_data
        }

        # Convert final_data to JSON before passing to the template
        final_data_json = final_data

        return render_template("upload_output.html", final_data=final_data_json)
    except:
        return render_template("something_went_wrong.html")

