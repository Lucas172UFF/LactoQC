# Documento de Arquitetura — LactoQC

**Disciplina:** Projeto de Software — UFF 2026.2
**Fase:** 1 · Checkpoint de Arquitetura
**Equipe:** Lucas Ardelino Alves da Silva, João Gabriel Pimentel, Aloysio Felipe Saad Silva, André Meschesi Dantas

| | |
|---|---|
| Estilo principal | Camadas (*layered*) |
| Estilos combinados | Ports & Adapters (hexagonal), Cliente/Servidor |
| Unidade de implantação | Monólito modular |
| ADRs | [`docs/adr/`](adr/) |

---

## 1. Escopo

### O que o sistema faz

O LactoQC é um sistema de **controle de qualidade para uma indústria de laticínios** que recebe leite em pó a granel e reenvasa o produto para diferentes marcas. Hoje esse controle é feito com registros manuais e planilhas.

O sistema cobre três momentos do processo:

| Momento | Agregado | Decisão que o sistema protege |
|---|---|---|
| Recebimento de matéria-prima | `RawMaterialReceipt` | A matéria-prima pode ou não ser usada na produção |
| Monitoramento da fábrica | `CollectionPoint` | A medição está dentro da faixa; se não, gera não conformidade |
| Controle do lote de produção | `ProductionBatch` | O lote pode ou não ser liberado |

### Para quem

| Stakeholder | O que espera do sistema |
|---|---|
| Analista de qualidade | Registrar medições e análises durante o turno, sem retrabalho de planilha |
| Supervisor de produção | Saber se um lote pode ser liberado e por que não, quando não pode |
| Auditoria / cliente da marca | Reconstituir o histórico de um lote e as não conformidades de um período |
| Equipe de desenvolvimento (4 alunos) | Evoluir três agregados em paralelo, sem conflito constante |

### O que não está no escopo da Fase 1

- Autenticação, autorização e perfis de usuário.
- Interface gráfica (a entrega é uma API REST em JSON).
- Integração com instrumentos de medição; os valores são digitados.
- Versionamento de especificações por produto (adiado para a Fase 2, conforme `PROPOSTA.md` §5).

### O que entra no desenho da arquitetura

O LactoQC é um **sistema de informação**: ele existe para registrar e proteger dados de negócio. Portanto, o módulo de persistência **faz parte da arquitetura** e aparece nos diagramas da seção 3.

---

## 2. Requisitos arquiteturais

### 2.1 Atributos de qualidade priorizados

Os três atributos abaixo estão em ordem de prioridade. A ordem é o que resolve os empates de projeto: quando dois desenhos competem, vence o que favorece o atributo mais alto.

| # | Atributo (ISO/IEC 25010:2023) | Por que é o mais importante aqui |
|---|---|---|
| **1** | **Manutenibilidade · testabilidade** | A disciplina exige TDD e a CI roda a cada PR. As regras de qualidade (faixas, aprovação, liberação de lote) precisam ser testadas sem banco, senão o ciclo de teste fica lento demais para dirigir o desenvolvimento. |
| **2** | **Manutenibilidade · modificabilidade** | Quatro pessoas evoluem três agregados em paralelo, em branches separadas, durante um semestre. O custo de adicionar um caso de uso e o custo de um merge são o gargalo real do projeto. |
| **3** | **Adequação funcional · corretude (integridade das regras)** | O sistema não é um cadastro. Se uma medição fora de faixa for gravada sem gerar não conformidade, ou um lote for liberado sem lecitinização, o sistema falha no seu propósito. |

Desempenho, escalabilidade e disponibilidade **não** são requisitos arquiteturais neste sistema: a carga é de dezenas de registros por turno, em uma única fábrica. Pelo teste prático da Aula 1 — *"se esse requisito mudasse, a estrutura do sistema mudaria?"* — eles não mudariam nada.

### 2.2 Cenários de qualidade

Cada cenário segue as seis partes: fonte, estímulo, ambiente, artefato, resposta e **medida da resposta**.

---

#### CQ-01 · Testabilidade do domínio

> **Quando** um integrante roda a suíte de testes unitários, **em** sua máquina ou na CI, **a camada de domínio deve ser exercitada sem banco de dados, sem servidor e sem rede**, **medido por**: a suíte `tests/unit` executa em menos de 1 s e `grep -rn "sqlalchemy\|flask" src/LactoQC/domain/` não retorna nenhuma linha.

| Parte | Valor |
|---|---|
| Fonte | Integrante da equipe / GitHub Actions |
| Estímulo | Execução de `pytest tests/unit` |
| Ambiente | Desenvolvimento e integração contínua |
| Artefato | `src/LactoQC/domain/model.py` |
| Resposta | Todas as regras de negócio são verificadas sem infraestrutura |
| **Medida** | **< 1 s de execução; 0 ocorrências de `sqlalchemy` ou `flask` em `domain/`** |

**Situação atual (seção 6):** 113 testes em **0,14 s**; **0** ocorrências. ✅

---

#### CQ-02 · Modificabilidade: trocar o mecanismo de persistência

