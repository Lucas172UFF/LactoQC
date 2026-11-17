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
| Lucas Ardelino Alves da Silva | `RawMaterialReceipt` (domínio) | OCP | ✅ Concluído |
| André Meschesi Dantas | Infraestrutura e API (`flask_app.py`) | SRP | ✅ Concluído |

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

### Aloysio Felipe Saad Silva — ProductionBatch (agregado Lote de Produção)
### Princípio violado: Open/Closed Principle (OCP)

Commit "antes": <HASH-ANTES> — código do ProductionBatch em src/LactoQC/domain/model.py antes da refatoração desta seção.

Trecho de src/LactoQC/domain/model.py no commit <HASH-ANTES>:

python
def check_mandatory_lecithinization(self):
    if self.milk_type == MilkType.GOAT and (self.lecithinization is None or not self.lecithinization.performed):
        self._register_non_conformity("Goat milk requires lecithinization, but it was not performed.")

def check_milk_type_conflict(self, other_batches_of_the_day: List["ProductionBatch"]):
    for other_batch in other_batches_of_the_day:
        same_date = other_batch.production_date.date() == self.production_date.date()
        if other_batch.id_ != self.id_ and same_date and other_batch.milk_type != self.milk_type:
            self._register_non_conformity(...)

def release(self, other_batches_of_the_day=None):
    ...
    if self.wettability_result != TestResult.APPROVED:
        self._register_non_conformity("Wettability test not approved.")
    self.status = BatchStatus.NON_CONFORMING if self.non_conformities else BatchStatus.RELEASED
O problema concreto

Cada regra de qualidade do lote — tolerância de peso, lecitinização obrigatória para leite de cabra, conflito de tipo de leite no mesmo dia, aprovação da molhabilidade — estava implementada como lógica fixa dentro dos próprios métodos de ProductionBatch. A classe que representa o agregado era também a única classe capaz de decidir se cada regra passava ou não.

Isso é uma violação de OCP exposta por uma mudança de requisito plausível, prevista na própria PROPOSTA.md: o checklist de regras do Lote de Produção tende a crescer (ex.: um produto específico exigir uma checagem adicional de validade da matéria-prima, ou um cliente exigir uma tolerância de peso diferente de 5% para determinada linha de produto). Com o código "antes", qualquer uma dessas mudanças exigiria editar ProductionBatch diretamente — a mesma classe coberta por toda a suíte de testes do agregado — misturando, no mesmo arquivo e pelo mesmo motivo estrutural, decisões de negócio que não têm relação entre si (peso não tem nada a ver com lecitinização, que não tem nada a ver com conflito de tipo de leite). A classe não estava fechada para modificação diante de uma extensão esperada do conjunto de regras.

A refatoração

Commit "depois": <HASH-DEPOIS> — refactor: extrai regras de qualidade do ProductionBatch em classes Strategy (OCP).

Extraí cada regra para sua própria classe, atrás de uma interface abstrata específica, e ProductionBatch passou a receber essas regras por injeção no construtor (com uma implementação padrão caso nada seja passado), em vez de implementá-las internamente:

python
class WettabilityRule(ABC):
    @abstractmethod
    def check(self, batch: "ProductionBatch") -> Optional[str]:
        raise NotImplementedError


class WettabilityMustBeApprovedRule(WettabilityRule):
    def check(self, batch: "ProductionBatch") -> Optional[str]:
        if batch.wettability_result != TestResult.APPROVED:
            return "Wettability test not approved."
        return None

O mesmo padrão foi aplicado às outras três regras (SampleWeightRule / WeightToleranceRule, LecithinizationRule / MandatoryLecithinizationForGoatMilkRule, MilkTypeConflictRule / SameDayDifferentMilkTypeRule). ProductionBatch passou a chamar self.wettability_rule.check(self) (e equivalentes) em vez de ter a condição escrita no próprio método — e wettability_rule é uma @property que usa a regra injetada, ou cai para um padrão de classe quando nenhuma foi passada (ver "custo", abaixo, sobre por que isso não é feito só no __init__).

Com isso, uma regra nova ou uma variação de regra existente (ex.: tolerância de peso diferente para uma linha de produto) entra como uma nova classe que implementa a interface correspondente, injetada na criação do lote — sem tocar em ProductionBatch nem nas regras já existentes e testadas.

