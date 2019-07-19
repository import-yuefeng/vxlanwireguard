from typing import List

def load(batch_name: str) -> list or bool:
    command_list: list(str) = []
    try:
        batch_file = open(batch_name, 'r')
    except FileNotFoundError:
        return False
    else:
        # batch_file_content :str = batch_file.readlines
        for sentence in batch_file.readlines():
            if sentence.split('\n')[0]:
                command_list.append(sentence.split('\n')[0].strip())

    return command_list



