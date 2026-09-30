---

## Checkpoint 2 — Repositórios

**Tag:** `fase1-checkpoint-2`  
**Semana:** 3

### Objetivo do checkpoint

- criar `adapters/repository.py` com a abstração de repositório;
- implementar o repositório real com SQLAlchemy/SQLite para cada agregado modelado;
- utilizar um FakeRepository nos testes;
- cobrir os repositórios reais com testes em `tests/integration`.

---

## João Gabriel Pimentel — Agregado Ponto de Coleta

### O que foi implementado

- `AbstractCollectionPointRepository`, contrato com as operações `add`, `get`
  e `list`;
- `SqlAlchemyCollectionPointRepository`, implementação real sobre uma sessão
  do SQLAlchemy;
- `FakeCollectionPointRepository`, implementação em memória para os testes;
- mapeamento imperativo do agregado em `adapters/orm.py`, com as tabelas
  `collection_points`, `specifications`, `measurements` e `non_conformities`;
- fixtures de banco SQLite em memória no `tests/conftest.py`;
- testes de integração do ORM e do repositório.

### Testes

Os testes de integração verificam:

- gravação do ponto de coleta e de suas specifications, conferida com SQL puro;
- carregamento do ponto de coleta a partir de linhas inseridas com SQL puro;
- gravação da não conformidade associada à medição que a gerou;
- recuperação do agregado completo em uma nova sessão;
- retorno de `None` para um identificador inexistente;
- listagem ordenada dos pontos de coleta.

Os testes que recuperam o agregado utilizam duas sessões distintas, para
garantir que os dados vêm do banco e não do mapa de identidade da sessão.

### Arquivos trabalhados

- `src/LactoQC/adapters/repository.py`
- `src/LactoQC/adapters/orm.py`
- `tests/conftest.py`
- `tests/unit/test_collection_point_repository.py`
- `tests/integration/test_orm.py`
- `tests/integration/test_repository.py`
- `requirements.txt`

### Commits de autoria

- `cb4a3ce` — `feat: adiciona contrato do repositório e fake do ponto de coleta`
- `8de6a6b` — `feat: adiciona ORM e repositório SQLAlchemy do ponto de coleta`

### Decisões de projeto

#### Um repositório por agregado

Foi criado apenas o repositório do `CollectionPoint`. Medições, specifications
e não conformidades são salvas e carregadas junto com a Aggregate Root.

Essa decisão impede que uma `Measurement` seja persistida sem passar por
`add_measurement`, o que ignoraria a verificação da specification e a geração
da não conformidade.

#### Mapeamento imperativo

Foi utilizado o mapeamento imperativo do SQLAlchemy (`map_imperatively`) em vez
do declarativo.

Dessa forma, as classes de `domain/model.py` não herdam de nenhuma classe do
SQLAlchemy e o domínio permanece independente da infraestrutura. O mapeamento
só é ativado por `start_mappers()`, o que mantém os testes unitários do
domínio sem banco.

#### Chave substituta para a Specification

A `Specification` não possui identificador no domínio, pois é tratada como
objeto de valor. A tabela `specifications` recebe uma chave própria, mapeada
no atributo privado `_id`, para não se confundir com o `id_` das entidades.

#### Numeração da NonConformity

O `id_` da `NonConformity` é gerado como `len(non_conformities) + 1` e, portanto,
se repete entre pontos de coleta diferentes.

Por isso, esse valor é gravado na coluna `number` e a tabela possui uma chave
primária própria.

#### Repositório sem commit

O repositório apenas adiciona e recupera objetos da sessão. A confirmação da
transação fica a cargo de quem utiliza o repositório: os testes neste
checkpoint e o service layer na entrega.

#### Enums persistidos pelo nome

`MeasurementType` e `MeasurementUnit` são gravados pelo nome do membro
(`CHLORINE`, `MG_L`). A unidade é anulável, pois a medição de pH não possui
unidade.

### Dificuldades encontradas

- compreender o funcionamento do `start_mappers()` e do mapeamento automático
  de colunas com o mesmo nome dos atributos;
- entender que o SQLAlchemy não executa o `__init__` ao carregar objetos, de
  modo que todo atributo do agregado precisa estar mapeado;
- conflito no `orm.py` ao integrar a branch com a `main`, pois outro integrante
  havia criado uma versão com modelo de persistência diferente;
