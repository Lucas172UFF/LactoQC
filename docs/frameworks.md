# Frameworks no LactoQC

## Escopo da análise

O LactoQC usa Flask para expor uma API HTTP, SQLAlchemy para persistir os agregados e pytest para executar a suíte de testes. Esta análise considera o sistema como um todo: os agregados `CollectionPoint`, `ProductionBatch` e `RawMaterialReceipt`, as rotas da API, os adaptadores de persistência, o service layer e os testes.

Neste documento, “frameworks” é usado no sentido amplo do enunciado. Flask e pytest são frameworks; SQLAlchemy é mais precisamente um toolkit de persistência e ORM. Cada ferramenta participa de uma parte diferente do sistema.

## Papel e localização de cada ferramenta

| Ferramenta | Papel no sistema | Camada e arquivos |
|---|---|---|
| Flask | Recebe requisições HTTP, encaminha URLs para handlers, fornece o contexto da requisição e ajuda a construir respostas JSON. Também permite registrar tratamento centralizado de erros. | Camada de entrada: `src/LactoQC/entrypoints/flask_app.py`, `collection_point_routes.py` e `production_batch_routes.py`. |
| SQLAlchemy | Cria conexões e sessões, mapeia objetos para tabelas, executa consultas e acompanha alterações para persistência. | Adaptadores: `src/LactoQC/adapters/database.py`, `orm.py` e `repository.py`. A sessão é usada também pelos casos de uso em `src/LactoQC/service_layer/services.py` para confirmar transações. |
| pytest | Descobre e executa testes, fornece fixtures e organiza a preparação e a limpeza dos ambientes de teste. | Testes em `tests/unit/`, `tests/integration/` e `tests/e2e/`; fixtures compartilhadas em `tests/conftest.py`; configuração em `pytest.ini`. |

Flask concentra a integração HTTP. As rotas do ponto de coleta estão em `collection_point_routes.py`; as rotas do lote de produção estão em `production_batch_routes.py`. Ambas usam os serviços e as fábricas de repositórios configuradas pela aplicação.

SQLAlchemy aparece nos mapeamentos dos dois agregados persistidos. `orm.py` contém as tabelas, relacionamentos e funções de mapeamento. `repository.py` implementa repositórios SQLAlchemy para `CollectionPoint` e `ProductionBatch`, além das fábricas que criam as famílias de repositórios. `database.py` monta o engine, ativa os mapeamentos e cria as tabelas.

pytest cobre o comportamento do domínio sem banco nos testes unitários, a persistência nos testes de integração e a API nos testes e2e. As fixtures em `conftest.py` oferecem sessões e bancos em memória aos testes que precisam deles.

## Independência do domínio

As classes de negócio ficam em `src/LactoQC/domain/model.py` e são classes Python comuns. O domínio não importa Flask nem SQLAlchemy e não precisa conhecer requisições HTTP, sessões, tabelas ou fixtures para aplicar suas regras.

A persistência é conectada ao domínio na camada de adaptadores. Em `adapters/orm.py`, o SQLAlchemy usa mapeamento imperativo (`map_imperatively`) para associar as classes de domínio às tabelas de `CollectionPoint`, `ProductionBatch`, `RawMaterialReceipt` e seus objetos relacionados. As entidades continuam separadas das definições das tabelas.

Os repositórios em `adapters/repository.py` isolam as consultas e operações de persistência. As rotas chamam o service layer, que coordena os casos de uso e confirma a sessão. Assim, Flask fica na entrada do sistema e SQLAlchemy fica principalmente nos adaptadores.

Há uma dependência explícita de `Session` no service layer: `services.py` importa o tipo SQLAlchemy e recebe uma sessão para executar `commit()`. Portanto, o domínio está independente dos frameworks, enquanto a camada de aplicação ainda conhece a fronteira transacional do SQLAlchemy.

## Inversão de controle

Inversão de controle ocorre quando o framework coordena o fluxo e chama código registrado pelo grupo. No LactoQC, isso aparece em pelo menos três pontos:

1. **Despacho de rotas pelo Flask.** As funções decoradas com `@bp.get` e `@bp.post` são registradas nos blueprints. Quando chega uma requisição compatível, Flask localiza e chama o handler. Isso ocorre nas rotas de `CollectionPoint` e `ProductionBatch`, em `entrypoints/collection_point_routes.py` e `entrypoints/production_batch_routes.py`.

2. **Encerramento do contexto pelo Flask.** `flask_app.py` registra a função `close_session` com `@app.teardown_appcontext`. Flask chama esse callback ao encerrar o contexto da aplicação, e o código do grupo fecha a sessão associada à requisição.

3. **Descoberta de testes e resolução de fixtures pelo pytest.** pytest encontra as funções `test_*`, executa cada teste e fornece os argumentos solicitados, como `client` ou `session`, resolvendo-os pelas fixtures de `tests/conftest.py`. Nas fixtures que usam `yield`, pytest também retoma a execução para realizar a limpeza do recurso.

Esses exemplos mostram a diferença entre framework e biblioteca: o framework coordena um ciclo de execução e chama os pontos de extensão registrados pelo grupo. Uma biblioteca oferece funções ou objetos que o código da aplicação chama quando precisa deles. Flask e pytest coordenam partes do fluxo do sistema e dos testes. SQLAlchemy é um toolkit/ORM que a aplicação usa para persistência, além de coordenar o ciclo de vida das sessões.

## Padrões de projeto fornecidos ou usados internamente pelas ferramentas

