import json
from concurrent.futures import ThreadPoolExecutor, as_completed  
import os
import pandas as pd
from gpt4o import Openai, API_INFOS
from datasets import load_dataset, Dataset
from tqdm import tqdm

system_template = \
"""You are tasked with acting as a text rewriter to enhance the readability and comprehension of text generated by a Large Language Model (LLM). Your goal is to ensure the text is easy to read, easy to understand, and visually organized in a logical manner. Modifications should be reasonable and appropriate, rather than mandatory. Each element should be used judiciously to enhance readability and comprehension."""

user_template = """  
<|User Prompt|>{instruction}  
<|The Start of Assistant's Answer|>{completion}<|The End of Assistant's Answer|>  
  
Your task is to:  
1. **Analyze the LLM-generated response**:  
    - Read and understand the text to grasp its context and purpose.  
    - Carefully review the text generated by the LLM.  
    - Evaluate its structure, formatting, and overall readability.  
2. **Determine the Need for Modification**:  
    - Decide whether the text needs modification to improve its readability and comprehension.  
    - If the text is already satisfactory, no changes are necessary.  
3. **Provide a Revised Version of the Text if Necessary**:  
    - Make appropriate modifications to enhance the text's readability and comprehension.  
    - Ensure the revised text maintains a consistent style and format throughout.  
  
**Textual Aesthetic Elements to Consider**:  
1. **Paragraph Structure**: Ensure paragraphs are of appropriate length and logically structured. Use appropriate spacing between paragraphs.  
2. **Indentation**: Apply consistent indentation if necessary.  
3. **Headings and Subheadings**: Use headings to organize content and improve readability, but only if the content naturally lends itself to such structure.  
4. **Lists and Bullet Points**: Utilize lists to break down complex information when applicable.  
5. **Formatting for Emphasis**: Use bold or italic text to emphasize important points judiciously.  
6. **Line Spacing**: Adjust line spacing to enhance readability.  
7. **Consistency**: Maintain a consistent style throughout the document.  
8. **Visual Breaks**: Use visual breaks to separate different sections if applicable.  
9. **Blockquotes**: Use blockquotes for quotations or highlighted text.  
10. **Links**: Format hyperlinks appropriately when applicable.  
11. **Tables**: Use tables for any tabular data if required.  
12. **Whitespace and Spacing**: Ensure appropriate use of whitespace and spacing to avoid a cluttered appearance.  
  
**Format**:  
**Textual Aesthetic Analysis**:  
- Your analysis  
**Does it need modification**:  
- If it needs modification: [[Y]]  
- If it doesn't need modification: [[N]]  
**Revised Text**:  
- If it needs modification: <|Revised Content Start|>Your revised text<|Revised Content End|>  
- If it doesn't need modification: <|Revised Content Start|>""<|Revised Content End|>  
  
**Example Output**:  
**Textual Aesthetic Analysis**:  
The text is clear, well-organized, and easy to read.  
**Does it need modification**: [[N]]  
**Revised Text**:  
<|Revised Content Start|>""<|Revised Content End|>  
"""

def get_data():
    ds = load_dataset("HuggingFaceH4/ultrafeedback_binarized", split="train_prefs")
    def get_instruct_response(item):
        # item["instruction"] = item['chosen'][0]["content"]
        item["response"] = item['chosen'][1]["content"]
        return item
    ds = ds.map(get_instruct_response, batch_size=1024, num_proc=8)
    export_data = ds.select_columns(["prompt", "response"])
    return export_data

def get_revised_text(client, instruction, completion, user_template, system_template, max_tokens=2048):  
    # 格式化用户模板，插入指令和完成的文本  
    content = user_template.format(instruction=instruction, completion=completion)  
      
    # 从客户端获取响应  
    gpt_answer = client.get_response(content=content, system=system_template, max_tokens=max_tokens)  
      
    if gpt_answer is None:  
        gpt_answer = ""  
    gpt_answer = gpt_answer.strip()  
      
    # 确定是否需要修改  
    need_modification = "Y" if "**Does it need modification**: [[Y]]" in gpt_answer else "N"  
      
    # 提取修改后的文本  
    if need_modification == "Y":  
        revised_text_start = gpt_answer.find("<|Revised Content Start|>") + len("<|Revised Content Start|>")  
        revised_text_end = gpt_answer.find("<|Revised Content End|>", revised_text_start)  
        revised_text = gpt_answer[revised_text_start:revised_text_end].strip()  
    else:  
        revised_text = ""  
      
    return need_modification, revised_text, gpt_answer  

  
    return need_modification, revised_text, gpt_answer  
 
def process_row(index, client, row, user_template, system_template, max_tokens=2048, output_file="output.jsonl"):  
    prompt = row['prompt']  
    response = row['response']  
    need_modification, revised_text, gpt_answer = get_revised_text(client, prompt, response, user_template, system_template, max_tokens=max_tokens)  
    # print(f"index {index}")
    result = {  
        'index': index,  
        'prompt': prompt,  
        'response': response,  
        'does_it_need_modification': need_modification,  
        'revised_text': revised_text,  
        'gpt_answer': gpt_answer  
    }  
    # Write the result to a JSONL file  
    with open(output_file, 'a') as f:  
        f.write(json.dumps(result) + "\n")  
    return result  
def main():  
    # Initialize multiple clients  
    clients = [Openai(apis=[API_INFOS[i]]) for i in range(len(API_INFOS))]  
    print(f"clients number: {len(clients)}")
    export_data = get_data()
    # sample_data = export_data.select(range(100))
    sample_data = export_data # all
    # user_template = "User: {instruction}\nCompletion: {completion}"  
    # system_template = "You are a helpful assistant."  
    max_tokens = 2048  
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    # data_path = os.path.join(cur_dir, "revised_data/output_sorted.jsonl")
    output_file = "revised_data/output.jsonl"  
    output_file = os.path.join(cur_dir, output_file)
  
    # Clear the output file before starting  
    if os.path.exists(output_file):  
        os.remove(output_file)  
  
    revised_data = []  
  
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:  
        # Create a future for each row in the dataset  
        futures = [executor.submit(process_row, i, clients[i % len(clients)], row, user_template, system_template, max_tokens, output_file) for i, row in enumerate(sample_data)]  
  
        # Collect the results as they complete  
        for future in tqdm(as_completed(futures), total=len(futures)):  
            revised_data.append(future.result())  

  
    # Load results from JSONL file and ensure the order is preserved  
    with open(output_file, 'r') as f:  
        revised_data = [json.loads(line) for line in f]  
  
    # Sort by the original index  
    revised_dataset = revised_data.sort(key=lambda x: x['index'])  
  
    # Create a new Dataset  
    revised_dataset = Dataset.from_pandas(pd.DataFrame(revised_data))  
    sorted_output_path = os.path.join(cur_dir, "revised_data/output_sorted.jsonl")
    revised_dataset.to_json(sorted_output_path) 
if __name__ == "__main__":
    main()
    # from generate_res import generate_res
    # generate_res()