> **Quando** a equipe decidir trocar o SQLite por PostgreSQL, ou substituir o SQLAlchemy, **em** qualquer momento do projeto, **nenhum arquivo de `domain/` nem de `service_layer/` deve precisar de alteração**, **medido por**: `git diff --stat` da mudança não toca `src/LactoQC/domain/`.

| Parte | Valor |
|---|---|
| Fonte | Equipe de desenvolvimento |
| Estímulo | Troca da tecnologia de persistência |
| Ambiente | Evolução do projeto (Fase 2) |
| Artefato | `adapters/orm.py`, `adapters/repository.py` |
| Resposta | A mudança fica contida nos adaptadores |
| **Medida** | **0 arquivos alterados em `domain/`** |

---

#### CQ-03 · Integridade: medição fora de faixa sempre gera não conformidade

> **Quando** um analista registra uma medição cujo valor está fora da especificação, **em** operação normal, **o sistema deve criar a não conformidade correspondente na mesma transação do registro da medição**, **medido por**: é impossível persistir uma `Measurement` sem passar por `CollectionPoint.add_measurement`, porque não existe repositório de `Measurement` — o único ponto de escrita é a Aggregate Root.

| Parte | Valor |
|---|---|
| Fonte | Analista de qualidade |
| Estímulo | Registro de medição fora da faixa da `Specification` |
| Ambiente | Operação normal |
| Artefato | Agregado `CollectionPoint` |
| Resposta | `NonConformity` criada e persistida junto com a medição |
| **Medida** | **Zero caminhos de escrita de `Measurement` fora da Aggregate Root (`grep -n "class.*MeasurementRepository" src/` → 0)** |

---

#### CQ-04 · Modificabilidade: custo de adicionar um caso de uso

> **Quando** a equipe adiciona um caso de uso novo de ponta a ponta, **em** desenvolvimento, **a mudança deve ficar contida em no máximo um arquivo por camada**, **medido por**: `git show --stat` dos commits do caso de uso toca no máximo 4 arquivos de produção.

**Situação atual (seção 6):** o caso de uso "fechar o registro diário" tocou exatamente **4 arquivos de produção, um por camada**. ✅

---

### 2.3 Restrições

Restrições também são requisitos arquiteturais: elas limitam as opções de projeto antes de qualquer decisão.

| Restrição | Origem | Efeito na arquitetura |
|---|---|---|
| Python, Flask, SQLAlchemy, SQLite | Disciplina | Elimina estilos que dependeriam de outra plataforma; SQLite em arquivo elimina implantação distribuída |
| Estrutura de diretórios `domain/`, `service_layer/`, `adapters/`, `entrypoints/` | Disciplina | **Impõe o estilo de camadas**; a decisão restante é o que vai em cada camada |
| TDD, com `tests/unit`, `tests/integration` e `tests/e2e` | Disciplina | Força o domínio a ser testável sem infraestrutura |
| Equipe de 4 pessoas, um semestre | Projeto | Elimina microsserviços e qualquer estilo com custo operacional relevante |
| Um agregado por integrante, trabalhando em paralelo | `PROPOSTA.md` §7 | Favorece fronteiras de agregado explícitas e arquivos separados por responsabilidade |
| CI obrigatória em cada PR (GitHub Actions) | `.github/workflows/ci.yml` | Suíte de testes precisa ser rápida e determinística |

### 2.4 Requisitos funcionais com impacto na estrutura

Nem todo requisito funcional é arquitetural. Estes são, porque mudam a estrutura:

| RF | Por que é arquitetural |
|---|---|
| Um lote de produção só pode usar matéria-prima aprovada | Cria uma **dependência entre dois agregados**, de dois donos diferentes. Força decidir como um agregado referencia o outro (ADR-0006) |
| Uma medição fora da especificação gera não conformidade | A não conformidade é **consequência automática**, não um cadastro. Define onde a regra mora (ADR-0005) |
| O registro diário só fecha com os três tipos de medição | A invariante depende do **conjunto** de medições → define a fronteira do agregado `CollectionPoint` |
| Consultar não conformidades por período ou origem | É uma consulta **transversal aos agregados**, que não cabe bem no padrão Repository orientado a escrita (ver seção 4, risco R-03) |

---

## 3. Arquitetura atual

### 3.1 Estilo adotado

O LactoQC usa **camadas** como estilo principal, combinado com **Ports & Adapters (hexagonal)** na fronteira com a infraestrutura, implantado como um **monólito modular**, servido em **cliente/servidor** por uma API REST.

- **Camadas** foi imposto pela restrição de estrutura de diretórios da disciplina e atende diretamente aos atributos 1 e 2 (testabilidade e modificabilidade).
- **Ports & Adapters** é o que transforma a camada em isolamento real: a camada de domínio não conhece nenhuma camada externa, e a dependência com o banco é invertida por uma interface (`AbstractCollectionPointRepository`) que o domínio/serviço define e o adaptador implementa.