Os três padrões abaixo são os exemplos principais de mecanismos do SQLAlchemy usados pelo projeto. A tabela também registra o Front Controller do caminho de requisições Flask como padrão arquitetural adicional; ele não é necessário para completar os três exemplos de SQLAlchemy.

| Padrão | Ferramenta | Como aparece no LactoQC |
|---|---|---|
| Data Mapper | SQLAlchemy ORM | `adapters/orm.py` mapeia classes de domínio para tabelas com `map_imperatively`, incluindo os agregados `CollectionPoint` e `ProductionBatch`. O domínio não precisa herdar de uma classe do ORM para ser persistido. |
| Identity Map | SQLAlchemy Session | Os repositórios consultam entidades usando a sessão, por exemplo com `session.get(CollectionPoint, id_)` em `adapters/repository.py`. Dentro de uma mesma sessão, o ORM mantém uma identidade de objeto por identidade persistida, evitando representar repetidamente o mesmo registro como instâncias distintas naquele contexto. |
| Unit of Work | SQLAlchemy Session | Os repositórios adicionam entidades à sessão com `session.add(...)`; os casos de uso em `service_layer/services.py` chamam `session.commit()`. A sessão acompanha as alterações pendentes e as confirma como parte de seu ciclo de trabalho. |
| Front Controller / despachante | Flask | `entrypoints/flask_app.py` cria a aplicação central e registra blueprints. Flask recebe a requisição e a encaminha ao handler correspondente nos módulos de rotas. |

O Data Mapper, o Identity Map e o Unit of Work são comportamentos oferecidos pela integração ORM e pela `Session` do SQLAlchemy; o código do grupo os utiliza por meio dos adaptadores e dos serviços. O Unit of Work citado aqui é o mecanismo interno da sessão SQLAlchemy. Isso não significa que o projeto tenha criado um módulo próprio `unit_of_work.py`.

O Front Controller descreve a organização da entrada HTTP: a aplicação Flask recebe as requisições e despacha para os handlers registrados. O domínio não participa desse despacho.

## Frameworks e bibliotecas

Flask e pytest controlam parte do fluxo: Flask chama handlers registrados conforme a URL e o método HTTP, e pytest descobre e executa testes, resolvendo fixtures. Esse controle do ciclo de execução caracteriza o uso de framework.

SQLAlchemy é um toolkit/ORM usado pelo código do grupo para mapear, consultar e persistir objetos. A aplicação cria e fornece sessões; os adaptadores e casos de uso chamam a API do SQLAlchemy para executar suas operações. O ORM, por sua vez, controla o estado persistente dos objetos mapeados durante a vida da sessão.

## O que mudaria com Django

Django ofereceria um conjunto mais integrado de recursos, incluindo roteamento, ORM, migrações, autenticação, administração, templates e formulários. O LactoQC substituiria a app factory e os blueprints Flask por configurações de URLs e views Django, e trocaria o mapeamento imperativo do SQLAlchemy pelo ORM do Django.

Uma implementação convencional do Django define modelos persistentes como subclasses de `django.db.models.Model`. Isso poderia aproximar as entidades de domínio da infraestrutura de persistência. Seria possível preservar classes de domínio independentes e criar modelos Django separados para a persistência, mas essa separação exigiria adaptadores e conversões explícitas.

Django reduziria parte da configuração manual e forneceria funcionalidades prontas, especialmente úteis para aplicações com autenticação, administração e interface HTML. Para o escopo atual — uma API JSON pequena, sem autenticação ou interface administrativa — esses recursos acrescentariam componentes que o sistema não usa. A decisão dependeria do peso dado à produtividade integrada do Django em comparação com a separação explícita entre domínio, entrada HTTP e persistência adotada no LactoQC.

## Evidência do agregado Ponto de Coleta (João Gabriel Pimentel)

Os três pontos abaixo são exemplos concretos, tirados do agregado que acompanho
(`CollectionPoint`), dos mecanismos descritos nas seções anteriores.

**Despacho de rota pelo Flask.** `register_measurement`
(`src/LactoQC/entrypoints/collection_point_routes.py:122-136`) nunca é chamada
pelo código da própria rota; ela só é registrada no blueprint com
`@bp.post("/collection-points/<int:collection_point_id>/measurements")`, e é o
despachante do Flask quem a invoca ao receber a requisição correspondente. O
mesmo vale para `close_session` (`flask_app.py:43-47`): o callback é
registrado com `@app.teardown_appcontext`, e é o Flask quem decide o instante
de chamá-lo, ao final de cada contexto de aplicação — nunca o código da rota.

**Fixtures do pytest nos meus testes.** `tests/unit/test_collection_point.py`
e `tests/unit/test_collection_point_services.py` declaram `fake_repo`,
`fake_session`, `client` e `session` como parâmetros, sem chamá-los; é o
pytest quem resolve a cadeia de dependências em `tests/conftest.py` (por
exemplo, `client` depende de `session_factory`, que depende de
`in_memory_db`) e injeta cada valor antes do teste rodar, retomando o
generator depois do `yield` para o teardown.

**Unit of Work na sessão que uso.** Todo caso de uso do meu agregado em
`src/LactoQC/service_layer/services.py` (`register_measurement`,
`close_daily_record`, `create_collection_point`) termina com
`session.commit()`, sem nenhuma lógica própria de acumular ou ordenar
mudanças — isso é o que a `Session` do SQLAlchemy já faz por dentro, desde o
`repo.add(...)` ou a chamada a `collection_point.add_measurement(...)` até o
commit.
