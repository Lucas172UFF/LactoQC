# LactoQC — Registro de Decisões e Contribuições

Este documento registra as decisões técnicas tomadas durante o desenvolvimento
do LactoQC e a contribuição individual de cada integrante em cada checkpoint.

Cada integrante deve preencher sua própria subseção com:

- o que implementou;
- os arquivos em que trabalhou;
- os commits de sua autoria;
- uma decisão de projeto tomada;
- a justificativa dessa decisão;
- eventuais dificuldades encontradas;
- uso de IA, quando houver, dentro dos limites definidos pela disciplina.

As responsabilidades principais estão divididas por agregado:

| Integrante | Agregado principal |
|---|---|
| Lucas Ardelino Alves da Silva | Recebimento de matéria-prima |
| João Gabriel Pimentel | Ponto de coleta |
| Aloysio Saad | Lote de produção |

---

# Fase 1

## Checkpoint 1 — Modelo de domínio

**Tag:** `fase1-checkpoint-1`  
**Semana:** 2

### Objetivo do checkpoint

- modelar entidades e objetos de valor do domínio;
- implementar pelo menos dois agregados;
- criar testes unitários correspondentes;
- manter o domínio independente de infraestrutura;
- garantir que os testes unitários sejam executados pela CI.

---

## João Gabriel Pimentel — Agregado Ponto de Coleta

### O que foi implementado

Foi implementado o modelo de domínio relacionado ao agregado **Ponto de Coleta**,
responsável pelo acompanhamento das medições realizadas nos ambientes da fábrica.

O agregado possui `CollectionPoint` como Aggregate Root e utiliza as seguintes
estruturas de domínio:

- `CollectionPoint`;
- `Measurement`;
- `Specification`;
- `NonConformity`;
- `MeasurementType`;
- `MeasurementUnit`.

Foram modelados inicialmente os seguintes tipos de medição:

- pH;
- cloro;
- temperatura.

Também foram implementadas regras de domínio para:

- associar cada tipo de medição à sua unidade esperada;
- impedir a criação de uma `Specification` cuja unidade seja incompatível com o
  tipo de medição;
- impedir a criação de uma `Measurement` cuja unidade seja incompatível com o
  tipo de medição;
- impedir a criação de uma `Specification` cujo valor mínimo seja maior que o
  valor máximo;
- exigir que um `CollectionPoint` possua exatamente uma `Specification` para cada
  `MeasurementType`;
- impedir specifications duplicadas para o mesmo tipo de medição;
- registrar medições no `CollectionPoint`;
- verificar a medição utilizando a `Specification` correspondente ao seu tipo;
- criar automaticamente uma `NonConformity` quando uma medição estiver fora da
  faixa definida;
- considerar os valores mínimo e máximo da specification como pertencentes à
  faixa válida.

A geração automática de não conformidade está alinhada à regra prevista para o
agregado de Ponto de Coleta, segundo a qual medições fora da especificação devem
gerar uma não conformidade.

### Testes unitários

Foram implementados testes unitários para as principais regras do agregado.

Os testes de `Specification` verificam:

- criação de specification de pH;
- criação de specification de cloro;
- criação de specification de temperatura;
- rejeição de `min_value` maior que `max_value`;
- rejeição de unidade incompatível com o tipo de medição;
- valor dentro da faixa;
- valor abaixo da faixa;
- valor acima da faixa;
- valores exatamente nos limites mínimo e máximo.

Os testes de `Measurement` verificam:

- criação de medição de pH;
- criação de medição de cloro;
- criação de medição de temperatura;
- rejeição de unidade incompatível com o tipo de medição.

Os testes de `CollectionPoint` verificam:

- rejeição da criação sem as specifications obrigatórias;
- criação válida com uma specification para cada tipo;
- rejeição quando alguma specification está ausente;
- rejeição quando existem specifications duplicadas;
- registro de uma nova medição;
- geração de `NonConformity` para valor abaixo da faixa;
- geração de `NonConformity` para valor acima da faixa;
- ausência de `NonConformity` para valores exatamente nos limites;
- associação da `NonConformity` à `Measurement` correspondente;
- associação da `NonConformity` à `Specification` correspondente;
- seleção da specification correta para medições de pH, cloro e temperatura.

Foram criadas funções auxiliares nos testes para reduzir repetição na criação de
specifications válidas e melhorar a legibilidade dos cenários de teste.

### Configuração dos testes e CI

Foi criado um `pytest.ini` para configurar a descoberta dos testes e permitir que
o pacote localizado em `src/` seja importado corretamente durante a execução do
pytest.

Também foi configurado um workflow do GitHub Actions para executar os testes
automaticamente em:

- Pull Requests direcionados para `main`;
- alterações integradas à branch `main`.

O workflow:

1. realiza checkout do repositório;
2. configura o ambiente Python;
3. instala as dependências presentes em `requirements.txt`;
4. executa o `pytest`.

