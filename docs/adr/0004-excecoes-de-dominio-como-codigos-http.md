# 0004 — Traduzir exceções de domínio em códigos HTTP no entrypoint

**Status:** aceito
**Data:** 2026-09-29
**Autor:** André Meschesi Dantas
**Fase:** Fase 1 (Entrega — Service layer e API)

## Contexto

O domínio sinaliza violação de regra lançando `ValueError`: unidade incompatível
com o tipo de medição (`model.py:37`), mínimo maior que o máximo
(`model.py:55`), especificação faltando ou duplicada (`model.py:99-101`), dia já
fechado (`model.py:108`), fechamento sem os três tipos de medição
(`model.py:116`), matéria-prima não aprovada (`model.py:241`). O service layer
sinaliza agregado inexistente com `LookupError` (`services.py:68`).

A API precisa responder com o código HTTP certo. Sem uma decisão explícita,
cada rota repetiria o mesmo bloco:

```python
try:
    ...
except ValueError as e:
    return jsonify(erro=str(e)), 422
except LookupError as e:
    return jsonify(erro=str(e)), 404
```

Isso seria repetido em cinco rotas hoje, e em mais quinze quando os agregados de
Recebimento e Lote de Produção ganharem seus endpoints — com três autores
diferentes, e portanto três formatos de resposta ligeiramente diferentes.

A alternativa oposta — o domínio devolver códigos HTTP — violaria o isolamento
do núcleo (ADR-0001): uma regra de laticínio não deve saber o que é um 422.

## Decisão

O domínio permanece ignorante do protocolo: ele lança exceções **do vocabulário
do Python**, não da web.

A tradução acontece **uma única vez**, em manipuladores de erro registrados na
fábrica da aplicação (`flask_app.py:46-62`):

| Exceção | Código | Significado |
|---|---|---|
| `LookupError` | **404** | O recurso não existe |
| `ValueError` | **422** | A requisição é bem formada, mas viola uma regra de negócio |
| `abort(400)` | **400** | O corpo da requisição está malformado ou faltam campos |

```python
@app.errorhandler(ValueError)
def domain_error(e):
    return jsonify(erro="regra de negócio violada", detalhe=str(e)), 422
```

A validação **sintática** (JSON é um objeto, campos obrigatórios presentes,
tipos corretos) fica no entrypoint e usa `abort(400)`
(`collection_point_routes.py:23-33`). A validação **semântica** fica no domínio
e chega como `ValueError`.

A distinção 400 × 422 é deliberada: 400 significa "não consigo nem ler o seu
pedido"; 422 significa "entendi perfeitamente, e a fábrica não permite".

## Alternativas consideradas

### A. `try/except` em cada rota

Explícito e local, mas duplicado em toda rota e em todo agregado. Com quatro
autores, o formato das respostas divergiria. Rejeitada pelo custo de manutenção.

### B. Exceções próprias do domínio (`RegraVioladaError`, `NaoEncontradoError`)

Mais expressivo e evitaria o risco de capturar `ValueError` acidental
(PS-03 abaixo). É uma melhoria real e candidata à Fase 2.

Não foi adotada na Fase 1 porque exigiria revisar todos os `raise` já escritos
pelos três donos de agregado e todos os testes que fazem
`pytest.raises(ValueError)` — no meio da entrega, com a CI já verde.

### C. O domínio retorna códigos HTTP ou objetos de resultado com status

Rejeitada de imediato: acopla o núcleo ao protocolo de entrega e contradiz a
decisão central da arquitetura (ADR-0001).

## Consequências

- `+` **Modificabilidade:** o mapeamento está em um lugar só. Acrescentar um
  agregado não exige escrever tratamento de erro.
- `+` **Consistência:** toda a API responde no mesmo formato
  (`{"erro": ..., "detalhe": ...}`), venha o erro de qual agregado vier.
- `+` **Isolamento:** `grep -rn "flask" src/LactoQC/domain/` retorna zero. O
  domínio não sabe que existe HTTP.
- `+` **Testabilidade:** os 43 testes e2e verificam os códigos de retorno
  (201, 400, 404, 422) sem que as rotas contenham lógica de erro.
- `−` **Risco (PS-03):** o manipulador captura **qualquer** `ValueError`,
  inclusive os acidentais. Um `int("abc")` esquecido em uma rota viraria um
  "regra de negócio violada 422" em vez de um erro de servidor — mascarando um
  bug como comportamento normal.
- `−` **Cobertura incompleta:** só as exceções previstas são traduzidas. Em
  `collection_point_routes.py:16`, `_parse_date` captura `TabError` onde
  deveria capturar `TypeError`; com `{"date": null}` a requisição retorna
  **500** em vez de 400 (R-04 do documento de arquitetura).
- `−` **Perda de informação:** 422 não distingue qual regra foi violada; o
  cliente precisa interpretar o texto em `detalhe`.

## Referências

- `docs/arquitetura.md` §4.3 (PS-03), §4.4 (R-04)
- `src/LactoQC/entrypoints/flask_app.py:46-62`
- `tests/e2e/test_collection_points_api.py`
- Commits `6c41caa`, `74132aa`, `e35eb96`
