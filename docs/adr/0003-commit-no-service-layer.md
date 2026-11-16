# 0003 — O commit da transação pertence ao service layer, não ao repositório

**Status:** aceito
**Data:** 2026-09-29
**Autor:** André Meschesi Dantas
**Fase:** Fase 1 (Entrega — Service layer e API)

## Contexto

Com os repositórios prontos (ADR-0002), foi preciso decidir **quem confirma a
transação**. Três candidatos: o repositório, o service layer ou o entrypoint.

A pergunta por trás é qual é a fronteira transacional do sistema. Um caso de uso
do LactoQC não é uma operação única: `register_measurement` busca o agregado,
cria a medição, chama `add_measurement` — que pode criar uma `NonConformity` —
e só então o resultado precisa ser durável. Se o repositório confirmasse a cada
`add`, a medição poderia ser gravada e a não conformidade não, caso algo
falhasse no meio.

Há também um requisito de testabilidade: os testes do service layer precisam
verificar não só *o que* aconteceu, mas se a transação foi ou não confirmada —
por exemplo, que um fechamento de dia incompleto **não** faz commit.

## Decisão

O repositório **apenas adiciona e recupera** objetos da sessão
(`repository.py:29-40`). Nenhuma de suas implementações chama `commit()`.

O **caso de uso** no service layer recebe a `Session` como parâmetro e é o único
responsável por confirmar:

```python
def register_measurement(repo, session, collection_point_id, ...):
    collection_point = get_collection_point(repo, collection_point_id)
    ...
    collection_point.add_measurement(measurement)   # pode criar NonConformity
    session.commit()                                # services.py:98
    return measurement, new_non_conformities
```

A **fronteira transacional é o caso de uso**: tudo o que ele tocou sobe ou desce
junto.

O entrypoint não confirma nada. Ele cria a sessão da requisição
(`flask_app.py:15-19`) e a fecha no `teardown_appcontext`
(`flask_app.py:35-39`), mas quem decide o commit é o serviço.

Nos testes, um `FakeSession` que apenas registra `committed = True`
(`tests/conftest.py:28`) permite verificar a decisão transacional sem banco.

## Alternativas consideradas

### A. Commit dentro do repositório, em cada `add`

Mais simples de chamar: o caso de uso não precisaria receber a `Session`.

Rejeitada porque fragmenta a transação. Cada escrita viraria sua própria unidade
atômica, e um caso de uso que falhasse no meio deixaria o banco em estado
parcial — por exemplo, a medição gravada sem a não conformidade que ela deveria
ter gerado. Isso ataca diretamente a integridade das regras (atributo 3).

### B. Commit no entrypoint, após cada rota

Daria uma fronteira transacional por requisição HTTP, que coincidiria com o caso
de uso na maioria das vezes.

Rejeitada porque acopla a transação ao protocolo. Um caso de uso chamado por um
script de carga, por um comando de CLI ou por um teste não teria transação
nenhuma — e a arquitetura hexagonal existe justamente para que a camada de
aplicação funcione igual por qualquer adaptador primário.

### C. Unit of Work explícito

Um objeto `UnitOfWork` que encapsula a sessão e expõe os repositórios, usado como
gerenciador de contexto (`with uow: ... uow.commit()`).

É a solução **correta** e está planejada para a Fase 2 (ajuste 1 da §5.2 do
documento de arquitetura). Não foi adotada na Fase 1 por custo de tempo: exigiria
reescrever a assinatura de todos os casos de uso e todos os testes já escritos,
no meio da entrega.

## Consequências

- `+` **Integridade:** a transação cobre o caso de uso inteiro. Uma medição e a
  não conformidade que ela gera são sempre gravadas juntas.
- `+` **Testabilidade:** os testes verificam a decisão transacional sem banco.
  Há testes que afirmam explicitamente a **ausência** de commit — fechamento de
  dia incompleto, ponto de coleta inexistente, medição em dia já fechado.
- `+` **Reuso:** o mesmo caso de uso serve à API HTTP, a um script ou a um teste,
  sempre com a mesma semântica transacional.
- `−` **Vazamento de infraestrutura:** `services.py:7` importa
  `sqlalchemy.orm.Session`. É o **único** acoplamento com o ORM acima da camada
  de adaptadores, e o que impede dizer que o hexágono está fechado
  (`docs/arquitetura.md` §6.1).
- `−` **Assinatura ruidosa:** todo caso de uso que escreve recebe dois parâmetros
  de infraestrutura, `repo` e `session`, antes dos parâmetros de negócio.
- `−` **Disciplina manual:** nada impede um caso de uso novo de esquecer o
  `commit()`. Um `UnitOfWork` tornaria o esquecimento impossível.

## Referências

- `docs/arquitetura.md` §3.6, §4.3 (PS-02), §5.2 (ajuste 1), §6.1
- `DECISIONS.md` — Checkpoint 2, "Repositório sem commit"
- Commits `6c41caa`, `95abde2`
- Percival & Gregory, *Architecture Patterns with Python*, cap. 4 e 6

## Revisão — Fase 2 (16/11/2026)

**Autor da revisão:** André Meschesi Dantas

A decisão deste ADR **continua valendo**: o commit segue no service layer.
Duas mudanças da Fase 2 tocam o contexto descrito acima:

- **Origem dos repositórios.** Com o padrão Abstract Factory (`docs/gof.md`,
  commit `8f368e4`), as rotas não instanciam mais `SqlAlchemy*Repository`:
  pedem o repositório a `get_repositories()`, que devolve a fábrica configurada
  em `create_app`. A sessão continua sendo criada por requisição
  (`get_session()`) e passada ao caso de uso, que faz o `commit()`. A fábrica
  em memória (`InMemoryRepositoryFactory`) é usada com um `FakeSession`, de
  forma que a mesma semântica transacional vale sem banco.
- **Montagem da persistência.** A criação do engine e das tabelas saiu de
  `flask_app.py` para `adapters/database.py` (refatoração SRP, `docs/solid.md`,
  commit `00f5522`). As referências de linha da seção "Decisão" (`flask_app.py:15-19`,
  `flask_app.py:35-39`, `tests/conftest.py:28`) se referem ao estado da Fase 1;
  hoje o equivalente é `get_session()` e o `teardown_appcontext` de
  `create_app`, e a classe `FakeSession` de `tests/conftest.py`.

A alternativa C (Unit of Work) fica **mais barata** depois dessas mudanças: um
`UnitOfWork` poderia receber uma `AbstractRepositoryFactory` e a sessão, e
expor os repositórios e o `commit()` em um único objeto.
