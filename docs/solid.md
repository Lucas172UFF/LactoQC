# Checkpoint 2 — Refatoração SOLID

**Disciplina:** Projeto de Software — UFF 2026.2
**Checkpoint:** 2 · Refatoração SOLID (03/11)
**Equipe:** Lucas Ardelino Alves da Silva, João Gabriel Pimentel, Aloysio Felipe Saad Silva, André Meschesi Dantas

Cada integrante corrige pelo menos uma violação de um princípio SOLID no código do
agregado/módulo sob sua responsabilidade. Como grupo, cobrimos pelo menos três
princípios diferentes. O código "antes" está em um commit anterior a 06/10, ou a
violação é exposta por uma mudança de requisito plausível descrita na seção do autor.

| Integrante | Agregado/módulo | Princípio | Status |
|---|---|---|---|
| João Gabriel Pimentel | `CollectionPoint` (domínio) | OCP | ✅ Concluído |
| Aloysio Felipe Saad Silva | _(preencher)_ | _(preencher)_ | ⬜ Pendente |
| Lucas Ardelino Alves da Silva | _(preencher)_ | _(preencher)_ | ⬜ Pendente |
| André Meschesi Dantas | _(preencher)_ | _(preencher)_ | ⬜ Pendente |

---

## João Gabriel Pimentel — `CollectionPoint` (agregado Ponto de Coleta)

### Princípio violado: Open/Closed Principle (OCP)

**Commit "antes":** [`56bdff3`](../../commit/56bdff3f670b0928229b62000be1066e04010712) (29/09/2026, anterior a 06/10) — código inalterado até `723e339`, o commit referência da seção 6 de `docs/arquitetura.md`.

Trecho de `src/LactoQC/domain/model.py` no commit `56bdff3`:

```python
def _validate_specifications(self):
    for measurement_type in MeasurementType:
        count = sum(1 for spec in self.specifications if spec.measurement_type == measurement_type)
        if count == 0:
            raise ValueError(f"Specification for measurement type {measurement_type.value} is missing.")
        if count > 1:
            raise ValueError(f"Specification for measurement type {measurement_type.value} is duplicated.")

def _verify_all_measurement_types_on(self, day: date):
    measured_types = {
        measurement.measurement_type for measurement in self.measurements if measurement.measurement_date.date() == day
    }
    for measurement_type in MeasurementType:
        if measurement_type not in measured_types:
            raise ValueError(
                f"Cannot close day {day}: missing {measurement_type.value} measurement."
            )
```

### O problema concreto

As duas regras de negócio mais importantes do agregado — "toda `CollectionPoint`
precisa de uma especificação por tipo de medição" e "o dia só fecha se todos os
tipos foram medidos" — tratavam **"é obrigatório" como sinônimo de "existe no
`Enum MeasurementType`"**. O `Enum` definia ao mesmo tempo *quais tipos de
medição existem* e *quais são obrigatórios*, dois conceitos que não são a
mesma coisa.

Isso é uma violação de OCP exposta por uma mudança de requisito plausível,
não forçada: a `PROPOSTA.md` já prevê evolução do catálogo de medições (ex.:
adicionar **Turbidez** como um tipo monitorado, mas opcional — nem toda
`CollectionPoint` tem o sensor, e o dia pode fechar sem ela). Ao adicionar
`TURBIDITY` em `MeasurementType`, as duas regras acima passariam a:

1. Exigir uma `Specification` de turbidez em **toda** `CollectionPoint` já
   cadastrada, quebrando pontos existentes que não têm esse instrumento.
2. Bloquear o fechamento do dia em **todo** ponto que não medisse turbidez,
   mesmo sendo opcional.

Para o novo tipo se comportar como "opcional", seria preciso **modificar**
`_validate_specifications` e `_verify_all_measurement_types_on` — os dois
métodos que materializam a invariante do agregado — toda vez que o catálogo
de medições mudasse. O agregado não estava fechado para modificação diante
de uma mudança de requisito esperada.

### A refatoração

**Commit "depois":** [`6ad1830`](../../commit/6ad1830) — `refactor: extrai política de tipos obrigatórios do CollectionPoint (OCP)`.

