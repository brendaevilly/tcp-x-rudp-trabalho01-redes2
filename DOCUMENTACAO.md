# Trabalho Redes de Computadores II — TCP vs R-UDP

Implementação da **Primeira Avaliação Redes 2 2026-1**: comparação entre transferência de arquivos via **TCP nativo** e **UDP confiável (R-UDP)** com Stop-and-Wait, simulação de rede com `tc`, métricas em Python e validação com Wireshark/tcpdump.

> **Importante:** Edite o arquivo `.env` com sua **matrícula** e **nome** antes dos testes. O hash `X-Custom-Auth` é `SHA-256(matrícula + nome)` e identifica seu tráfego no Wireshark.

---

## Estrutura do projeto

```
trabalho1-avaliacao2-redes2/
├── src/
│   ├── config.py           # Portas, .env, hash X-Custom-Auth
│   ├── metrics.py          # Log JSON de throughput e tempo
│   ├── path_setup.py       # Ajuste de PYTHONPATH
│   ├── rudp_protocol.py    # Cabeçalho binário R-UDP
│   ├── tcp_server.py       # Servidor TCP
│   ├── tcp_client.py       # Cliente TCP
│   ├── rudp_server.py      # Servidor R-UDP
│   └── rudp_client.py      # Cliente R-UDP
├── scripts/
│   ├── generate_test_file.py
│   ├── setup_tc.sh         # Cenários A, B, C com netem
│   ├── run_benchmark.sh    # 10–30 execuções automáticas
│   └── capture_traffic.sh  # tcpdump → .pcap
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── run_docker_tests.sh
├── analysis/
│   ├── analyze.py          # Pandas + Matplotlib
│   └── pcap_to_csv.py      # Exporta pcap via tshark
├── data/                   # Arquivo de teste
├── logs/                   # transfers.jsonl
├── received/               # Arquivos recebidos
├── captures/               # Arquivos .pcap
└── .env.example
```

---

## Configuração inicial

### 1. Dependências

```bash
cd "/home/brenda/Área de trabalho/trabalho1-avaliacao2-redes2"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ferramentas opcionais (host ou Docker):

- `tcpdump`, `tshark` — captura e exportação
- `iproute2` (`tc`) — simulação de perda/latência
- Docker + Docker Compose — ambiente isolado

### 2. Arquivo `.env

Exemplo:

```env
STUDENT_MATRICULA=20249007096
STUDENT_NOME=Brenda Evilyl Oliveira de Moura
```

O hash aparece ao executar:

```bash
python3 -c "import path_setup; from src.config import custom_auth_hash; print(custom_auth_hash())"
```

---

## Explicação dos códigos

### `src/config.py`

Centraliza diretórios (`logs/`, `received/`, `data/`, `captures/`), lê `.env` e calcula:

- `custom_auth_hash()` — SHA-256 em hexadecimal (campo **X-Custom-Auth** no TCP e no cabeçalho R-UDP).
- Portas padrão: TCP `5000`, R-UDP `5001`.

### `src/metrics.py`

Classe `TransferMetrics` registra por execução:

| Campo | Significado |
|--------|-------------|
| `mode` | `tcp` ou `rudp` |
| `scenario` | `A`, `B`, `C` ou `local` |
| `bytes_sent` | Tamanho do arquivo |
| `duration_s` | Tempo total |
| `throughput_mbps` | Bits/s ÷ 10⁶ |
| `retransmissions` | Retransmissões (só R-UDP) |

Grava em `logs/transfers.jsonl` (uma linha JSON por teste).

### Modo TCP (`tcp_server.py` / `tcp_client.py`)

Protocolo de aplicação em texto:

1. Linha: `X-Custom-Auth: <hash_sha256>\n`
2. Linha: `FILE <nome> <tamanho>\n`
3. Bytes brutos do arquivo
4. Servidor responde `OK\n`

O cliente mede tempo entre `connect` e recebimento do `OK`.