- após o merge, alterações enviadas diretamente para a `main` deixaram a CI
  vermelha. A correção foi feita no PR #8, que restaurou o repositório com
  mapeamento imperativo, unificou o service layer em `services.py`, criou a
  fixture `client` para os testes e2e e removeu os arquivos `__pycache__` do
  versionamento.

Commits da correção:

- `c63a193` — `fix: restaura repositório SQLAlchemy do ponto de coleta`
- `6c41caa` — `refactor: unifica service layer em services.py e usa o repositório SQLAlchemy nas rotas`
- `74132aa` — `test: adiciona fixture client para os testes e2e`
- `19f1eea` — `chore: remove __pycache__ do versionamento`
- `5eadb45` — `fix: corrige nomes do repositório no service layer e nas rotas`

---

## Entrega da Fase 1 — Service layer e API

**Tag:** `fase1-entrega`  
**Semana:** 4

### Objetivo

- orquestrar os casos de uso em `service_layer/services.py`;
- disponibilizar os endpoints correspondentes na API Flask;
- cobrir a API com testes e2e;
- completar a estrutura exigida para a Fase 1.

---

## João Gabriel Pimentel — Agregado Ponto de Coleta

### O que foi implementado

#### Unificação do domínio em `model.py`

O domínio foi unificado em um único arquivo `src/LactoQC/domain/model.py`,
conforme a estrutura exigida. Antes existiam `models.py`, com o conteúdo, e
`model.py`, que apenas reexportava o primeiro.

#### Testes do service layer com o FakeRepository

O `FakeCollectionPointRepository` foi movido para o `tests/conftest.py` e
passou a simular o autoincremento de identificadores, pois o service cria o
ponto de coleta com `id_=None`, como ocorre com o banco.

Também foi criado um `FakeSession`, que registra se o `commit()` foi chamado.

Os testes verificam, sem banco de dados:

- criação do ponto de coleta com commit;
- ausência de commit quando falta alguma specification;
- registro de medição dentro e fora da faixa;
- conversão do rótulo do tipo de medição (`"Cloro"`) para o enum;
- erro `LookupError` para ponto de coleta inexistente;
- filtros de não conformidades por ponto de coleta e por período.

#### Caso de uso: fechar o registro diário de monitoramento

Foi implementado o caso de uso 7 da proposta, em todas as camadas:

- **domínio:** classe `DailyClosure` e método `CollectionPoint.close_day`;
- **ORM:** tabela `daily_closures`;
- **service:** `close_daily_record`;
- **API:** `POST /collection-points/<id>/daily-closures`, que recebe
  `{"date": "AAAA-MM-DD"}`. O detalhe do ponto de coleta passou a listar os
  dias fechados.

Casos de uso do Ponto de Coleta disponíveis no service layer:

1. criar ponto de coleta;
2. consultar ponto de coleta;
3. registrar medição, com verificação da specification e geração de não
   conformidade;
4. consultar não conformidades por período ou por ponto de coleta;
5. fechar o registro diário de monitoramento.

### Testes

- **unitários do domínio:** fechamento de dia completo; recusa de dia
  incompleto; desconsideração de medições de outros dias; recusa de fechamento
  duplicado; recusa de medição em dia fechado; aceitação de medição em outro
  dia; ponto de coleta novo sem dias fechados;
- **service com fake:** fechamento com commit; dia incompleto sem commit; ponto
  inexistente; medição recusada em dia fechado, sem commit;
- **integração:** persistência do fechamento e aplicação da regra em um ponto
  de coleta carregado do banco;
- **e2e:** respostas 201, 422 (dia incompleto, fechamento duplicado, data
  inválida, medição em dia fechado), 400 (sem data) e 404 (ponto inexistente).

### Arquivos trabalhados

- `src/LactoQC/domain/model.py`
- `src/LactoQC/adapters/orm.py`
- `src/LactoQC/service_layer/services.py`
- `src/LactoQC/entrypoints/collection_point_routes.py`
- `tests/conftest.py`
- `tests/unit/test_collection_point.py`
- `tests/unit/test_collection_point_repository.py`
- `tests/unit/test_collection_point_services.py`
- `tests/integration/test_repository.py`
- `tests/e2e/test_collection_points_api.py`
- `DECISIONS.md`

### Commits de autoria