Extraí a política de obrigatoriedade para um dado explícito, ao lado de
`EXPECTED_UNITS`:

```python
MANDATORY_MEASUREMENT_TYPES = frozenset(
    {MeasurementType.CHLORINE, MeasurementType.PH, MeasurementType.TEMPERATURE}
)
```

E troquei a iteração sobre o `Enum` inteiro pela iteração sobre essa política
nos dois métodos:

```python
def _validate_specifications(self):
    for measurement_type in MANDATORY_MEASUREMENT_TYPES:
        ...

def _verify_all_measurement_types_on(self, day: date):
    ...
    for measurement_type in MANDATORY_MEASUREMENT_TYPES:
        ...
```

Com isso, um tipo de medição novo e opcional entra em `MeasurementType` e em
`EXPECTED_UNITS` (dado), e **não** em `MANDATORY_MEASUREMENT_TYPES` — sem
tocar em `CollectionPoint`. A classe fica aberta para extensão (novo tipo,
novo "é obrigatório ou não") e fechada para modificação (nenhum método do
agregado muda).

### Como os testes garantiram que o comportamento não mudou

- A suíte completa antes da mudança: `173 passed` (`pytest -q`, commit `0212d2e`, estado de `main` no Checkpoint 1).
- Depois da mudança: `174 passed` — os mesmos 173 testes continuam verdes
  (nenhuma asserção mudou), mais um teste novo.
- O teste novo, `test_collection_point_only_requires_mandatory_measurement_types`
  (`tests/unit/test_collection_point.py`), usa `monkeypatch` para reduzir
  `MANDATORY_MEASUREMENT_TYPES` a `{CHLORINE}` e comprova que o
  `CollectionPoint` aceita faltar especificação/medição dos demais tipos —
  ou seja, prova que a obrigatoriedade hoje vem da política, não do `Enum`
  inteiro. Sem essa mudança, esse teste não passaria com o código "antes"
  (`MeasurementType` não é substituível por `monkeypatch` da mesma forma, e a
  obrigatoriedade de todos os três tipos estaria hard-coded).
- `MANDATORY_MEASUREMENT_TYPES` definido com exatamente os três tipos atuais
  mantém o comportamento observável idêntico para todo o resto da suíte
  (`test_close_day_with_all_measurement_types`,
  `test_close_day_missing_measurement_typ_raises`,
  `test_reject_collection_point_missing_specifications`, etc.).

### O custo e por que compensa

**Custo:** uma constante a mais (`MANDATORY_MEASUREMENT_TYPES`) e um nível de
indireção nos dois métodos — em vez de "todo tipo do Enum", agora é "todo tipo
desta política". Zero classes novas, zero camadas novas.

**Por que compensa:** o custo é uma linha de dado; o que ele evita é editar
`CollectionPoint` — a Aggregate Root central do agregado, coberta por 25+
testes unitários — toda vez que o catálogo de medições muda. Pela mesma
lógica de CQ-04 em `docs/arquitetura.md` (custo de adicionar um caso de uso),
o ganho de modificabilidade aqui é concentrar a mudança em uma linha de dado
em vez de dois métodos de regra de negócio. Dado que a equipe já tem um
precedente real de evolução do catálogo de medições, essa é uma mudança com
probabilidade concreta de acontecer na Fase 2.

---

## Aloysio Felipe Saad Silva — _(preencher)_

- Princípio violado:
- Commit "antes":
- Trecho de código:
- Problema concreto:
- Commit "depois":
- Como os testes garantiram que o comportamento não mudou:
- Custo e por que compensa:

---

## Lucas Ardelino Alves da Silva — _(preencher)_

- Princípio violado:
- Commit "antes":
- Trecho de código:
- Problema concreto:
- Commit "depois":
- Como os testes garantiram que o comportamento não mudou:
- Custo e por que compensa:

---

## André Meschesi Dantas — _(preencher)_

- Princípio violado:
- Commit "antes":
- Trecho de código:
- Problema concreto:
- Commit "depois":
- Como os testes garantiram que o comportamento não mudou:
- Custo e por que compensa:
