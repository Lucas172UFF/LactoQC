# 0005 — Não conformidade é registrada pelo agregado, não lançada como exceção

**Status:** aceito
**Data:** 2026-09-25
**Autor:** Aloysio Felipe Saad Silva
**Fase:** Fase 1 (Entrega — Lote de Produção)

## Contexto

O LactoQC tem dois tipos de "coisa errada", e eles exigem reações opostas.

**O primeiro tipo impede a operação.** Um lote não pode ser aberto com matéria-
prima reprovada; uma medição não pode ser registrada em um dia já fechado; uma
amostra não pode ter peso negativo. Nesses casos, aceitar o dado deixaria o
agregado em estado inválido.

**O segundo tipo é o resultado do controle de qualidade.** Uma medição de cloro
em 7,0 mg/L está fora da faixa — mas ela **aconteceu** e precisa ficar
registrada. Uma amostra de peso 8% acima do esperado é um desvio real da
produção. Um lote de leite de cabra sem lecitinização precisa ser reprovado,
não esquecido.

Se o segundo tipo também lançasse exceção, o sistema perderia exatamente a
informação que justifica sua existência: o histórico de não conformidades que
`PROPOSTA.md` §6 pede para consultar por período e por origem. Pior: a medição
fora de faixa nem seria gravada, e a fábrica ficaria sem o registro do problema.

## Decisão

Os dois tipos são tratados de formas diferentes, e essa diferença é explícita no
código.

**Violação de pré-condição → exceção.** Verificada antes de alterar o estado,
para que o agregado nunca fique inválido:

```python
def add_measurement(self, measurement):
    self._verify_day_is_open(measurement.measurement_date.date())  # lança ValueError
    self.measurements.append(measurement)
    self.check_for_non_conformity(measurement)
```

**Resultado de controle de qualidade → registro no agregado.** O dado é aceito e
a não conformidade vira parte do estado:

```python
def _register_non_conformity(self, description: str):          # model.py:250
    self.non_conformities.append(
        BatchNonConformity(id_=len(self.non_conformities) + 1,
                           batch_id=self.id_, description=description)
    )
```

Em `ProductionBatch`, a decisão de liberar é a **consequência** desse registro,
não uma verificação paralela (`model.py:294-303`):

```python
def release(self, other_batches_of_the_day=None):
    self.check_mandatory_lecithinization()        # pode registrar
    self.check_milk_type_conflict(...)            # pode registrar
    if self.wettability_result != TestResult.APPROVED:
        self._register_non_conformity("Wettability test not approved.")

    self.status = BatchStatus.NON_CONFORMING if self.non_conformities else BatchStatus.RELEASED
```

`release()` **nunca lança exceção**. Ele sempre devolve um lote com um status e,
quando reprovado, com a lista completa dos motivos. O mesmo padrão vale para
`CollectionPoint.check_for_non_conformity` (`model.py:120`).

## Alternativas consideradas

### A. Lançar exceção também para a não conformidade

Rejeitada. A medição fora de faixa não seria persistida, e o histórico de não
conformidades — um caso de uso explícito da proposta — ficaria vazio
justamente nos casos que importam.

### B. Interromper na primeira não conformidade encontrada

`release()` lançaria exceção assim que achasse o primeiro problema.

Rejeitada porque o supervisor precisa saber **todos** os motivos de uma vez. Com
interrupção precoce, reprovar um lote de leite de cabra sem lecitinização
esconderia que ele também falhou no teste de molhabilidade — e a correção viraria
um ciclo de tentativa e erro.

### C. Eventos de domínio

`release()` publicaria `LoteReprovado` e um consumidor registraria a não
conformidade.

Rejeitada para a Fase 1. A não conformidade **é parte do estado do lote**, não um
efeito colateral: ela é persistida na mesma transação e aparece na consulta do
lote. Eventos fariam sentido para notificar outros contextos (avisar a produção,
enviar e-mail), e ficam como caminho para a Fase 2.

## Consequências

- `+` **Adequação funcional:** o histórico de não conformidades é completo. A
  consulta por período e origem da `PROPOSTA.md` §6 é possível porque os dados
  existem.
- `+` **Usabilidade da API:** uma única chamada de `release()` devolve todos os
  motivos da reprovação, não o primeiro.
- `+` **Integridade:** a separação deixa claro no código o que invalida o
  agregado (exceção) e o que é informação de qualidade (registro).
- `+` **Testabilidade:** verificar uma não conformidade é inspecionar uma lista,
  sem `pytest.raises` nem captura de exceção.
- `−` **Chamador precisa verificar:** nada no tipo de retorno obriga quem chama
  `add_measurement` a olhar `non_conformities`. O service layer compensa isso
  comparando o tamanho da lista antes e depois (`services.py:95-97`) — uma
  solução funcional, mas frágil.
- `−` **Identificador fraco:** `id_` é gerado como `len(non_conformities) + 1` e
  se repete entre agregados diferentes. Foi preciso gravá-lo na coluna `number`
  e dar à tabela uma chave primária própria (`orm.py:59-61`).
- `−` **Status silencioso:** `release()` nunca falha. Um chamador que não
  inspecionar `status` pode tratar um lote `NON_CONFORMING` como liberado.

## Referências

- `docs/arquitetura.md` §3.6 (tática "detectar e registrar"), §2.4
- `src/LactoQC/domain/model.py:120-133` (`CollectionPoint`), `:250-303` (`ProductionBatch`)
- `tests/unit/test_production_batch.py` (329 linhas), `tests/unit/test_collection_point.py` (454 linhas)
- `PROPOSTA.md` §4.3 e §6 (casos de uso 6, 12 e 14)