- `c4ce266` — `style: remove comentário do mapeamento de unidades`
- `2919fc4` — `refactor: unifica o domínio em model.py conforme estrutura exigida`
- `7f64f06` — `test: move fake repository para o conftest e simula autoincremento`
- `15473f3` — `test: adiciona testes do service layer do ponto de coleta com fake repository`
- `56bdff3` — `feat: adiciona fechamento do registro diário no domínio do ponto de coleta`
- `36ba11e` — `feat: persiste o fechamento do registro diário do ponto de coleta`
- `95abde2` — `feat: adiciona caso de uso de fechamento do registro diário`
- `e35eb96` — `feat: adiciona endpoint de fechamento do registro diário`

### Decisões de projeto

#### Regras do fechamento diário

| Decisão | Regra adotada |
|---|---|
| Pré-condição | o dia só pode ser fechado com ao menos uma medição de cada tipo (cloro, pH e temperatura) |
| Após o fechamento | medições com a data de um dia fechado são recusadas com `ValueError` |
| Fechamento duplicado | fechar novamente um dia já fechado lança `ValueError` |
| Reabertura | não permitida nesta fase |

As regras ficam no `CollectionPoint`, pois dependem do conjunto de medições e
de fechamentos do agregado. A verificação em `add_measurement` ocorre antes da
inclusão da medição, para que o agregado não fique em estado inválido quando o
erro é lançado.

#### DailyClosure como objeto de valor

O fechamento é representado pela classe `DailyClosure`, que contém apenas o
dia. Foi utilizada uma classe em vez de uma lista de datas porque o SQLAlchemy
precisa mapear objetos para a tabela `daily_closures`. Assim como na
`Specification`, a chave da tabela é mapeada no atributo privado `_id`.

#### Restrição de unicidade no banco

A tabela `daily_closures` possui `UNIQUE (collection_point_id, day)`. O domínio
já impede o fechamento duplicado, e a restrição funciona como segunda proteção
caso algum código grave diretamente no banco.

#### Data no fechamento e data e hora na medição

O fechamento utiliza `date` e a medição utiliza `datetime`. A comparação é
feita com `measurement_date.date()`. Na API, o endpoint aceita apenas datas no
formato `AAAA-MM-DD`, pois uma hora não teria significado no fechamento.

#### Filtro de não conformidades por período

A `NonConformity` não possui data própria. A consulta por período utiliza a
data da medição que originou a não conformidade, pois ambas são criadas no
mesmo momento, durante o registro da medição.

#### Autoincremento no FakeRepository

O Fake atribui um identificador quando recebe um ponto com `id_=None`,
simulando o banco. Sem isso, pontos criados pelo service seriam guardados na
mesma chave e sobrescritos.

### Pendência do Checkpoint 1 revisitada

O Checkpoint 1 registrou que a regra de medições antes do início da produção
não havia sido implementada. O fechamento diário passa a garantir que o
monitoramento do dia esteja completo, com os três tipos de medição, e que o
registro não seja alterado depois de fechado. A integração com o horário de
início da produção do agregado Lote de Produção continua fora do escopo da
Fase 1.

### Dificuldades encontradas

- os testes antigos do domínio criavam medições com a data em texto
  (`"2024-06-01T12:00:00Z"`). O erro só apareceu quando o domínio passou a usar
  a data, e os testes foram corrigidos para usar `datetime`;
- diferença entre `date` e `datetime` nas comparações do fechamento;
- necessidade de implementar domínio e ORM no mesmo PR, pois objetos carregados
  do banco não possuem atributos que não estejam mapeados;
- distinção entre o método `commit()` e o atributo `committed` do `FakeSession`.

### Uso de Inteligência Artificial

Foi utilizada IA como apoio durante o Checkpoint 2 e a entrega, dentro dos
limites estabelecidos pela disciplina.

O uso ocorreu principalmente para:

- explicação de conceitos do padrão Repository, do mapeamento imperativo do
  SQLAlchemy, de fixtures do pytest e do papel do service layer;
- revisão do código escrito pelo integrante e explicação dos erros encontrados;
- diagnóstico da quebra da CI na `main` e elaboração do plano de correção;
- sugestão de trechos de código (mapeamento ORM, testes de integração, testes
  do service layer, endpoint e testes e2e), que foram analisados, aplicados,
  ajustados e validados pelo integrante com a execução dos testes;
- discussão das alternativas de projeto do fechamento diário. As regras
  adotadas foram escolhidas pelo integrante.