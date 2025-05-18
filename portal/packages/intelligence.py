from zipfile import ZipFile
import os, json
from portal.packages.generic_extraction import main_run_generic_interpretation

def unzipping_file(zip_path, unzip_path):
    with ZipFile(zip_path, 'r') as zObject:
        zObject.extractall(path=unzip_path)


def classification_logic(unzip_path):
    list_file = os.listdir(unzip_path)
    return_data = {}
    for i in range(len(list_file)):
        if str(list_file[i]).__contains__("discharge"):
            return_data["discharge summary"] = str(unzip_path) + "/" + str(list_file[i])
        elif str(list_file[i]).__contains__("policy"):
            return_data["policy"] = str(unzip_path) + "/" + str(list_file[i])
        elif str(list_file[i]).__contains__("pharmacy_bill"):
            return_data["bill page full"] = str(unzip_path) + "/" + str(list_file[i])
        elif str(list_file[i]).__contains__("bills"):
            return_data["bills"] = str(unzip_path) + "/" + str(list_file[i])
    return return_data


def select_interpretation_config(int_config_path, class_res):
    doc_types, final_list_conf, ref_id, count_id, int_name, final_type_doc, doc_path ,final_doc_path = [], [], [], [], [], [], [], []
    list_int_conf = os.listdir(int_config_path)
    for key, val in class_res.items():
        doc_types.append(key)
        doc_path.append(val)
    for i in range(len(list_int_conf)):
        temp_list = []
        json_file = str(int_config_path) + "/" + str(list_int_conf[i])
        f = open(json_file)
        json_data = json.load(f)
        for key, val in json_data['data'].items():
            temp_list.append(key)
        final_list_conf.append(temp_list)
        ref_id.append(json_data['ref_id'])
        int_name.append(json_data['int_name'])
    print("final_list_conf", final_list_conf)
    print("doc_types", doc_types)
    for i in range(len(final_list_conf)):
        res = 0
        for k in range(len(doc_types)):
            if str(doc_types[k]) in final_list_conf[i]:
                res += 1
                final_type_doc.append(doc_types[k])
                final_doc_path.append(doc_path[k])
        # res = len([final_list_conf[i].index(k) for k in doc_types])
        count_id.append(res)
    max_index = count_id.index(max(count_id))
    ret_data = {
        "ref_id": ref_id[max_index],
        "int_name": int_name[max_index],
        "final_type_doc": final_type_doc,
        "final_doc_path": final_doc_path
    }
    return ret_data



# new 


def main_interpretation_run(app, int_file_config,result_path):
    json_file = str(app.config['INT_JSON']) + "/" + str(int_file_config['int_name']).replace(" ","_") + ".json"
    f = open(json_file)
    json_data = json.load(f)
    merged_data = {}
    for i in range(len(int_file_config['final_type_doc'])):
        content = "get "
        for key,val in json_data["data"][int_file_config['final_type_doc'][i]].items():
            content = content + str(key) + " key as " + str(key).lower().replace(
                " ",
                "_") + " in format of " + str(val) + ", "
        content = content + " in json if data not found give result as none from below text\n\n"
        print("final_doc_path",int_file_config['final_doc_path'][i])
        print("final_doc_path",os.path.basename(int_file_config['final_doc_path'][i]))
        res_js,type_single = main_run_generic_interpretation(int_file_config['final_doc_path'][i], content, os.path.basename(int_file_config['final_doc_path'][i]))
        print("res_js",res_js)
        json_object = json.dumps(res_js, indent=4)
        with open(str(result_path) + "/" + str(int_file_config['final_type_doc'][i]) + ".json", "w") as outfile:
            outfile.write(json_object)
        merged_data = {}
       
# Assuming you have a loop where you iterate over your JSON objects
    for filename in os.listdir(result_path):
        if filename.endswith(".json"):
            file_path = os.path.join(result_path, filename)
 
            # Read the current JSON file
            with open(file_path, "r") as infile:
                json_object = json.load(infile)
 
            # Get the key for the current JSON file
            key = filename.split(".")[0]
 
            # Merge the current JSON object into the dictionary using the key
            merged_data[key] = json_object
 
    # Specify the path for the final merged JSON file
    result1_path = result_path
    merged_json_file_path = os.path.join(result1_path, "merged_data.json")
 
    # Write the merged data to the JSON file
    with open(merged_json_file_path, "w") as outfile:
        json.dump(merged_data, outfile, indent=2)
 
    print(f"Merged data has been written to {merged_json_file_path}")
    return merged_json_file_path