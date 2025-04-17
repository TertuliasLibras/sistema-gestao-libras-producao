"""
Este arquivo contém funções para corrigir problemas comuns em arquivos Python.
Estas correções são aplicadas automaticamente quando o aplicativo é iniciado.
"""

import os
import re

def fix_payment_status_references():
    """
    Função para corrigir referências a 'payment_status' em todos os arquivos Python.
    Será executada automaticamente na inicialização do aplicativo.
    """
    fixed_files = []
    
    # Diretórios a serem verificados
    directories = ['.', 'pages']
    
    for directory in directories:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith('.py'):
                    filepath = os.path.join(directory, filename)
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Verifique por referências a 'payment_status'
                    if "payment_status" in content:
                        # Substitua 'payment_status' por 'status'
                        new_content = re.sub(r'(\[|\s|\.)payment_status(\s|\]|\)|\'|\")', r'\1status\2', content)
                        
                        # Se houve alteração, salve o arquivo
                        if new_content != content:
                            with open(filepath, 'w', encoding='utf-8') as file:
                                file.write(new_content)
                            fixed_files.append(filepath)
    
    return fixed_files


def fix_estagios_format_students():
    """
    Corrige o problema 'AttributeError: 'int' object has no attribute 'split'' 
    na função format_students do arquivo 3_Estagios.py
    """
    filepath = 'pages/3_Estagios.py'
    fixed = False
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Localize a função format_students
        pattern = r'def format_students\(students_str\):(.*?)return'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            func_body = match.group(1)
            
            # Verifique se já contém a verificação de tipo
            if "isinstance(students_str, str)" not in func_body:
                # Adicione a verificação de tipo
                new_func_body = func_body.replace(
                    'if not students_str or pd.isna(students_str):',
                    'if not students_str or pd.isna(students_str):\n                    return ""\n                \n                # Se o valor não for string (for inteiro), converta para string\n                if not isinstance(students_str, str):\n                    students_str = str(students_str)'
                )
                
                # Substitua o corpo da função
                new_content = content.replace(func_body, new_func_body)
                
                # Corrija também a função lambda que conta alunos
                if "lambda x: len(x.split(','))" in new_content:
                    new_content = new_content.replace(
                        "lambda x: len(x.split(',')) if not pd.isna(x) and x.strip() else 0",
                        "lambda x: len(str(x).split(',')) if not pd.isna(x) and (isinstance(x, str) and x.strip() or not isinstance(x, str)) else 0"
                    )
                
                # Corrija também na seção "Horas por Aluno"
                if "students_in_internship = str(internship['students']).split(',')" not in new_content:
                    new_content = new_content.replace(
                        "students_in_internship = internship['students'].split(',')",
                        "students_str = str(internship['students']) if not pd.isna(internship['students']) else ''\n                students_in_internship = students_str.split(',')"
                    )
                
                # Salve as alterações
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                fixed = True
    
    return fixed
