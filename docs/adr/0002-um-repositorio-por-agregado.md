# 0002 — Um repositório por agregado, com a Aggregate Root como fronteira de persistência

**Status:** aceito
**Data:** 2026-09-28
**Autor:** João Gabriel Pimentel
**Fase:** Fase 1 (Checkpoint 2 — Repositórios)

## Contexto

O agregado `CollectionPoint` contém quatro coleções filhas: `measurements`,
`specifications`, `non_conformities` e `daily_closures`. O agregado
`ProductionBatch` contém `weight_samples`, `lecithinization` e
`non_conformities`.

Duas regras do domínio dependem do **conjunto**, não de um item isolado:

- uma medição fora da especificação gera uma não conformidade, a verificação
  precisa das `specifications` do ponto de coleta;
- o registro diário só fecha com ao menos uma medição de cada um dos três tipos,
  a verificação precisa de todas as `measurements` daquele dia.

Se existisse um `MeasurementRepository` com um método `add`, qualquer código
poderia gravar uma medição diretamente, pulando `CollectionPoint.add_measurement`
e, com ela, a verificação de especificação e a geração da não conformidade.
A regra deixaria de ser uma garantia estrutural e passaria a depender da
disciplina de quem escreve o código.

## Decisão

Existe **um repositório por Aggregate Root**, e apenas por Aggregate Root
(`src/LactoQC/adapters/repository.py`):

- `AbstractCollectionPointRepository` → `add`, `get`, `list`
- `AbstractProductionBatchRepository` → `add`, `get`, `list`

As coleções filhas **não têm repositório**. Elas são carregadas e salvas junto
com a raiz, por `relationship` declarado em `orm.py:102-112`. A única forma de
incluir uma medição é:

```python
collection_point.add_measurement(measurement) 
```

que executa, nesta ordem: `_verify_day_is_open`, inclusão na coleção e
`check_for_non_conformity`.

O repositório é definido como uma **interface abstrata** (`ABC`) sobre a qual
existem três implementações: a real sobre SQLAlchemy, e os dublês em memória
usados nos testes (`FakeCollectionPointRepository` em `tests/conftest.py`,
`FakeProductionBatchRepository` em `repository.py:77`). É essa interface que
funciona como **porta de saída** da arquitetura hexagonal.

## Alternativas consideradas

### A. Um repositório por entidade

Um `MeasurementRepository`, um `NonConformityRepository`, e assim por diante.
Permitiria consultas diretas e eficientes — por exemplo, listar não
conformidades de um período com um `SELECT ... WHERE` em vez de carregar
agregados inteiros.

Rejeitada porque abre caminhos de escrita que contornam as invariantes. O ganho
de desempenho responde a um requisito que o LactoQC não tem (§2.1 do documento
de arquitetura: desempenho não é atributo priorizado); o custo é a integridade,
que é o atributo 3.

### B. Repositório único genérico (`Repository[T]`)

Uma classe parametrizada servindo a todos os agregados. Menos código, mas
apaga a diferença entre o que é Aggregate Root e o que não é — exatamente a
informação que esta decisão existe para preservar. Também dificulta métodos de
consulta específicos, como `get(batch_number)` em vez de `get(id)`.

## Consequências

- `+` **Integridade:** nenhum caminho de escrita contorna a Aggregate Root.
  `grep -n "class.*Repository" src/LactoQC/adapters/repository.py` mostra
  repositórios apenas para `CollectionPoint` e `ProductionBatch`.
- `+` **Testabilidade:** a interface abstrata permite substituir o banco por um
  dicionário em memória nos testes do service layer, sem mudar o código testado.
- `+` **Clareza do modelo:** o repositório documenta, por existir ou não, onde
  estão as fronteiras transacionais do domínio.
- `+` **Trabalho em paralelo:** cada integrante define o repositório do seu
  agregado sem tocar no dos outros.
- `−` **Desempenho (R-03):** `services.list_non_conformities` precisa chamar
  `repo.list()` e filtrar em Python (`services.py:102-115`), porque não há como
  consultar não conformidades sem passar pelos agregados. É O(n) sobre todo o
  histórico.
- `−` **Granularidade fixa:** carregar um `CollectionPoint` traz todas as suas
  medições, mesmo quando só se quer o nome e a localização.
- `−` **Manutenção dos dublês:** cada repositório abstrato exige um `Fake`
  correspondente, que precisa acompanhar mudanças no contrato — inclusive
  detalhes do banco, como o autoincremento simulado em `tests/conftest.py:16`.

## Referências

- `docs/arquitetura.md` §3.4, §4.2 (PT-03), §4.4 (R-03), §6.6
- `DECISIONS.md` — Checkpoint 2, "Um repositório por agregado"
- Commits `cb4a3ce`, `8de6a6b`
- Evans, E. *Domain-Driven Design*, cap. 6 (Aggregates, Repositories)
