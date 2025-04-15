import os
from datetime import datetime
import re
import pandas as pd

def fix_payment_status_references():
    """
    Função para corrigir referências a 'payment_status' em todos os arquivos Python.
    Será executada automaticamente na inicialização do aplicativo.
    """
    files_fixed = []

    # Verificar diretório principal
    for file in os.listdir("."):
        if file.endswith(".py") and file != "auto_fix.py":
            try:
                file_path = os.path.join(".", file)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if "payment_status" in content:
                    new_content = content.replace("payment_status", "status")
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    files_fixed.append(file)
            except Exception as e:
                print(f"Erro ao processar {file}: {str(e)}")

    # Verificar diretório pages
    if os.path.exists("pages"):
        for file in os.listdir("pages"):
            if file.endswith(".py"):
                try:
                    file_path = os.path.join("pages", file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    if "payment_status" in content:
                        new_content = content.replace("payment_status", "status")
                        with open(file_path, 'w') as f:
                            f.write(new_content)
                        files_fixed.append(f"pages/{file}")
                except Exception as e:
                    print(f"Erro ao processar pages/{file}: {str(e)}")

    # Verificar se há pagamentos com status 'paid' sem data de pagamento
    if os.path.exists("data/payments.csv"):
        try:
            payments_df = pd.read_csv("data/payments.csv")
            if 'status' in payments_df.columns and 'payment_date' in payments_df.columns:
                # Encontrar pagamentos com status 'paid' sem data de pagamento
                paid_no_date = payments_df[(payments_df['status'] == 'paid') & (payments_df['payment_date'].isna())]
                
                if not paid_no_date.empty:
                    # Adicionar data atual para pagamentos sem data
                    today = datetime.now().strftime('%Y-%m-%d')
                    payments_df.loc[(payments_df['status'] == 'paid') & (payments_df['payment_date'].isna()), 'payment_date'] = today
                    payments_df.to_csv("data/payments.csv", index=False)
                    files_fixed.append("data/payments.csv (corrigidos pagamentos sem data)")
        except Exception as e:
            print(f"Erro ao processar payments.csv: {str(e)}")

    return files_fixed

def fix_estagios_format_students():
    """
    Corrige o problema 'AttributeError: 'int' object has no attribute 'split'' 
    na função format_students do arquivo 3_Estagios.py
    """
    if not os.path.exists("pages/3_Estagios.py"):
        return False
    
    try:
        with open("pages/3_Estagios.py", 'r') as f:
            content = f.read()
        
        # Procurar a função format_students
        if "def format_students" in content:
            # Corrigir o código para verificar se o valor é string antes de chamar .split()
            updated_content = re.sub(
                r'(def format_students\(students_str\):.*?\n.*?if not students_str or pd\.isna\(students_str\):.*?\n.*?return "".*?\n\n.*?)student_phones = students_str\.split\(\',\'\)',
                r'\1# Converter para string se não for string\n                if not isinstance(students_str, str):\n                    students_str = str(students_str)\n                \n                student_phones = students_str.split(\',\')',
                content, 
                flags=re.DOTALL
            )
            
            # Se a substituição com regex não funcionou, tente uma mais simples
            if updated_content == content:
                updated_content = content.replace(
                    "student_phones = students_str.split(',')",
                    "# Converter para string se não for string\n                if not isinstance(students_str, str):\n                    students_str = str(students_str)\n                \n                student_phones = students_str.split(',')"
                )
            
            # Verificar se o conteúdo foi realmente alterado
            if updated_content != content:
                with open("pages/3_Estagios.py", 'w') as f:
                    f.write(updated_content)
                return True
    except Exception as e:
        print(f"Erro ao corrigir format_students em 3_Estagios.py: {str(e)}")
        
    return False
