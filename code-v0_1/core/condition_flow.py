from core.flow_functions import auto_planning,execute_sub_task,judge_whether_finish,flow_conclusion

def condition_flow(task_description:str, max_turns:int=3) -> str:
    try:
        print(f"[Condition Flow] Extracted task info: \n {task_description}")
        flow_messages = [{"role":"task_description",
                          "content":task_description}]
        current_turn = 0
        while current_turn < max_turns:
            print("[Condition Flow] Auto planning...")
            tasks = auto_planning(flow_messages)
            print("[Condition Flow] Scheduled tasks below: \n ")
            for i in range(len(tasks)):
                print(tasks[i])
            if tasks == []:
                return "Planning failed"
            for i, task in enumerate(tasks):
                print(f"[Condition Flow] Executing sub task {i}...")
                flow_messages.append({"role":f"step_{i}","content":execute_sub_task(task, flow_messages)})
            judge = judge_whether_finish(flow_messages)
            if judge:
                break
            current_turn += 1
        if current_turn >= max_turns:
            flow_messages.append({"role":"result","content":f"failed to solve the task after {max_turns} turns."})
        print("[Condition Flow] Flow finished, now concluding...")
        return flow_conclusion(flow_messages)
    except Exception as e:
        print(f"[Condition Flow] Failed. Info: {e}")
        return "Condition Flow failed."