### Arquivos trabalhados

- `src/LactoQC/domain/models.py`
- `tests/unit/test_collection_point.py`
- `pytest.ini`
- `.github/workflows/tests.yml`
- `DECISIONS.md`

### Commits de autoria

> Preencher com os hashes após a finalização dos commits.

- `19863f1` - `organiza estrutura inicial e documentação da Fase 1`
- `d3aa652` - `chore: organiza estrutura inicial e criação de arquivos base vazios` 
- `87bccb1` — `feat: implementa modelo de domínio do ponto de coleta`
- `00e1ab3` — `test: adiciona testes unitários do ponto de coleta`
- `00e1ab3` — `chore: configura CI para execução dos testes`
- `00e1ab3` — `docs: atualiza registro de decisões do checkpoint 1`

### Decisões de projeto

#### CollectionPoint como Aggregate Root

Foi decidido que `CollectionPoint` será a Aggregate Root do agregado de Ponto de
Coleta.

A entidade é responsável por controlar suas medições, specifications e
não conformidades e por garantir as invariantes relacionadas a esses objetos.

Essa decisão centraliza as regras do agregado e evita que operações que afetem
sua consistência sejam realizadas sem passar pelo `CollectionPoint`.

#### Specifications obrigatórias por tipo de medição

Foi definido que cada `CollectionPoint` deve possuir exatamente uma
`Specification` para cada `MeasurementType`.

Dessa forma, todo tipo de medição aceito pelo ponto de coleta possui previamente
uma faixa de referência conhecida.

A regra também impede ambiguidades como a existência de duas specifications
diferentes para o mesmo tipo de medição.

#### Associação entre tipo de medição e unidade

Foi criado um mapeamento entre `MeasurementType` e `MeasurementUnit`.

A associação definida atualmente é:

- cloro → `mg/L`;
- temperatura → `°C`;
- pH → sem unidade.

Tanto `Measurement` quanto `Specification` validam essa associação no momento
de sua criação.

Essa decisão evita estados inválidos, como uma medição de temperatura
representada em `mg/L`.

#### Responsabilidade da Specification pela própria faixa

Foi decidido que a própria `Specification` deve garantir que:

`min_value <= max_value`

Essa validação foi mantida na própria classe porque os valores mínimo e máximo
fazem parte do estado da `Specification`.

O `CollectionPoint`, por sua vez, permanece responsável pelas invariantes que
envolvem o conjunto de specifications do agregado.

#### Geração automática de NonConformity

Ao registrar uma `Measurement`, o `CollectionPoint` identifica a
`Specification` correspondente ao seu `MeasurementType`.

Caso o valor esteja fora da faixa configurada, uma `NonConformity` é criada
automaticamente e associada tanto à medição quanto à specification que foi
violada.

Os valores exatamente iguais ao mínimo e ao máximo são considerados válidos.

### Dificuldades encontradas

Durante a implementação foram identificados alguns pontos que exigiram revisão
da modelagem:

- definição da responsabilidade entre `CollectionPoint` e `Specification`;
- tratamento do pH como uma medição sem unidade;
- prevenção de specifications ausentes ou duplicadas;
- comparação entre objetos `Specification` nos testes;
- separação entre erro de domínio e geração de `NonConformity`;
- configuração do layout `src/` para execução do pytest;
- configuração do `PYTHONPATH` por meio do `pytest.ini`;
- preparação do workflow de CI no GitHub Actions.

Durante os testes também foi identificado que medições fora da specification não
devem lançar `ValueError`. Elas devem ser registradas e gerar uma
`NonConformity`, conforme a regra de domínio adotada.

### Pontos ainda não abordados neste checkpoint

A proposta prevê que as medições do Ponto de Coleta sejam realizadas antes do
início da produção.

Essa regra ainda não foi implementada neste momento, pois depende da definição
de como o horário ou estado de início da produção será disponibilizado ao
agregado de Ponto de Coleta.

A decisão será revisitada quando houver integração entre os agregados ou
definição do serviço responsável por fornecer essa informação.

### Uso de Inteligência Artificial

Foi utilizada IA somente como apoio durante o desenvolvimento, dentro dos
limites estabelecidos pela disciplina.

O uso ocorreu principalmente para:

- esclarecimento de conceitos de DDD, entidades, objetos de valor, Aggregate
  Root e invariantes;
- discussão conceitual de possíveis regras de domínio;
- explicação de sintaxe Python e pytest;
- compreensão de mensagens de erro;
- revisão de código escrito pelo próprio integrante;
- revisão da estrutura e dos cenários de testes;
- auxílio na compreensão da configuração do pytest e CI;
- exemplos didáticos utilizando domínios diferentes do LactoQC.

O código do domínio e os testes utilizados no projeto foram elaborados e
adaptados pelo integrante responsável, com a IA sendo utilizada como ferramenta
de apoio conceitual, revisão e explicação.