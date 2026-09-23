# LactoQC

Sistema de controle de qualidade para indústria de laticínios, desenvolvido como projeto acadêmico da disciplina de Projeto de Software — UFF 2026.2.

O LactoQC tem como objetivo representar, de forma simplificada, o processo de controle de qualidade de uma indústria que recebe leite em pó a granel, realiza análises da matéria-prima, acompanha o processo produtivo e monitora as condições da fábrica.

O projeto é desenvolvido utilizando conceitos de arquitetura em camadas, Domain-Driven Design (DDD) e Test-Driven Development (TDD).


## Sobre o sistema

O controle de qualidade representado pelo LactoQC acontece em três momentos principais:

### Recebimento de matéria-prima

Cada lote recebido passa por análises de qualidade antes de poder ser utilizado na produção.

Entre as verificações previstas estão:

- umidade;
- teor de gordura;
- acidez;
- partículas queimadas;
- presença de antibióticos.

O agregado responsável por essas regras é **Recebimento de Matéria-Prima**.


### Controle do lote de produção

Durante a produção, são realizados testes para verificar se o produto está dentro das especificações esperadas.

Entre eles:

- controle do peso das embalagens;
- teste de molhabilidade;
- controle de lecitinização quando aplicável;
- validação da matéria-prima utilizada;
- liberação ou reprovação do lote.

O agregado responsável por essas regras é **Lote de Produção**.


### Monitoramento da fábrica

Antes do início da produção são realizadas medições das condições da fábrica.

Entre elas:

- cloro da água;
- pH da água;
- temperatura das salas.

Quando uma medição estiver fora da faixa definida, o sistema deverá registrar uma **não conformidade**.

O agregado responsável por essas regras é **Ponto de Coleta**.


# Agregados do domínio

O domínio do sistema foi dividido inicialmente em três agregados principais:

| Agregado | Responsabilidade |
|---|---|
| Recebimento de Matéria-Prima | Controlar as análises e decidir se uma matéria-prima pode ser utilizada |
| Ponto de Coleta | Controlar as medições ambientais e identificar valores fora da especificação |
| Lote de Produção | Controlar as regras de qualidade relacionadas à produção e liberação de lotes |

As regras detalhadas de cada agregado estão documentadas em [`Proposta.md`](Proposta.md).


# Entidades principais

O domínio possui inicialmente as seguintes entidades e conceitos de negócio:

- Recebimento de matéria-prima
- Lote de produção
- Ponto de coleta
- Medição
- Lecitinização
- Amostra de peso
- Não conformidade
- Especificação

A modelagem dessas entidades será desenvolvida de forma incremental conforme os checkpoints da disciplina.


# Estrutura do projeto

Atualmente, o projeto está organizado da seguinte forma:

```text
LactoQC/
│
├── .github/
│
├── src/
│   └── LactoQC/
│       │
│       ├── adapters/
│       │
│       ├── domain/
│       │
│       ├── entrypoints/
│       │
│       └── service_layer/
│
├── tests/
│
├── Proposta.md
├── README.md
└── requirements.txt