### Modo R-UDP (`rudp_protocol.py`, `rudp_server.py`, `rudp_client.py`)

**Stop-and-Wait** sobre UDP:

| Tipo | Valor | Uso |
|------|-------|-----|
| SYN | 1 | Início: `nome\|tamanho` |
| DATA | 2 | Bloco do arquivo (até 1024 B) |
| ACK | 3 | Confirma próximo seq esperado |
| FIN | 4 | Encerramento |

**Cabeçalho (52 bytes + payload):**

- Magic `RUDP`, versão, tipo, seq, ack, tamanho, **auth 32 bytes**, CRC32 do payload.

**Confiabilidade:**

- Cliente reenvia até receber ACK (timeout configurável).
- Servidor descarta DATA fora de ordem e reenvia ACK do seq esperado.
- Checksum CRC32 por bloco; auth inválido → pacote ignorado.

### Scripts shell

| Script | Função |
|--------|--------|
| `setup_tc.sh` | Cenário **A**: 10 ms, 0% perda; **B**: 50 ms, 5%; **C**: 100 ms, 10% |
| `run_benchmark.sh` | Várias rodadas TCP/R-UDP por cenário |
| `capture_traffic.sh` | Grava `.pcap` (portas 5000/5001) |

### `analysis/analyze.py`

Lê `logs/transfers.jsonl`, calcula **mín/média/máx/desvio padrão** da vazão (Mbps) e gera:

- `analysis/output/summary_statistics.csv`
- `throughput_comparison.png`
- `duration_boxplot.png`
- `rudp_retransmissions.png` (se houver retransmissões)

### `analysis/pcap_to_csv.py`

Exporta pacotes do `.pcap` para CSV com `tshark` e gera resumo de bytes TCP/UDP para **validação cruzada** com as métricas da aplicação.

### Docker

- **server** (`172.28.0.10`): TCP + R-UDP
- **client** (`172.28.0.20`): aplica `tc` e roda benchmark

---

## Como rodar tudo

### Teste rápido local (sem Docker)

**Terminal 1 — servidores:**

```bash
cd "/home/brenda/Área de trabalho/trabalho1-avaliacao2-redes2"
source .venv/bin/activate   # se usar venv
python3 scripts/generate_test_file.py --size 512000
python3 src/tcp_server.py
```

**Terminal 2 — servidor R-UDP:**

```bash
python3 src/rudp_server.py
```

**Terminal 3 — clientes:**

```bash
python3 src/tcp_client.py data/testfile.bin --scenario local --run-id 1
python3 src/rudp_client.py data/testfile.bin --scenario local --run-id 1
```

Arquivos recebidos em `received/`. Métricas em `logs/transfers.jsonl`.

### Simular cenários A/B/C com `tc` (Linux)

No host que envia (cliente), com interface correta (ex.: `eth0` ou `wlan0`):

```bash
sudo ./scripts/setup_tc.sh A wlp0s20f3
python3 src/tcp_client.py data/testfile.bin --scenario A --run-id 1
python3 src/rudp_client.py data/testfile.bin --scenario A --run-id 1
sudo ./scripts/setup_tc.sh clear wlp0s20f3
```

Repita para `B` e `C`.

```bash
sudo ./scripts/setup_tc.sh B wlp0s20f3
python3 src/tcp_client.py data/testfile.bin --scenario B --run-id 1
python3 src/rudp_client.py data/testfile.bin --scenario B --run-id 1
sudo ./scripts/setup_tc.sh clear wlp0s20f3
```

```bash
sudo ./scripts/setup_tc.sh C wlp0s20f3
python3 src/tcp_client.py data/testfile.bin --scenario C --run-id 1
python3 src/rudp_client.py data/testfile.bin --scenario C --run-id 1
sudo ./scripts/setup_tc.sh clear wlp0s20f3
```

### Benchmark completo (10–30 execuções)