Por que hexagonal e não só camadas: em camadas puras, a camada de cima depende da de baixo, e o domínio acabaria dependendo da persistência. O repositório abstrato **inverte** essa seta.

### 3.2 Visão lógica e de desenvolvimento (alto nível)

```
LEGENDA
  [ ]  usuário / ator          (  )  componente de software
  < >  sistema externo          ───▶ usa / depende de
  ⇢    implementa a interface (seta de dependência invertida)
```

```
  [Analista]   [Supervisor]   [Auditoria]
       │            │              │
       └────────────┼──────────────┘
                    │  HTTP / JSON
                    ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                     LactoQC (monólito)                       │
  │                                                              │
  │  ┌────────────────────────────────────────────────────────┐  │
  │  │  entrypoints/      ADAPTADOR PRIMÁRIO (driving)        │  │
  │  │  flask_app.py · collection_point_routes.py             │  │
  │  │  HTTP → dict · dict → JSON · exceção → código HTTP     │  │
  │  └───────────────────────────┬────────────────────────────┘  │
  │                              │ chama casos de uso            │
  │  ┌───────────────────────────▼────────────────────────────┐  │
  │  │  service_layer/     ORQUESTRAÇÃO (porta de entrada)    │  │
  │  │  services.py                                           │  │
  │  │  busca agregado · chama regra · commit                 │  │
  │  └──────────┬──────────────────────────────┬──────────────┘  │
  │             │ usa                          │ depende da      │
  │             │                              │ interface       │
  │  ┌──────────▼───────────────┐   ┌──────────▼──────────────┐  │
  │  │  domain/   NÚCLEO        │   │  AbstractRepository     │  │
  │  │  model.py                │   │  (PORTA DE SAÍDA)       │  │
  │  │                          │   │  add · get · list       │  │
  │  │  CollectionPoint   ◀─────┼───┤                         │  │
  │  │  ProductionBatch         │   └──────────▲──────────────┘  │
  │  │  RawMaterialReceipt      │              ⇢ implementa      │
  │  │                          │   ┌──────────┴──────────────┐  │
  │  │  Sem import de Flask     │   │  adapters/              │  │
  │  │  Sem import de SQLAlchemy│   │  ADAPTADOR SECUNDÁRIO   │  │
  │  └──────────▲───────────────┘   │  repository.py · orm.py │  │
  │             │                   └──────────┬──────────────┘  │
  │             └── mapeia (imperativo) ────────┘                │
  └───────────────────────────────────┬──────────────────────────┘
                                      │ SQL
                                      ▼
                              < SQLite / lactoqc.db >
```

**A seta que define a arquitetura** é a que vai de `adapters/` para `AbstractRepository`: a infraestrutura depende da abstração, não o contrário. É por isso que `domain/` não importa SQLAlchemy.

### 3.3 Onde cada elemento está no código

| Elemento da arquitetura | Arquivo | Linhas |
|---|---|---|
| Entidades, objetos de valor e agregados | `src/LactoQC/domain/model.py` | 302 |
| Casos de uso (porta de entrada) | `src/LactoQC/service_layer/services.py` | 327 |
| Contrato do repositório (porta de saída) | `src/LactoQC/adapters/repository.py` | 91 |
| Mapeamento objeto-relacional (adaptador) | `src/LactoQC/adapters/orm.py` | 191 |
| Composição da aplicação e sessão por requisição | `src/LactoQC/entrypoints/flask_app.py` | 84 |
| Rotas REST do Ponto de Coleta (adaptador primário) | `src/LactoQC/entrypoints/collection_point_routes.py` | 150 |
| Rotas REST do Lote de Produção (adaptador primário) | `src/LactoQC/entrypoints/production_batch_routes.py` | 329 |

### 3.4 Padrões táticos de DDD em uso

| Padrão | Onde | Observação |
|---|---|---|
| **Aggregate Root** | `CollectionPoint`, `ProductionBatch` | Única porta de escrita das coleções filhas |
| **Entidade** | `Measurement`, `WeightSample`, `NonConformity` | Possuem `id_` |
| **Objeto de valor** | `Specification`, `DailyClosure`, `Lecithinization` | Sem identidade no domínio; chave substituta mapeada em `_id` (ADR-0001) |
| **Repository** | `AbstractCollectionPointRepository`, `AbstractProductionBatchRepository` | Um por agregado (ADR-0002) |
| **Service layer** | `services.py` | Orquestra; não contém regra de negócio |

### 3.5 Visão de processo e física (resumo)

Deliberadamente simples, porque desempenho e disponibilidade não são requisitos arquiteturais (§2.1):

| Visão | Conteúdo |
|---|---|
| **Processo** | Um processo Flask, síncrono, uma *thread* por requisição. Uma sessão SQLAlchemy por requisição, criada sob demanda em `get_session()` e fechada em `teardown_appcontext` (`flask_app.py:35-39`). Sem concorrência entre agregados. |
| **Física** | Um único artefato implantável + um arquivo SQLite (`DATABASE_URL`, padrão `sqlite:///lactoqc.db`). Sem balanceador, sem réplica, sem fila. |
| **Cenários (+1)** | Os casos de uso da `PROPOSTA.md` §6, cobertos por `tests/e2e`. |

