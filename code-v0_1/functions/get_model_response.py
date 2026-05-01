from openai import OpenAI
from datetime import datetime
import time
import os
import json

def get_model_response(
        model_name:str, 
        base_url:str, 
        api_key:str, 
        user_prompt:str="", 
        system_prompt:str="", 
        messages:list=None,
        max_tokens:int=4000, 
        max_retries:int=3, 
        temperature:float=0,
        tools:list=None,
        tool_choice:str="auto",
        response_format:dict=None,
        extra_body:dict=None
    ) -> str:
    if messages == None:
        messages=[
                    {"role":"system", "content":system_prompt},
                    {"role":"user", "content":user_prompt}
                ]
        
    
    client = OpenAI(base_url=base_url, api_key=api_key)
    for attemp in range(max_retries+1):
        try:
            start_time = time.time()

            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=tools,
                tool_choice=tool_choice,
                response_format=response_format,
                extra_body=extra_body
            )

            end_time = time.time()

            if completion.choices[0].message:
                usage = completion.usage
                prompt_tokens = usage.prompt_tokens if usage else None
                completion_tokens = usage.completion_tokens if usage else None
                total_tokens = usage.total_tokens if usage else None
                cost = getattr(usage, 'cost', None)

                log_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "model": model_name,
                    "latency_sec": round(end_time - start_time, 3),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    #"messages": messages,
                    #"response": completion.choices[0].message.content
                }

                os.makedirs("log", exist_ok=True)
                filepath = os.path.join("log", "model_request_log.jsonl")
                with open(filepath, "a") as f:
                    f.write(json.dumps(log_data, ensure_ascii=False)+"\n")

                return completion.choices[0].message
            else:
                if attemp == max_retries:
                    raise RuntimeError(f"[Request Info]: Request to LLM failed after {max_retries} retries.")
                print(f"[Request Info]: Model returns \'None\', retry the {attemp+1} times in 3 seconds...")
        except Exception as e:
            if attemp == max_retries:
                raise RuntimeError(f"[Request Info]: Request to LLM failed after {max_retries} retries. {e}")
            print(f"[Request Info]: Request failed, retry the {attemp+1} times in 3 seconds...")
            time.sleep(3)