Com servidores rodando:

```bash
./scripts/run_benchmark.sh 127.0.0.1 15
```

Gera logs e chama `analysis/analyze.py` automaticamente.

### Captura para Wireshark

**Terminal separado:**

```bash
./scripts/capture_traffic.sh any benchmark_tcp_rudp
# Execute os testes; depois Ctrl+C
```

Abra `captures/*.pcap` no Wireshark. Filtros úteis:

- `tcp.port == 5000`
- `udp.port == 5001`
- Busca por bytes do hash (Display Filter: `udp contains <hex>`)

Exportar CSV:

```bash
python3 analysis/pcap_to_csv.py captures/benchmark_tcp_rudp_XXXX.pcap
```

### Docker (recomendado para entrega)

```bash
cd docker
docker compose build
docker compose up -d
# ou benchmark automatizado:
bash run_docker_tests.sh
```

Dentro do cliente manualmente:

```bash
docker exec -it redes2-client bash
sudo /app/scripts/setup_tc.sh C eth0
python3 /app/src/rudp_client.py /app/data/testfile.bin --host 172.28.0.10 --scenario C --run-id 1
```

### Gráficos

```bash
source .venv/bin/activate
python3 analysis/analyze.py
# Saída em analysis/output/
```

---

## Cenários de rede (requisito do PDF)

| Cenário | Perda | Atraso |
|---------|-------|--------|
| A | 0% | 10 ms |
| B | 5% | 50 ms |
| C | 10% | 100 ms |

Comando: `sudo ./scripts/setup_tc.sh [A|B|C|clear] [interface]`

---

## Validação cruzada (aplicação × Wireshark)

1. Rode o cliente com log (`logs/transfers.jsonl`).
2. Capture com `tcpdump` o mesmo intervalo.
3. Compare:
   - **Bytes úteis:** tamanho do arquivo vs soma `tcp.len` / payload UDP no CSV.
   - **Tempo:** `duration_s` da aplicação vs intervalo entre primeiro e último pacote no pcap (`frame.time_relative`).
4. **Overhead R-UDP:** ~52 bytes de cabeçalho de aplicação por pacote DATA + 8 bytes UDP + 20 IP (medir no Wireshark).

### Perguntas do relatório (orientação)

1. **TCP vs R-UDP com 10% de perda (C):** TCP adapta janela/congestão; R-UDP Stop-and-Wait tende a cair a vazão e aumentar retransmissões — compare gráficos em `analysis/output/`.
2. **Overhead:** conte bytes por pacote DATA no Wireshark (cabeçalho de 52 B + UDP/IP).
3. **Discrepância de tempo:** a aplicação mede da conexão/envio SYN até OK/FIN; o Wireshark inclui handshake TCP, ARP, retransmissões e fila — pequenas diferenças são esperadas.

---

## Entrega (checklist PDF)

- [ ] Código no GitHub (este repositório)
- [ ] `.env` com sua matrícula/nome (não commitar `.env` real)
- [ ] Arquivos `.pcap` em `captures/`
- [ ] Gráficos em `analysis/output/`
- [ ] Relatório PDF (modelo SBC)
- [ ] Vídeo demonstrativo (≤ 15 min)

---

## Solução de problemas

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: src` | Execute a partir da raiz: `python3 src/tcp_client.py` (usa `path_setup.py`) |
| R-UDP timeout | Aumente `RUDP_TIMEOUT` no `.env`; confirme servidor ativo na porta 5001 |
| `tc: command not found` | `sudo apt install iproute2` |
| Permissão no `tc` | Use `sudo` ou container com `cap_add: NET_ADMIN` |
| pandas não instala | Use `python3 -m venv .venv` e `pip install -r requirements.txt` |

---

## Referência rápida de portas

| Serviço | Porta |
|---------|-------|
| TCP | 5000 |
| R-UDP | 5001 |

Bom trabalho e boa avaliação.