Como os testes garantiram que o comportamento não mudou
A suíte de testes unitários do agregado antes da mudança: 43 passed (pytest tests/unit/test_production_batch.py -q, commit <HASH-ANTES>).
Depois da mudança: 44 passed — os mesmos 43 testes continuam verdes, sem nenhuma alteração nas próprias asserções, mais um teste novo.
O teste novo, test_release_behavior_can_be_extended_via_injected_rule_without_modifying_production_batch (tests/unit/test_production_batch.py), injeta uma AlwaysApprovedWettabilityRule (uma subclasse de WettabilityRule escrita só para o teste, fora de ProductionBatch) e comprova que um lote com wettability_result ainda PENDING — que, com a regra padrão, reprovaria o lote (test_batch_with_pending_wettability_is_non_conforming_on_release) — é liberado normalmente quando essa regra é trocada. Ou seja, prova que o comportamento de aprovação hoje vem da regra injetada, não de uma condição fixa dentro de release(). Sem a refatoração, esse teste não seria possível: no código "antes" não existe nenhum ponto de extensão — a condição if self.wettability_result != TestResult.APPROVED está hard-coded dentro do método, e mudar esse comportamento exigiria editar ProductionBatch diretamente.
Também foi necessário um ajuste de compatibilidade com o mapeamento imperativo do SQLAlchemy: um ProductionBatch recarregado do banco não passa pelo __init__ (o SQLAlchemy reconstrói o objeto direto a partir das colunas), então as quatro regras passaram a ser expostas por @property com getattr(self, "_regra", <regra_padrão_da_classe>), em vez de depender apenas do que foi atribuído em __init__. Os testes e2e que liberam lotes recarregados do banco (tests/e2e/test_production_batches_api.py) continuaram passando sem alteração depois desse ajuste, confirmando que a regra padrão é aplicada corretamente também para objetos vindos do banco.
O custo e por que compensa

Custo: quatro novas interfaces (SampleWeightRule, LecithinizationRule, MilkTypeConflictRule, WettabilityRule) e quatro implementações padrão, em vez de quatro condições inline. ProductionBatch ganhou quatro parâmetros opcionais no construtor e quatro @property para resolver a regra efetiva (injetada ou padrão).

Por que compensa: o custo é oito classes pequenas e sem estado mutável relevante (cada uma com um único método, check); o que ele evita é editar ProductionBatch — a Aggregate Root do agregado, coberta por 44 testes unitários e pelos testes e2e da API — toda vez que uma regra de qualidade muda ou uma nova é adicionada. Na mesma lógica de custo de modificabilidade discutida para o CollectionPoint, o ganho aqui é concentrar uma mudança de regra de negócio em uma classe nova e isolada, em vez de um if a mais dentro de um método já testado do agregado central. Como a PROPOSTA.md já aponta o Lote de Produção como o agregado com mais regras de negócio específicas por tipo de produto, essa é uma mudança com probabilidade concreta de se repetir ao longo da Fase 2.
---

## Lucas Ardelino Alves da Silva — `RawMaterialReceipt` (agregado de recebimento)

### Princípio violado: Open/Closed Principle (OCP), exposto por uma mudança plausível de requisito

**Código anterior:** [`2919fc4`](../../commit/2919fc4), de 29/09/2026.

```python
class RawMaterialReceipt:
    def __init__(self, id_: int, status: RawMaterialReceiptStatus):
        self.id_ = id_
        self.status = status

    @property
    def approved(self) -> bool:
        return self.status == RawMaterialReceiptStatus.APPROVED
```

### O problema concreto

O recebimento armazenava um status que podia ser alterado diretamente, sem
representar quais transições eram permitidas. Uma mudança plausível para o
domínio é colocar em quarentena uma matéria-prima com resultado inconclusivo e
permitir sua aprovação ou reprovação depois de um reteste. Sem uma estrutura
para essas regras, a lógica de cada novo estado e suas transições acabaria
concentrada no próprio recebimento ou espalhada pelos chamadores, exigindo
modificações à medida que o ciclo de vida crescesse.

### A refatoração

**Commit "depois":** [`bdbad53`](../../commit/bdbad53) — `feat: adiciona ciclo State ao recebimento de matéria-prima`.

Introduzi estados separados para pendente, em quarentena, aprovado e rejeitado.
`RawMaterialReceipt` delega as operações ao estado atual; seu status passou a
ser somente leitura, e transições inválidas lançam `ValueError`. O registro
`_RECEIPT_STATES` associa cada status à implementação correspondente. O ORM
continua persistindo o enum na coluna existente, agora mapeada para `_status`.

### Como os testes cobrem a mudança

