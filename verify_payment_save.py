import pandas as pd
import os
from datetime import datetime

print("VERIFICADOR DE COLUNA DE STATUS DE PAGAMENTOS")
print("=============================================")

def get_csv_files():
    """Lista todos os arquivos CSV no diretório data"""
    return [f for f in os.listdir('data') if f.endswith('.csv')]

def check_payments_file():
    """Verifica e corrige o arquivo de pagamentos"""
    if not os.path.exists('data/payments.csv'):
        print("Arquivo de pagamentos não encontrado!")
        return
    
    try:
        payments_df = pd.read_csv('data/payments.csv')
        print(f"Arquivo de pagamentos carregado com {len(payments_df)} registros")
        
        # Verificar nomes das colunas
        print("\nColunas encontradas:")
        for col in payments_df.columns:
            print(f"- {col}")
        
        # Verificar se status existe
        if 'status' in payments_df.columns:
            print("\nColuna 'status' encontrada, verificando valores...")
            status_counts = payments_df['status'].value_counts().to_dict()
            print(f"Contagem de status: {status_counts}")
        else:
            print("\nATENÇÃO: Coluna 'status' NÃO encontrada!")
            
            # Verificar se status existe
            if 'status' in payments_df.columns:
                print("Coluna 'status' encontrada, renomeando para 'status'...")
                payments_df = payments_df.rename(columns={'status': 'status'})
                payments_df.to_csv('data/payments.csv', index=False)
                print("Arquivo payments.csv atualizado com coluna renomeada.")
        
        # Verificar se há dados de pagamento
        if 'payment_date' in payments_df.columns:
            print("\nVerificando datas de pagamentos...")
            paid_count = payments_df[payments_df['status'] == 'paid'].shape[0]
            
            date_counts = payments_df['payment_date'].notna().sum()
            
            print(f"Pagamentos com status 'paid': {paid_count}")
            print(f"Pagamentos com data de pagamento preenchida: {date_counts}")
            
            # Verificar se há inconsistências
            if paid_count != date_counts:
                print("\nALERTA: Inconsistência entre status 'paid' e datas de pagamento!")
                
                # Corrigir inconsistências
                if paid_count > date_counts:
                    print("Corrigindo pagamentos marcados como pagos sem data...")
                    paid_no_date = payments_df[(payments_df['status'] == 'paid') & 
                                             (payments_df['payment_date'].isna())]
                    print(f"Encontrados {len(paid_no_date)} pagamentos com status 'paid' sem data")
                    
                    # Adicionar data atual para pagamentos sem data
                    today = datetime.now().strftime('%Y-%m-%d')
                    payments_df.loc[(payments_df['status'] == 'paid') & 
                                   (payments_df['payment_date'].isna()), 
                                   'payment_date'] = today
                    payments_df.to_csv('data/payments.csv', index=False)
                    print(f"Data {today} adicionada aos pagamentos sem data. Arquivo salvo.")
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")

def fix_relatorios_file():
    """Verifica se existem arquivos .py com referências a status"""
    errors_found = False
    
    # Verificar páginas
    for root, dirs, files in os.walk("pages"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if "status" in content:
                            print(f"\nEncontrada referência a 'status' em {filepath}")
                            errors_found = True
                            with open(filepath, 'w') as fw:
                                new_content = content.replace("status", "status")
                                fw.write(new_content)
                                print(f"Arquivo {filepath} corrigido")
                except Exception as e:
                    print(f"Erro ao processar {filepath}: {str(e)}")
    
    # Verificar também na raiz
    for file in os.listdir("."):
        if file.endswith(".py") and file != "verify_payment_save.py":
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    if "status" in content:
                        print(f"\nEncontrada referência a 'status' em {file}")
                        errors_found = True
                        with open(file, 'w') as fw:
                            new_content = content.replace("status", "status")
                            fw.write(new_content)
                            print(f"Arquivo {file} corrigido")
            except Exception as e:
                print(f"Erro ao processar {file}: {str(e)}")
    
    if not errors_found:
        print("\nNenhuma referência a 'status' encontrada nos arquivos .py")
    
    return errors_found

if __name__ == "__main__":
    print("Arquivos CSV encontrados:", get_csv_files())
    print("\n--- Verificando arquivo de pagamentos ---")
    check_payments_file()
    
    print("\n--- Verificando referências a 'status' em arquivos Python ---")
    fix_relatorios_file()
    
    print("\nVerificação concluída. Execute este script no Render para corrigir o erro KeyError: 'status'.")