### 3.6 Táticas arquiteturais empregadas

Tática ≠ tecnologia. As táticas abaixo continuam valendo se trocarmos Flask, SQLAlchemy ou SQLite.

| Atributo | Tática | Decisão concreta no LactoQC |
|---|---|---|
| Testabilidade | Limitar a complexidade | Domínio puro, sem I/O; regras verificáveis em memória |
| Testabilidade | Controlar e observar o estado | `FakeCollectionPointRepository` e `FakeSession` em `tests/conftest.py`; `create_app(session_factory)` recebe a fábrica de sessão nos testes |
| Modificabilidade | Usar intermediários | `AbstractCollectionPointRepository` entre o serviço e o banco |
| Modificabilidade | Adiar decisões de vínculo | *App factory* escolhe o engine em tempo de execução (`flask_app.py:22-32`) |
| Modificabilidade | Encapsular | Blueprint por agregado; cada integrante mexe no seu arquivo de rotas |
| Integridade | Encapsular o estado | Coleções filhas só mudam por métodos da Aggregate Root |
| Integridade | Detectar e registrar | `check_for_non_conformity` e `_register_non_conformity` registram em vez de abortar (ADR-0005) |
| Integridade | Validar na entrada | Invariantes verificadas no construtor (ADR-0006) e `UNIQUE (collection_point_id, day)` no banco |

---

## 4. Trade-offs

Lembrando as definições da Aula 2:
**Ponto de sensibilidade** = decisão que afeta um atributo. **Ponto de trade-off** = decisão que melhora um atributo e piora outro. **Risco** = decisão que pode comprometer um atributo.

### 4.1 O que a arquitetura ganha e perde, por atributo

| Atributo | Ganha | Perde |
|---|---|---|
| Testabilidade | 113 testes de domínio em 0,14 s, sem banco | Precisa manter dublês (`Fake*`) sincronizados com os contratos reais |
| Modificabilidade | Um caso de uso = 1 arquivo por camada; os 4 integrantes raramente colidem | Um caso de uso = **4** arquivos; a mudança mais simples atravessa tudo |
| Integridade | Nenhum caminho de escrita contorna a Aggregate Root | As invariantes do construtor **não** são reaplicadas na carga do banco (R-02) |
| Simplicidade | — | `orm.py` tem 191 linhas só para mapear 302 linhas de domínio |
| Desempenho | Irrelevante nesta escala | Consulta de não conformidades é O(n) em memória (R-03) |

### 4.2 Pontos de trade-off

#### PT-01 — Mapeamento imperativo do ORM: testabilidade × simplicidade

**Decisão.** O domínio não herda de `Base` nem importa SQLAlchemy; o mapeamento vive em `adapters/orm.py` e só é ativado por `start_mappers()` (ADR-0001).

| Melhora | Piora |
|---|---|
| **Testabilidade** — `tests/unit` roda sem banco em 0,14 s | **Simplicidade** — `orm.py` repete a estrutura das classes em 191 linhas |
| **Modificabilidade** — trocar o banco não toca `domain/` | **Simplicidade** — objetos de valor precisam de chave substituta em `_id` |

Com o modelo declarativo (herdar de `Base`), `orm.py` quase desapareceria — mas o domínio passaria a importar SQLAlchemy e o cenário CQ-01 deixaria de ser verificável. Pela ordem de prioridade da §2.1, testabilidade vence simplicidade. **Decisão mantida.**

#### PT-02 — Quatro camadas: modificabilidade × custo por mudança

**Decisão.** HTTP, orquestração, regra e persistência em camadas separadas.

| Melhora | Piora |
|---|---|
| **Modificabilidade** — cada mudança fica contida; merges entre 4 pessoas ficam baratos | **Simplicidade / esforço** — o caso de uso mais trivial custa 4 arquivos |

**Evidência medida (§6.3):** adicionar "fechar o registro diário" exigiu 4 commits, 4 arquivos de produção e 82 linhas de produção — contra 327 linhas de teste. O custo é real e foi aceito conscientemente.

#### PT-03 — Agregado carregado inteiro: integridade × desempenho

**Decisão.** Não existe repositório de `Measurement` nem de `NonConformity`; tudo é carregado e salvo pela Aggregate Root (ADR-0002).

| Melhora | Piora |
|---|---|
| **Integridade** — impossível gravar uma medição sem a verificação de especificação | **Desempenho** — `list_non_conformities` carrega *todos* os pontos de coleta, com todas as suas medições, e filtra em Python |

Hoje o custo é invisível (dezenas de registros). Com um ano de histórico, passa a ser o primeiro gargalo. É um trade-off **consciente e datado**, não um descuido.

### 4.3 Pontos de sensibilidade

