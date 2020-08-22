import json
import sys
import os
import re
import random
from pprint import pprint
from tqdm import tqdm

def Extract(eq, quan_map, mode):
    eq = re.sub(' ', '', eq)
    if mode == 'unknown':
        variables = []
        for var in re.findall(r'[a-zA-Z_]+', eq):
            if var not in variables:
                variables.append(var)
        return variables
    elif mode == 'variable':
        # substitute the equations
        variables = []
        xy = ['x', 'y']
        # unknowns
        for var in re.findall(r'(?<!\w)[a-zA-Z_](?!\w)', eq):
            if var not in variables:
                variables.append(var)
        for i in range(len(variables)):
            eq = re.sub(rf'(?<!\w){variables[i]}+(?!\w)', xy[i], eq)
        
        # quantities
        eq = re.sub(r'(?<=\.\d)0+', '', eq)
        eq = re.sub(r'\.0+(?!\d)', '', eq)
        for quan, num in quan_map.items():
            eq = re.sub(rf'(?<![\d\.N]){num}(?![\d\.])', quan, eq)
        # print(eq)
        return eq.split('\n')

def genMap(numbers):
    quan_map = {}
    for i in range(len(numbers)):
        quan_map['N'+str(i+1)] = numbers[i]
    return quan_map

def Normalize(question, mode):
    numbers = []
    if mode == 'unknown':
        return question
    elif mode == 'variable':
        question = question.lower()
        for (key, value) in str_to_num.items():
            question = re.sub(key, value, question)
        question = re.sub(r'(?<=\d),(?=\d)', '', question)
        question = re.sub(r'(?<=\.\d)0+', '', question)

        # generate the maop between quantities and numnber
        for number in re.findall(r'(\d+(\,\d+)?(\.\d+)?)', question):
            if number[0] not in numbers:
                tmp = str(number[0])
                tmp = re.sub(r'\.0$', '', tmp)
                tmp = re.sub(',', '', tmp)
                numbers.append(tmp)
        quan_map =  genMap(numbers)
        # print(quan_map)

        # substitute the question sentence
        for quan, num in quan_map.items():
            question = re.sub(rf'(?<![\d\.N]){num}(?!(\d|\.\d+))', quan, question)
        return question, quan_map


def createData(problemList):
    content = []
    for (iIndex, sQuestion, lEquations, lSolutions) in problemList:
        # if (type(iIndex) == str and re.search(r'\d+', iIndex)):
        #     iIndex = int(re.search(r'\d+', iIndex).group())
        #     iIndex += 1000
        dictionary = {'iIndex':iIndex, 'sQuestion':sQuestion, 'lEquations':lEquations,'lSolutions':lSolutions}
        content.append(dictionary)
    return content

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Missing Saving Dir(1), Mode(2) [unknown, variables]')
        exit(-1)
    Dir = sys.argv[1]
    mode = sys.argv[2]
    problemList = []
    str_to_num = { 'two':'2', 'three':'3', 'four':'4', 'five':'5', 'six':'6', 'seven':'7', 'eight':'8', 'nine':'9', 'ten':'10', 'once':'1', 'twice':'2', 'half':'0.5' }
    input_files = ['dev_cleaned.json', 'eval_cleaned.json']
    output_files = ['dev.json', 'eval.json']

    ID = 10000
    for (input_file, output_file) in zip(input_files, output_files):
        with open(input_file, 'r') as json_file:
            data = json.loads(json_file.read())
            for question in data:
                if len(re.findall(r'[\w\s\+\-\*\/]+=[\w\s\+\-\*\/]+', question['equations'])) <= 2:
                    # ID, ok
                    ID += 1
                    print('ID: ', ID)
                    # question, ok
                    str_q = question['text'][:question['text'].find('\"')]
                    print(str_q)
                    str_q, quan_map = Normalize(str_q, mode)
                    # equations
                    eq = re.sub('\r\n', '', question['equations'])
                    eq = '\n'.join(re.findall(r'(?<![equ:])[\w\s\+\-\*\/]+=[\w\s\+\-\*\/]+(?![qu:])', eq))
                    try:
                        nor_eq = Extract(eq, quan_map, mode)
                    except:
                        continue
                    # Solutions
                    ans = [ lambda x: int(x) for x in re.findall(r'\d+', question['ans']) ]

                    problemList.append((ID, str_q, nor_eq, ans))
                   
        with open(os.path.join(Dir, output_file), 'w') as json_file:
            json_file.write(json.dumps(createData(problemList), ensure_ascii=False, indent=2))