`tests/unit/test_production_batch.py::TestRawMaterialReceipt` cobre aprovação,
reprovação, quarentena, reteste e transições inválidas.
`tests/integration/test_orm.py::test_receipt_state_transitions_survive_orm_reload`
cobre as transições depois de salvar e recarregar o recebimento pelo SQLAlchemy.
A [CI do commit `bdbad53`](https://github.com/Lucas172UFF/LactoQC/actions/runs/43351331311)
passou.

### O custo e por que compensa

A mudança acrescenta quatro classes de estado e um registro que associa status
a estados. Também exige mapear `_status` para a coluna `status` do banco. Esse
custo mantém as regras de transição junto dos estados correspondentes e evita
que o recebimento aceite alterações arbitrárias de status.

---

## André Meschesi Dantas — `entrypoints/flask_app.py` (Infraestrutura compartilhada e API)

> Entregue em 16/11/2026, depois do prazo do checkpoint 2 (03/11).

### Princípio violado: Single Responsibility Principle (SRP)

**Commit "antes":** `d98d499` (30/09/2026), o último commit anterior a 06/10 que
alterou `src/LactoQC/entrypoints/flask_app.py`.

```python
# src/LactoQC/entrypoints/flask_app.py @ d98d499
def create_app(session_factory: sessionmaker | None = None) -> Flask:
    """Em produção cria engine/tabelas via DATABASE_URL; nos testes recebe a session_factory."""
    app = Flask(__name__)

    if session_factory is None:
        engine = create_engine(os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
        orm.start_mappers()
        orm.start_mappers_production_batch()
        orm.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)

    app.config["SESSION_FACTORY"] = session_factory
    ...
```

### O problema concreto

`create_app` é a *app factory* do Flask. Pela responsabilidade que tem, só
deveria mudar por motivos da camada web: registrar blueprints, tratar erros,
abrir e fechar a sessão de cada requisição. Mas ela também **montava a
persistência**: criava o engine, sabia **quais funções de mapeamento existem**
e criava as tabelas. São dois motivos de mudança, de dois responsáveis
diferentes: quem mantém a API e quem mantém o mapeamento de cada agregado.

A evidência está no histórico. No commit `d98d499`, o Aloysio adicionou o
agregado Lote de Produção e teve de editar `flask_app.py` por um motivo
**puramente de persistência**:

```diff
         orm.start_mappers()
+        orm.start_mappers_production_batch()
         orm.metadata.create_all(engine)
```

E o conhecimento "quais mapeamentos existem" não estava só ali. O mesmo par
`start_mappers()` / `start_mappers_production_batch()` aparecia em **três
lugares**: em `create_app` e em duas fixtures de `tests/conftest.py`
(`session_factory` e `sqlite_session_production_batch`). Qualquer agregado novo
com mapeamento próprio (por exemplo, o Recebimento de matéria-prima, previsto
na PROPOSTA §4.1) exigiria editar os três. Esquecer um deles é justamente a
falha descrita no risco R-01 de `docs/arquitetura.md` (mapeamento como estado
global: um erro de mapeamento derruba tudo).

Havia ainda um efeito colateral: o caminho de produção de `create_app` (sem
`session_factory`) **não era testado por nenhum teste**, porque os testes
sempre injetavam a fábrica de sessões. A lógica de montar o banco ficava
escondida dentro da app factory, sem cobertura.

### A refatoração

**Commit "depois":** `00f5522` (meu).

1. **`src/LactoQC/adapters/database.py` (novo).** `build_session_factory(database_url)`
   cria o engine, ativa os mapeamentos, cria as tabelas e devolve o `sessionmaker`.
   A persistência passa a ser montada na camada de adaptadores, que é onde ela
   pertence.
2. **`src/LactoQC/adapters/orm.py`.** Nova função `start_all_mappers()`, que é o
   **único** lugar que lista os mapeamentos dos agregados.
3. **`src/LactoQC/entrypoints/flask_app.py`.** `create_app` só delega:

   ```python
   if session_factory is None:
       session_factory = build_session_factory(
           os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
       )
   ```

   O módulo não importa mais `create_engine` nem `orm`.
4. **`tests/conftest.py`.** As duas fixtures passam a chamar `start_all_mappers()`.

Com isso, adicionar um agregado com mapeamento próprio muda **um arquivo da
camada de adaptadores** (`orm.py`), em vez de três arquivos em duas camadas
diferentes.

### Como os testes garantiram que o comportamento não mudou

- A suíte completa passava antes (`193 passed`) e continuou passando depois
  (`195 passed`). Nenhum teste existente foi alterado; em `tests/conftest.py`
  mudou só a forma de ativar os mapeamentos.
- Os testes e2e (`tests/e2e/`) criam a aplicação por `create_app(session_factory)`
  e exercitam todas as rotas dos dois agregados. Eles provam que a parte web da
  app factory continuou igual.
- O caminho de produção, que não tinha teste nenhum, ganhou dois testes em
  `tests/integration/test_database.py`:
  - `test_build_session_factory_maps_all_aggregates_and_creates_tables`: com
    um banco SQLite em memória, os repositórios dos dois agregados conseguem
    consultar o banco, o que só acontece se todos os mapeamentos e tabelas
    existirem.
  - `test_create_app_without_session_factory_uses_database_url`: com
    `DATABASE_URL` apontando para SQLite em memória, `create_app()` sobe e
    responde `/health` e `/production-batches`.

### O custo e por que compensa

**Custo:** um módulo a mais (`database.py`, 18 linhas) e uma função a mais em
`orm.py`. Para saber como o banco é montado em produção, agora é preciso abrir
um arquivo a mais. Além disso, a refatoração **não elimina** a edição a cada
agregado novo: `start_all_mappers()` ainda precisa ganhar uma linha. O que muda
é **onde** essa edição acontece.

**Por que compensa:** a mudança que antes se espalhava por três lugares, em duas
camadas, passa a acontecer em um lugar só, na camada que é dona do assunto.
`flask_app.py` volta a ter um único motivo de mudança (a configuração web), e o
caminho de produção da aplicação ganhou cobertura de teste que não existia.
Essa separação também preparou o padrão GoF do checkpoint 3 (ver `docs/gof.md`):
com a persistência fora de `create_app`, a app factory passou a ser o lugar
natural para escolher **qual família de repositórios** a API usa.