| # | Decisão | Atributo sensível |
|---|---|---|
| PS-01 | Granularidade do agregado `CollectionPoint` | Quanto maior o agregado, maior a integridade e menor o desempenho de leitura |
| PS-02 | Local do `commit()` (service layer, ADR-0003) | Define a fronteira transacional: tudo que o caso de uso tocou sobe ou desce junto |
| PS-03 | Mapeamento de `ValueError` → 422 e `LookupError` → 404 (ADR-0004) | Qualquer `ValueError` acidental vira 422; mascara bug como erro de negócio |

### 4.4 Riscos

#### R-01 — `start_mappers()` é estado global: um erro de mapeamento derruba tudo · **severidade alta, já materializado uma vez**

O registro de mapeadores é global ao processo. Mapear a mesma classe duas vezes é um erro irrecuperável, e o efeito não fica contido no agregado que errou.

**O risco já se materializou.** Até o commit `d5d0ee5`, `src/LactoQC/adapters/orm.py:167` trazia:

```python
mapper_registry.map_imperatively(RawMaterialReceipt, weight_samples)   # deveria ser WeightSample
```

`RawMaterialReceipt` já havia sido mapeada cinco linhas acima. Resultado medido na época:

```
$ pytest tests/integration -q
8 passed, 18 errors in 0.65s
sqlalchemy.exc.ArgumentError: Class 'RawMaterialReceipt' already has a primary mapper defined.
```

As 18 falhas estavam **todas** no agregado Lote de Produção, mas a causa era a natureza global do registro: `start_mappers_production_batch()` não conseguia sequer terminar. Um erro de uma linha, em um agregado, parava a inicialização do sistema inteiro.

**Corrigido no commit `7ab94f5`**, com a troca da classe para `WeightSample`. A suíte está verde: `173 passed`.

**O risco estrutural permanece**, e com duas agravantes novas:

1. Hoje são **duas** funções de mapeamento (`start_mappers()` e `start_mappers_production_batch()`), chamadas em sequência em `flask_app.py:28-29` e em `tests/conftest.py:57-58`. Cada agregado novo acrescenta uma, e nenhuma é idempotente.
2. Os testes que detectaram o erro — `tests/integration/test_orm_production_batch.py` e `tests/integration/test_repository_production_batch.py` — **foram removidos** na mesma faixa de commits (ver R-05). O mapeamento do Lote de Produção hoje só é exercitado indiretamente, pelos testes e2e.

**Mitigação proposta:** unificar as duas funções em um único `start_mappers()` idempotente, que verifique `mapper_registry.mappers` antes de mapear.

#### R-02 — O SQLAlchemy não executa `__init__` ao carregar do banco · **severidade média**

Todas as invariantes do projeto são verificadas em construtores: `Measurement._verify_unit`, `Specification._verify_min_max_values`, `CollectionPoint._validate_specifications`, `ProductionBatch._verify_raw_material_approved`. Ao **ler** do banco, o SQLAlchemy reconstrói o objeto sem chamar `__init__` — nenhuma dessas verificações roda.

Se um registro inconsistente entrar no banco por fora da aplicação (script, correção manual, migração), ele será carregado sem protesto. Isso ataca diretamente o atributo 3 da §2.1.

**Mitigação:** o banco é a última linha de defesa, mas hoje só há uma restrição declarada (`UNIQUE (collection_point_id, day)` em `daily_closures`). Faltam `CHECK (min_value <= max_value)` e `UNIQUE (collection_point_id, measurement_type)` em `specifications`.

#### R-03 — Consulta transversal carregada em memória · **severidade baixa hoje, cresce com o tempo**

`services.list_non_conformities` (`services.py:102-115`) chama `repo.list()` e filtra em Python. Com o histórico de uma fábrica real, isso carrega todo o banco a cada requisição de relatório.

**Mitigação:** separar uma porta de **consulta** (modelo de leitura) do repositório de escrita, mantendo o padrão Repository apenas para a transação.

#### R-04 — Exceção não tratada vira HTTP 500 · **severidade baixa, confirmado**

Em `collection_point_routes.py:13-17`, `_parse_date` captura `TabError` onde deveria capturar `TypeError`:

```python
except (TabError, ValueError):
```

`_require(body, "date")` garante que a chave existe, mas não que o valor não é nulo. Com `{"date": null}`, `date.fromisoformat(None)` lança `TypeError` — que não é subclasse de `TabError` — e a requisição retorna **500** em vez de 400. Verificado:

```
$ python -c "from datetime import date; date.fromisoformat(None)"
TypeError: fromisoformat: argument must be str
```

É um erro de digitação, mas ilustra o ponto de sensibilidade PS-03: o tratamento de erro centralizado só funciona para as exceções que ele realmente prevê.

#### R-05 — A camada de adaptadores do Lote de Produção perdeu seus testes de integração · **severidade média, novo**

A pirâmide de testes da disciplina atribui um papel a cada nível: `tests/unit` cobre o domínio sem infraestrutura, `tests/integration` cobre o **mapeamento e o repositório** contra um banco real, e `tests/e2e` cobre a API.

Para o Lote de Produção, o nível do meio não existe mais:

