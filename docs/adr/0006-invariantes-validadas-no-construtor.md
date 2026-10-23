# 0006 — Invariantes do agregado validadas no construtor

**Status:** aceito
**Data:** 2026-09-28
**Autor:** Lucas Ardelino Alves da Silva
**Fase:** Fase 1 (Checkpoint 1 — Modelo de domínio)

## Contexto

Várias regras do LactoQC não são sobre uma operação, e sim sobre **o que é válido
existir**:

- uma medição de cloro tem de estar em mg/L; uma de pH não tem unidade;
- uma especificação com mínimo maior que o máximo não descreve faixa nenhuma;
- um ponto de coleta sem especificação de cloro não consegue avaliar cloro;
- uma amostra de peso igual ou menor que zero não é uma medição;
- um lote de produção com matéria-prima reprovada não deveria existir —
  é a primeira regra listada em `PROPOSTA.md` §4.3.

Se essas verificações ficarem em métodos separados, chamados *depois* da
construção, existe uma janela em que o objeto está no ar em estado inválido. E,
com quatro pessoas escrevendo código em paralelo, alguém vai esquecer de chamar
o método de validação — especialmente no agregado de outra pessoa.

Havia também a alternativa de centralizar essas verificações no service layer,
já que toda criação passa por lá. Mas isso espalharia a regra do agregado para
fora dele, e cada novo adaptador primário (script, CLI, carga de dados) teria
que lembrar de repeti-la.

## Decisão

As invariantes são verificadas **no `__init__`**, no final da atribuição dos
atributos. Um objeto que existe está, por construção, em estado válido.

```python
class Measurement:
    def __init__(self, id_, measurement_date, value, measurement_unit, measurement_type):
        ...
        self._verify_unit()                      # model.py:32

class Specification:
    def __init__(self, ...):
        ...
        self._verify_min_max_values()            # model.py:50
        self._verify_unit()

class CollectionPoint:
    def __init__(self, ...):
        ...
        self._validate_specifications()          # model.py:93  — exige os 3 tipos, sem duplicata

class ProductionBatch:
    def __init__(self, ...):
        ...
        self._verify_raw_material_approved()     # model.py:236
        self._verify_expected_weight()
```

As verificações são métodos privados nomeados `_verify_*` / `_validate_*`, e a
falha é sinalizada com `ValueError` — traduzido em HTTP 422 pelo ADR-0004.

A regra que liga os agregados **Recebimento** e **Lote de Produção** —
*"um lote só pode usar matéria-prima aprovada"* — é implementada desta forma.
O `ProductionBatch` não consulta o repositório de recebimentos: ele recebe um
`RawMaterialReceipt` já carregado e pergunta apenas `approved`
(`model.py:178-180`), que é tudo de que precisa saber sobre o outro agregado.

## Alternativas consideradas

### A. Métodos de validação públicos, chamados pelo service layer

`collection_point.validate()` invocado depois de construir.

Rejeitada: cria uma janela de invalidez e depende de o chamador lembrar. Com
três agregados de três donos diferentes, é questão de tempo até alguém esquecer.

### B. *Factory methods* (`CollectionPoint.create(...)`)

Construtor sem validação, mais um método de classe que valida e constrói.

Tem uma vantagem real sobre a opção escolhida: o SQLAlchemy não chamaria o
método de fábrica ao carregar, e a diferença entre "criar novo" e "reconstituir
do banco" ficaria explícita no código em vez de implícita.

Rejeitada pelo custo: exigiria dois caminhos de construção em todas as classes e
a revisão de todos os testes já escritos. É a melhoria natural caso o risco R-02
se torne um problema concreto.

### C. Validação por esquema na entrada da API

Validar o corpo JSON nas rotas, com um validador de esquema.

Rejeitada como **substituta** — a regra sairia do domínio e cada novo adaptador
teria que repeti-la. Mantida como **complemento**: o entrypoint valida a
sintaxe com `abort(400)` e o domínio valida a semântica (ADR-0004).

## Consequências

- `+` **Integridade:** não existe instância inválida em memória. A regra "lote só
  com matéria-prima aprovada" é impossível de contornar pela aplicação.
- `+` **Acoplamento mínimo entre agregados:** `ProductionBatch` depende de uma
  única propriedade booleana de `RawMaterialReceipt`, não do agregado inteiro.
  Lucas pode evoluir o Recebimento sem quebrar o Lote de Produção.
- `+` **Testabilidade:** a invariante é testada construindo o objeto e esperando
  `ValueError` — sem banco, sem *setup*. É o que sustenta os 113 testes unitários
  em 0,14 s.
- `+` **Localidade:** a regra fica ao lado dos dados que ela protege.
- `−` **Risco (R-02):** o SQLAlchemy **não executa `__init__`** ao carregar do
  banco (ADR-0001). Nenhuma dessas verificações roda na leitura. Um registro
  inconsistente inserido por fora da aplicação é carregado sem protesto.
  Mitigação: declarar as restrições também no esquema — hoje só existe
  `UNIQUE (collection_point_id, day)` em `daily_closures`.
- `−` **Construção rígida:** não é possível montar um `CollectionPoint`
  incrementalmente, adicionando especificações uma a uma. As três precisam estar
  prontas antes.
- `−` **Mensagens genéricas:** todas as falhas chegam como `ValueError`, e a API
  não distingue qual invariante foi violada além do texto (ADR-0004).

## Referências

- `docs/arquitetura.md` §2.4, §3.6 (tática "validar na entrada"), §4.4 (R-02)
- `src/LactoQC/domain/model.py:32, 50-51, 93, 189, 236-237`
- `PROPOSTA.md` §4.1 e §4.3
- Evans, E. *Domain-Driven Design*, cap. 5 (invariantes de entidade)
