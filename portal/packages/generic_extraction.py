import json, requests, os, time, cv2
from pdf2image import convert_from_path
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

def auth_gen():
    url = ""

    payload = json.dumps({
      "username": "",
      "password": ""
    })
    headers = {
      'Content-Type': 'application/json',
      'Cookie': 'session=eyJfcGVybWFuZW50Ijp0cnVlfQ.ZRgI8Q.gDdtC93b0PaqMFd1N3dKnMElttU'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()
def advance_rectifier(content):
    url = ""

    payload = json.dumps({
        "input": str(content)
    })
    headers = {
        'Authorization': 'JWT ' + str(auth_gen()['access_token']),
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()

def converting_to_image_pdf(file_path,file_name):
    Image.MAX_IMAGE_PIXELS = None
    file_name_temp = []
    my_image_name = str(file_name).replace(".pdf","").replace(".PDF","")
    if os.path.exists('temp_folder/' +str(my_image_name)):
        print("folder")
    else:
        os.mkdir('temp_folder/' +str(my_image_name))
    pages = convert_from_path(file_path, 600)
    no_of_pages = len(pages)

    for i, page in enumerate(pages):
        try:
            page.save('temp_folder/' + str(my_image_name) + "/" + str(my_image_name) + '-' + str(i) + '.jpeg', 'JPEG')
            page.close()
        except OSError as e:
            print(f"Error saving image {i}: {e}")   
    
    # old code below 
    # for i in range(len(pages)):
    #     file_name_temp.append(str(my_image_name) + '-' + str(i) + '.jpeg')
    #     print("image")
    #     print('temp_folder/' +str(my_image_name) +"/"+ str(my_image_name) + '-' + str(i) + '.jpeg')
    #     pages[i].save('temp_folder/' +str(my_image_name) +"/"+ str(my_image_name) + '-' + str(i) + '.jpeg', 'JPEG')
    return no_of_pages,file_name_temp,'temp_folder/' +str(my_image_name)


def process_subscription_key(subscription_key, endpoint, img_path):
    try:
        computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
        with open(img_path, 'rb') as read_image:
            read_response = computervision_client.read_in_stream(read_image,  raw=True)
        read_operation_location = read_response.headers["Operation-Location"]
        operation_id = read_operation_location.split("/")[-1]
        while True:
            read_result = computervision_client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
        time.sleep(1)
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
                    pass
            return text_result.as_dict()
    except Exception as e:
        print(f"Error processing {subscription_key} - {e}")
        return None

def ms_icr(img_path):
    keys_and_endpoints = [
        
    ]
    with ThreadPoolExecutor(max_workers=len(keys_and_endpoints)) as executor:
        futures = [executor.submit(process_subscription_key, key, endpoint, img_path) for key, endpoint in keys_and_endpoints]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                return result
    return None

def format_data(text_json,width_image):
    text_list_output = []
    line_text = ""
    buffer_space = ""
    bounding_buffer = []
    bounding_buffer_text = []
    # print("text_json",text_json)
    for i in range(len(text_json)):
        bounding_buffer_text.append(text_json[i].get("text"))
        bounding_buffer.append(text_json[i].get("bounding_box"))
    for i in range(len(bounding_buffer_text)):
        if len(bounding_buffer_text) - 1 > i:
            if bounding_buffer[i+1][0] - bounding_buffer[i][0] > 1:
                if line_text == "":
                    buffer_value = 3 * round(
                        width_image / (width_image - (bounding_buffer[i][0])) / 3)
                    if buffer_value == 0:
                        buffer_space = "    "
                    elif buffer_value == 3:
                        buffer_space = "        "
                    elif buffer_value == 6:
                        buffer_space = "            "
                    elif buffer_value == 9:
                        buffer_space = "                "
                    elif buffer_value == 12:
                        buffer_space = "                    "
                    line_text = line_text + buffer_space + str(bounding_buffer_text[i])
                else:
                    buffer_value = 3 * round(width_image/(width_image - (bounding_buffer[i][0] - bounding_buffer[i-1][6]))/3)
                    if buffer_value == 0:
                        buffer_space = "    "
                    elif buffer_value == 3:
                        buffer_space = "        "
                    elif buffer_value == 6:
                        buffer_space = "            "
                    elif buffer_value == 9:
                        buffer_space = "                "
                    elif buffer_value == 12:
                        buffer_space = "                    "
                    line_text = line_text + buffer_space + str(bounding_buffer_text[i])
            else:
                if line_text == "":
                    buffer_value = 3 * round(
                        width_image / (width_image - (bounding_buffer[i][0])) / 3)
                    if buffer_value == 0:
                        buffer_space = "    "
                    elif buffer_value == 3:
                        buffer_space = "        "
                    elif buffer_value == 6:
                        buffer_space = "            "
                    elif buffer_value == 9:
                        buffer_space = "                "
                    elif buffer_value == 12:
                        buffer_space = "                    "
                    line_text = line_text + buffer_space + str(bounding_buffer_text[i])
                else:
                    buffer_value = 3 * round(width_image/(width_image - (bounding_buffer[i][0] - bounding_buffer[i-1][6]))/3)
                    if buffer_value == 0:
                        buffer_space = "    "
                    elif buffer_value == 3:
                        buffer_space = "        "
                    elif buffer_value == 6:
                        buffer_space = "            "
                    elif buffer_value == 9:
                        buffer_space = "                "
                    elif buffer_value == 12:
                        buffer_space = "                    "
                    line_text = line_text + buffer_space + str(bounding_buffer_text[i])

                # line_text = line_text + " " +str(bounding_buffer_text[i])
                # print("#########################")
                text_list_output.append(line_text)
                # print("#########################")
                line_text = ""
    text_list_output.append(bounding_buffer_text[len(bounding_buffer_text) - 1])
    return text_list_output


# new 

# def main_run_generic_interpretation(file_path,context_main,file_name):
#     temp_dict_icr = {}
#     if str(file_path).upper().__contains__(".PDF"):
#         pages_no,list_of_img,parent_img_path = converting_to_image_pdf(file_path, file_name)
#         print("list_of_img",len(list_of_img))
#         for i in range(len(list_of_img)):
#             res_json = ms_icr(parent_img_path + "/" + str(list_of_img[i]))
#             print("page_" + str(i))
#             temp_text = ""
#             im = cv2.imread(parent_img_path + "/" + str(list_of_img[i]))
#             format_list = format_data(res_json['lines'],im.shape[1])
#             # for j in range(len(res_json['lines'])):
#             #     temp_text += res_json['lines'][j]['text'] + " "
#             for k in range(len(format_list)):
#                 temp_text += format_list[k] + "\n"
#             temp_dict_icr["page_" + str(i)] = temp_text
#     elif not str(file_path).upper().__contains__(".JSON"):
#         print("enetered here")
#         res_json = ms_icr(file_path)
#         temp_text = ""
#         im = cv2.imread(file_path)
#         format_list = format_data(res_json['lines'], im.shape[1])
#         # for j in range(len(res_json['lines'])):
#         #     temp_text += res_json['lines'][j]['text'] + " "
#         for i in range(len(format_list)):
#             temp_text += format_list[i] + "\n"
#         temp_dict_icr["page_0"] = temp_text
#     else:
#         print("file is not pdffff")
#         print("still going ahead")
#     print(temp_dict_icr)
#     if temp_dict_icr != "":
#         context = ""
#         for key, val in temp_dict_icr.items():
#             context = context + str(val)
#         context = context_main + context
#         final_output = advance_rectifier(context)
#         if type(final_output) == str:
#             return json.loads(final_output), "single"
#         else:
#             return final_output, "single"


# updated new 


def text_concat(json_data):
    text = " ".join([str(text.get('text')) for text in json_data])
 
    return text


def main_run_generic_interpretation(file_path,context_main,file_name):
    print(file_path,"cehck path")
    temp_dict_icr = {}
    if "bills.json" in file_path:
        with open(file_path, 'r') as file:
            bill_data = json.load(file)
        for i, (key, value_bill) in enumerate(bill_data.items(), start=1):
            print("Iteration:", i)
            print(key, "check key")
            # print(value_bill, 'check value_bill')
           
            format_list = value_bill
            # print(format_list, "check format_list")
           
            # temp_text = ""
            # for k in range(len(format_list)):
            #     temp_text += format_list[k] + "\n"
           
            temp_dict_icr["page_" + str(i)] = format_list
        print(temp_dict_icr,"check icr data")
        if temp_dict_icr != "":
            context = ""
            for key, val in temp_dict_icr.items():
                context = context + str(val)
            context = context_main + context
            print(context ,"check context")
            try:
                final_output = advance_rectifier(context)
                print(final_output,"i did it ")
            except:
                try:
                    final_output = advance_rectifier(context)
                    print(final_output,"i did it ")
                    
                except:
                    final_output = advance_rectifier(context)
                    print(final_output,"i did it ")
            if type(final_output) == str:
                return json.loads(final_output), "single"
            else:
                return final_output, "single"
    # print(bill_data)
    if "discharge" in file_path:
        print("entered discharge")
        with open(file_path, 'r') as file:
            discharge_data = json.load(file)
            for i, (key, value_discharge) in enumerate(discharge_data.items(), start=1):
                print("Iteration:", i)
                print(key, "check key")
                # print(value_bill, 'check value_bill')
               
                format_list = value_discharge
                # print(format_list, "check format_list")
               
                # temp_text = ""
                # for k in range(len(format_list)):
                #     temp_text += format_list[k] + "\n"
               
                temp_dict_icr["page_" + str(i)] = format_list
            print(temp_dict_icr,"check icr data")
            if temp_dict_icr != "":
                context = ""
                for key, val in temp_dict_icr.items():
                    context = context + str(val)
                context = context_main + context
                print(context ,"check context")
                final_output = advance_rectifier(context)
                print(final_output,"i did it ")
                if type(final_output) == str:
                    return json.loads(final_output), "single"
                else:
                    return final_output, "single"
    if "policy" in file_path:
        with open(file_path, 'r') as file:
            policy_data = json.load(file)
            for i, (key, value_policy) in enumerate(policy_data.items(), start=1):
                print("Iteration:", i)
                print(key, "check key")
                # print(value_bill, 'check value_bill')
               
                format_list = value_policy
                # print(format_list, "check format_list")
               
                # temp_text = ""
                # for k in range(len(format_list)):
                #     temp_text += format_list[k] + "\n"
               
                temp_dict_icr["page_" + str(i)] = format_list
            print(temp_dict_icr,"check icr data")
            if temp_dict_icr != "":
                context = ""
                for key, val in temp_dict_icr.items():
                    context = context + str(val)
                context = context_main + context
                print(context ,"check context")
                final_output = advance_rectifier(context)
                print(final_output,"i did it ")
                if type(final_output) == str:
                    return json.loads(final_output), "single"
                else:
                    return final_output, "single"