```
$ git diff --stat d5d0ee5 HEAD -- tests/integration/
 tests/integration/conftest.py                      |  23 -
 tests/integration/test_orm_production_batch.py     | 101 -----
 tests/integration/test_repository_production_batch.py |  71 ---
```

São exatamente os arquivos que haviam detectado o R-01. A suíte de integração que restou cobre apenas o Ponto de Coleta:

```
$ ls tests/integration/
test_orm.py   test_repository.py
```

**Por que importa.** O mapeamento imperativo (ADR-0001) tem um custo específico: `orm.py` repete a estrutura das classes, e nada no interpretador avisa quando as duas se desencontram. O teste de integração — que grava com o ORM e confere com SQL puro, e que carrega o agregado em uma **segunda sessão** para não ler do *identity map* — é a única verificação dessa correspondência. Sem ele, um atributo não mapeado em `ProductionBatch` volta `None` do banco silenciosamente.

**Atenuante.** Os 43 testes e2e exercitam o mapeamento de forma indireta, porque `tests/conftest.py:83-84` chama as duas funções de mapeamento antes de criar o cliente. A cobertura não é zero — mas é acidental, e um teste e2e que falha não diz *qual* coluna está errada.

**Mitigação proposta:** restaurar os dois arquivos de integração, ou reescrevê-los, antes de fechar a Fase 1. É o ponto mais barato de recuperar entre todos os riscos listados.

---

## 5. Alternativa arquitetural

> *Outra arquitetura seria melhor para este domínio? Qual escolheríamos hoje?*

### 5.1 Alternativas consideradas

#### A) Transaction Script / CRUD em camada fina

Flask com SQLAlchemy declarativo, regras direto nas rotas ou em funções de serviço, sem agregados.

| Favorece | Prejudica |
|---|---|
| Simplicidade: `orm.py` e `repository.py` desaparecem | Testabilidade: toda regra exigiria banco |
| Velocidade inicial de entrega | Integridade: as regras se espalham pelas rotas e se duplicam |

**Rejeitada.** A `PROPOSTA.md` §2 é explícita: *"o sistema não é apenas um cadastro"*. Os slides da Aula 2 colocam exatamente este caso no "quando **não** usar hexagonal" — e o LactoQC está do outro lado da linha, com as vinte regras de negócio listadas na `PROPOSTA.md` §4.

#### B) Microsserviços — um serviço por agregado

Um serviço para Recebimento, um para Ponto de Coleta, um para Lote de Produção.

| Favorece | Prejudica |
|---|---|
| Isolamento de times: cada integrante implanta o seu | Complexidade operacional: 3 serviços, 3 bancos, rede |
| Escalabilidade independente | Consistência: "lote só usa matéria-prima aprovada" viraria chamada remota |

**Rejeitada pelas restrições.** Pela tabela de comparação da Aula 2: *4 pessoas, um semestre* → "dificilmente cabe". E o ganho de escalabilidade responde a um requisito que o LactoQC não tem.

#### C) Arquitetura orientada a eventos entre os agregados

Manter o monólito, mas comunicar os agregados por eventos de domínio (`MedicaoForaDaFaixaRegistrada`, `RecebimentoAprovado`).

| Favorece | Prejudica |
|---|---|
| Desacoplamento entre os três agregados, de três donos | Consistência eventual em decisões que precisam ser síncronas |
| Extensibilidade: novos consumidores sem tocar no produtor | Rastreabilidade: fica mais difícil depurar e auditar |

**Parcialmente rejeitada.** Aprovar ou reprovar um lote é uma decisão síncrona: o supervisor precisa da resposta na requisição. Mas há **um** ponto onde eventos caberiam bem: a notificação de não conformidade para fora do agregado. Fica registrado como caminho para a Fase 2.

### 5.2 O que escolheríamos hoje

**Manteríamos camadas + Ports & Adapters.** A arquitetura atual atende aos três atributos priorizados, e a evidência da §6 confirma: domínio sem infraestrutura, testes unitários em 0,14 s e um caso de uso contido em um arquivo por camada.

Faríamos **três ajustes**, todos internos ao estilo escolhido:

| # | Ajuste | Atributo que resolve | Risco endereçado |
|---|---|---|---|
| 1 | **Unit of Work explícito** no lugar de passar `Session` ao service layer | Modificabilidade — hoje `services.py:7` importa `sqlalchemy.orm.Session`, o único vazamento de infraestrutura acima dos adaptadores | PS-02 |
| 2 | **Porta de consulta separada** do repositório de escrita | Desempenho, sem sacrificar integridade | R-03 |
| 3 | **Um único `start_mappers()` idempotente**, com as restrições de integridade declaradas no esquema | Integridade e confiabilidade | R-01, R-02 |

O ajuste 1 é o mais relevante arquiteturalmente: é o que fecha o hexágono. Hoje o domínio está limpo, mas o service layer ainda sabe que existe um SQLAlchemy do outro lado.

---

## 6. Evidências

Todas as medidas foram coletadas na branch `main`, no commit `723e339` (22/10/2026). Cada afirmação traz o comando que a produz.

### 6.1 O domínio não depende da infraestrutura

