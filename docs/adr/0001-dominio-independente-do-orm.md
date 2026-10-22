# 0001 — Manter o domínio independente do ORM, com mapeamento imperativo

**Status:** aceito
**Data:** 2026-09-28
**Autor:** João Gabriel Pimentel
**Fase:** Fase 1 (Checkpoint 2 — Repositórios)

## Contexto

A disciplina exige TDD e uma suíte dividida em `tests/unit`, `tests/integration` e
`tests/e2e`. As regras de negócio do LactoQC — faixa de cloro, pH, temperatura,
obrigatoriedade das três especificações, fechamento do registro diário, são o
núcleo do sistema e precisam ser escritas antes do código de produção.

Se as classes de domínio herdarem de `Base` do SQLAlchemy (mapeamento
declarativo), instanciá-las passa a depender de um registro de metadados e, na
prática, de um banco. O ciclo escrever-rodar-corrigir do TDD fica lento, e o
cenário de qualidade CQ-01 ("o domínio deve ser exercitado sem banco, sem
servidor e sem rede") deixa de ser verificável.

Há ainda uma restrição de equipe: quatro integrantes evoluem três agregados em
paralelo. O arquivo de mapeamento é compartilhado e será uma fonte de conflitos
de merge de qualquer forma; o domínio não precisa ser a segunda.

## Decisão

As classes de `src/LactoQC/domain/model.py` são **Python puro**: não herdam de
nenhuma classe do SQLAlchemy e não importam o pacote.

O mapeamento objeto-relacional é **imperativo**, concentrado em
`src/LactoQC/adapters/orm.py`, e só é ativado pela chamada explícita de
`start_mappers()` (`orm.py:76`):

```python
mapper_registry.map_imperatively(
    CollectionPoint,
    collection_points_table,
    properties={
        "id_": collection_points_table.c.id,
        "specifications": relationship(Specification, order_by=specifications_table.c.id),
        ...
    },
)
```

Objetos de valor sem identidade no domínio (`Specification`, `DailyClosure`)
recebem uma **chave substituta** mapeada no atributo privado `_id`, para não se
confundir com o `id_` das entidades.

A dependência é invertida: `adapters/` conhece `domain/`, nunca o contrário.

## Alternativas consideradas

### A. Mapeamento declarativo (herdar de `Base`)

Menos código: as tabelas seriam declaradas junto das classes e `orm.py`
praticamente desapareceria (hoje são 191 linhas).

Rejeitada porque acopla o domínio ao ORM. A regra de negócio passaria a depender
de uma biblioteca de infraestrutura, e o atributo de qualidade prioritário do
projeto (testabilidade) seria o primeiro a pagar.

### B. Domínio puro com tradução manual para DTOs de persistência

Um conjunto paralelo de classes de persistência e funções de ida e volta.
Dá o mesmo isolamento, mas custa **duas** representações para manter em vez de
uma mais o mapeamento, e perde o *identity map* e o *dirty checking* do
SQLAlchemy, que é justamente o que faz `session.commit()` salvar as alterações
feitas pelos métodos do agregado sem código extra.

## Consequências

- `+` **Testabilidade:** 113 testes unitários rodam em **0,14 s**, sem banco.
- `+` **Verificabilidade:** `grep -rn "sqlalchemy\|flask" src/LactoQC/domain/`
  retorna **zero** ocorrências. A propriedade pode ser checada automaticamente.
- `+` **Modificabilidade:** trocar SQLite por PostgreSQL, ou o SQLAlchemy por
  outra biblioteca, não toca nenhum arquivo de `domain/`.
- `−` **Simplicidade:** `orm.py` tem **191 linhas** para mapear **302 linhas** de
  domínio, 63% de duplicação estrutural que precisa ser mantida em sincronia.
- `−` **Simplicidade:** objetos de valor precisam de uma chave substituta
  artificial (`_id`) que não existe no modelo de negócio.
- `−` **Risco (R-02):** o SQLAlchemy **não chama `__init__`** ao carregar do banco.
  As invariantes verificadas no construtor (ADR-0006) não são reaplicadas na
  leitura, o que torna o esquema do banco a última linha de defesa.
- `−` **Risco (R-01):** `start_mappers()` é estado global do processo; mapear a
  mesma classe duas vezes derruba a inicialização inteira, não só o agregado que
  errou. O risco **já se materializou uma vez** em `orm.py:167`, onde
  `WeightSample` havia sido trocada por `RawMaterialReceipt`, quebrando 18 testes
  de integração do Lote de Produção. Corrigido no commit `7ab94f5`.

## Referências

- `docs/arquitetura.md` §3.1, §4.2 (PT-01), §4.4 (R-01, R-02), §6.1, §6.4
- `DECISIONS.md` — Checkpoint 2, "Mapeamento imperativo"
- Commits `cb4a3ce`, `8de6a6b`, `c63a193`
- Percival & Gregory, *Architecture Patterns with Python*, cap. 2
