import json
import requests
def advance_rectifier(prompt_txt):

    prompt_template=f'''<|im_start|>system
    you are an expert medical analyst<|im_end|>
    <|im_start|>user
    {prompt_txt}<|im_end|>
    <|im_start|>assistant
    '''

    url = ""

    payload = json.dumps({
    "model": "",
    "prompt": prompt_template,
    "max_tokens": 500,
    "temperature": 0.7
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.status_code)

    # print(response.json())
    data = response.json()
    text = data['choices'][0]['text']

    # Print the extracted text
    print(text)

    return text


def get_prompt(data,finder):
    rule_dict = {}
    query_dict = {}

    '''
 
    :param data: interpretation data
    :param finder:
    {"que": "Check whether patient name is same across all documents?","type" : "generic", "doc" : ["discharge summary" , "policy"]}
    :return:
    '''
    response_dict = {}
    for key,value in finder.items():
        if key != "":
            print(value,"this is printedd")
            for rule_key,value_docs in value.items():
                final_key = f"{key}_{rule_key}"
                prompt_text = ""

                check_response = advance_rectifier(prompt_text)
                print(check_response,'reposne from nlp')

                response_dict[final_key] = check_response



    print(response_dict, "checkkkkkkkkkkk_geneirc")
    print(json.dumps(response_dict, indent=2))
    return response_dict
