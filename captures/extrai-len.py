import pandas as pd

# Ler o CSV
df = pd.read_csv('captures/tcp-len-C.csv')

# Criar coluna Len extraindo apenas o número após "Len="
df['Len'] = (
    df['Info']
    .str.extract(r'Len=(\d+)')[0]
    .fillna(0)      # coloca 0 quando não existe Len=
    .astype(int)
)

# Salvar o resultado (opcional)
df.to_csv('captures/tcp-len-C-com-len.csv', index=False)

# Visualizar
print(df.head())

soma_tcp = df['Len'].sum()
print(soma_tcp)