```
$ grep -rn "sqlalchemy\|flask" src/LactoQC/domain/
(nenhuma ocorrência)

$ grep -rn "flask" src/LactoQC/service_layer/
(nenhuma ocorrência)

$ grep -rn "sqlalchemy" src/LactoQC/service_layer/
src/LactoQC/service_layer/services.py:7:from sqlalchemy.orm import Session
```

**Leitura.** `domain/` está completamente limpo — o cenário CQ-01 é atendido. O service layer está limpo de Flask, mas **importa `Session`** do SQLAlchemy. É uma anotação de tipo, não uma chamada, mas é um acoplamento real de compilação: é exatamente o que o ajuste 1 da §5.2 remove.

### 6.2 Testes de domínio são ordens de grandeza mais rápidos que e2e

```
$ pytest -q
173 passed in 0.73s
```

| Suíte | Testes | Tempo | Tempo por teste | Razão vs. unitários |
|---|---|---|---|---|
| `tests/unit` | 113 | **0,14 s** | 1,2 ms | 1× |
| `tests/integration` | 17 | 0,13 s | 7,6 ms | **6×** |
| `tests/e2e` | 43 | 0,47 s | 10,9 ms | **9×** |

Medições estáveis em três execuções consecutivas de cada suíte.

**Leitura.** A comparação justa é por teste, não por suíte: um teste unitário custa **1,2 ms**; um e2e custa **9× mais**. É isso que torna o TDD praticável — o ciclo escrever-rodar-corrigir é instantâneo.

Nenhum teste unitário toca o banco, o que mantém o cenário CQ-01 atendido:

```
$ grep -rn "in_memory_db\|session_factory\|sqlite" tests/unit/
(nenhuma ocorrência)
```

A suíte unitária subiu de 0,02 s para 0,14 s desde `d5d0ee5`. O aumento é de **importação e coleta** dos arquivos de teste novos (`test_production_batch_services.py`, 490 linhas), não de I/O: o teste mais lento leva 0,01 s, e é *setup*.

### 6.3 Adicionar um caso de uso toca um arquivo por camada

Caso de uso 7 da `PROPOSTA.md` — *fechar o registro diário de monitoramento*:

```
$ git show --stat 56bdff3 36ba11e 95abde2 e35eb96
```

| Commit | Camada | Arquivo de produção | Linhas prod. | Linhas teste |
|---|---|---|---|---|
| `56bdff3` | Domínio | `domain/model.py` | +35 | +141 |
| `36ba11e` | Adaptador | `adapters/orm.py` | +18 | +38 |
| `95abde2` | Serviço | `service_layer/services.py` | +10 | +60 |
| `e35eb96` | Entrypoint | `entrypoints/collection_point_routes.py` | +19 | +88 |
| | **Total** | **4 arquivos** | **82** | **327** |

**Leitura.** O cenário CQ-04 é atendido: exatamente um arquivo por camada, nenhum vazamento. É também a medida do custo do PT-02 — 4 commits para uma funcionalidade, e **4 linhas de teste para cada linha de produção**.

**Segunda medida, mais forte.** O commit `d98d499` levou o agregado Lote de Produção ao ar inteiro — 6 casos de uso e 329 linhas de rotas:

```
$ git show --stat d98d499
 src/LactoQC/entrypoints/production_batch_routes.py | 330 +++++
 src/LactoQC/service_layer/services.py              | 217 +++--
 src/LactoQC/entrypoints/flask_app.py               |   3 +
 tests/...                                          | 865 +++++
```

Zero linhas em `domain/` e zero em `adapters/`. O domínio e o mapeamento já estavam prontos desde os checkpoints anteriores, e expor um agregado inteiro pela API **não exigiu tocá-los**. É a demonstração mais direta de que as camadas estão isolando de verdade: a mudança parou exatamente na fronteira prevista.

O contraponto honesto é o processo, não a arquitetura: foi um único commit de 1.411 linhas, contra os 4 commits incrementais do fechamento diário. A arquitetura conteve a mudança; a disciplina de commits não.

### 6.4 O custo do mapeamento imperativo

```
$ wc -l src/LactoQC/adapters/orm.py src/LactoQC/domain/model.py
     191 src/LactoQC/adapters/orm.py
     302 src/LactoQC/domain/model.py
```

**Leitura.** O mapeamento custa **191 linhas, 63% do tamanho do domínio que ele mapeia** — e essas linhas repetem a estrutura das classes. É o preço concreto do PT-01, e o argumento mais forte a favor do modelo declarativo. A §6.1 é o contra-argumento que venceu.

### 6.5 Distribuição do código e dos testes

```
$ find src -name "*.py" | xargs wc -l   → 1.474 linhas
$ find tests -name "*.py" | xargs wc -l → 2.516 linhas
```

| Camada | Linhas | % | Em `d5d0ee5` |
|---|---|---|---|
| `entrypoints/` | 563 | **38%** | 231 (25%) |
| `service_layer/` | 327 | 22% | 116 (12%) |
| `domain/` | 302 | 20% | 302 (32%) |
| `adapters/` | 282 | 19% | 282 (30%) |

**Razão testes/produção: 1,71 : 1.**

**Leitura — e a distribuição se inverteu.** No checkpoint anterior o domínio era a maior camada (32%). Hoje é a **terceira** (20%), e `entrypoints/` passou a ser a maior (38%). O domínio não encolheu: as outras cresceram em volta dele.

A causa é concreta e não é um defeito: expor o Lote de Produção custou 329 linhas de rotas e 217 de serviço para um agregado cujo domínio já estava escrito. Serialização para JSON, parsing de entrada e tradução de erro são código de adaptador, e adaptador é verboso.

Mas vale como **sinal de vigilância** para a Fase 2. Em um sistema cujo valor está nas regras, uma camada de rotas quase duas vezes maior que o domínio merece a pergunta: isso é só serialização, ou já há regra de negócio vazando para cima? Vale um `grep` por `if` em `production_batch_routes.py` antes de fechar a fase.

O service layer continua sendo a camada que mais confirma o projeto: 22% do código, 8 chamadas de `session.commit()` e **zero** regra de negócio — ele busca o agregado, chama um método e confirma a transação.

### 6.6 Nenhum caminho de escrita contorna a Aggregate Root

```
$ grep -n "class.*Repository" src/LactoQC/adapters/repository.py
9:class AbstractCollectionPointRepository(ABC)
24:class SqlAlchemyCollectionPointRepository(...)
43:class AbstractProductionBatchRepository(ABC)
58:class SqlAlchemyProductionBatchRepository(...)
77:class FakeProductionBatchRepository(...)
```

**Leitura.** Existem repositórios apenas para as duas Aggregate Roots. Não há `MeasurementRepository` nem `NonConformityRepository` — o cenário CQ-03 é estrutural, não depende de disciplina do programador.

### 6.7 Distribuição do trabalho entre a equipe

```
$ git shortlog -sne --all
```

| Integrante | Commits |
|---|---|
| João Gabriel Pimentel | 34 |
| Aloysio Felipe Saad Silva | 21 |
| Lucas Ardelino Alves da Silva | 11 |
| André Meschesi Dantas | 7 |

**Leitura.** Em 73 commits sobre quatro agregados em paralelo, a arquitetura em camadas com **um arquivo de rotas por agregado** manteve os conflitos de merge concentrados em dois arquivos compartilhados — `orm.py` e `model.py` — exatamente como registrado em `DECISIONS.md`.

O blueprint por agregado é a decisão que mais paga aqui: `collection_point_routes.py` e `production_batch_routes.py` evoluíram em branches diferentes, por autores diferentes, sem um único conflito. Os conflitos que houve foram nos dois arquivos que a estrutura da disciplina obriga a compartilhar.

---

## 7. ADRs

Cada ADR registra **uma única decisão**: contexto, decisão, alternativas e consequências. Os ADRs não são editados: se uma decisão mudar, escreve-se um novo que substitui o anterior.

| ADR | Decisão | Autor | Status |
|---|---|---|---|
| [0001](adr/0001-dominio-independente-do-orm.md) | Manter o domínio independente do ORM com mapeamento imperativo | João Gabriel Pimentel | Aceito |
| [0002](adr/0002-um-repositorio-por-agregado.md) | Um repositório por agregado, com a Aggregate Root como fronteira de persistência | João Gabriel Pimentel | Aceito |
| [0003](adr/0003-commit-no-service-layer.md) | O commit da transação pertence ao service layer | André Meschesi Dantas | Aceito |
| [0004](adr/0004-excecoes-de-dominio-como-codigos-http.md) | Traduzir exceções de domínio em códigos HTTP no entrypoint | André Meschesi Dantas | Aceito |
| [0005](adr/0005-nao-conformidade-registrada-nao-lancada.md) | Não conformidade é registrada pelo agregado, não lançada como exceção | Aloysio Felipe Saad Silva | Aceito |
| [0006](adr/0006-invariantes-validadas-no-construtor.md) | Invariantes do agregado validadas no construtor | Lucas Ardelino Alves da Silva | Aceito |

Modelo para novos ADRs: [`adr/0000-template.md`](adr/0000-template.md).

---

## Referências

- Bass, L.; Clements, P.; Kazman, R. *Software Architecture in Practice*, 3ª ed., 2012. (cenários de qualidade em seis partes; táticas)
- Kruchten, P. "Architectural Blueprints — The 4+1 View Model of Software Architecture", 1995. (visões)
- ISO/IEC 25010:2023. (vocabulário de atributos de qualidade)
- Cockburn, A. "Hexagonal Architecture", 2005. (ports & adapters)
- Percival, H.; Gregory, B. *Architecture Patterns with Python*, 2020. (domínio independente do ORM, Repository, service layer)
- Nygard, M. "Documenting Architecture Decisions", 2011. (formato do ADR)
- Neves, V. O. *Arquitetura de Software* — Aulas 1 e 2, Projeto de Software, UFF, 2026.2.
