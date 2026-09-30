# PROPOSTA.md

## 1. Integrantes

| Nome | GitHub | E-mail |
|---|---|---|
| Lucas Ardelino Alves da Silva | Lucas172UFF | ardelino_lucas@id.uff.br |
| João Gabriel Pimentel | JoaogPimentel | j_gabriel@id.uff.br |
| Aloysio Felipe Saad Silva | AloysioSaad | aloysiosaad@id.uff.br |
| André Meschesi Dantas | meschesiandre-maker | meschesiandre@id.uff.br |

## 2. Sistema proposto

### LactoQC

O LactoQC é um sistema de controle de qualidade para uma indústria de laticínios.

O projeto foi inspirado na rotina de uma fábrica que recebe leite em pó a granel e realiza o reenvase do produto para diferentes marcas. Atualmente, parte do controle de qualidade é realizado utilizando registros manuais e planilhas.

O objetivo do sistema é representar, de forma simplificada, esse processo e aplicar regras de negócio relacionadas à aprovação de matérias-primas, controle de produção e monitoramento da fábrica.

O sistema não é apenas um cadastro de informações. Existem regras que precisam ser protegidas, como:

- faixas aceitáveis para medições;
- aprovação ou reprovação automática;
- obrigatoriedade de determinados testes;
- restrições para liberação de lotes;
- criação automática de não conformidades.

## 3. Entidades principais

O domínio do sistema possui inicialmente as seguintes entidades:

1. Recebimento de matéria-prima;
2. Lote de produção;
3. Ponto de coleta;
4. Medição;
5. Lecitinização;
6. Amostra de peso;
7. Não conformidade;
8. Especificação.

## 4. Agregados e módulos do sistema

O sistema será organizado em três agregados de domínio e um módulo técnico compartilhado.

### 4.1 Recebimento de matéria-prima

Responsável por decidir se um lote recebido pode ser utilizado na produção.

#### Regras de negócio

- Umidade não pode ultrapassar 5%.
- Gordura deve ser de pelo menos 26%.
- Acidez deve respeitar o limite máximo definido.
- Partículas queimadas devem permanecer dentro do limite aceitável.
- O teste de antibiótico deve ser negativo.
- Um resultado positivo para antibiótico reprova automaticamente o lote.
- O lote só pode ser aprovado após a realização de todos os testes obrigatórios.

#### Responsável

Lucas Ardelino Alves da Silva.

### 4.2 Ponto de coleta

Responsável pelo monitoramento das condições da fábrica.

#### Regras de negócio

- O cloro da água deve estar entre 0,5 e 5,0 mg/L.
- O pH da água deve estar entre 6,0 e 9,5.
- Cada sala possui uma faixa própria de temperatura aceitável.
- As medições devem ser realizadas antes do início da produção.
- Uma medição fora da especificação deve gerar uma não conformidade.

#### Responsável

João Gabriel Pimentel.

### 4.3 Lote de produção

Responsável pelo controle de qualidade de cada ordem de produção.

#### Regras de negócio

- Um lote de produção só pode utilizar matéria-prima previamente aprovada.
- Produtos de leite de cabra exigem registro de lecitinização.
- A proporção definida é de 5 gramas de lecitina por quilograma.
- O peso real do produto não pode variar mais de 5% do peso esperado.
- Leite de vaca e leite de cabra não podem ser processados no mesmo dia.
- Um lote só pode ser liberado após cumprir todos os testes exigidos.
- Um lote não conforme não pode ser reaberto sem justificativa.

#### Responsável

Aloysio Felipe Saad Silva.

### 4.4 Infraestrutura compartilhada e API

Este módulo não representa um agregado de negócio. Ele concentra os componentes técnicos compartilhados necessários para integrar os agregados e disponibilizar suas operações pela API.

#### Responsabilidades

- Configurar o mapeamento objeto-relacional com SQLAlchemy em `adapters/orm.py`.
- Criar e manter abstrações compartilhadas de repositório em `adapters/repository.py`.
- Configurar a aplicação Flask em `entrypoints/flask_app.py`.
- Implementar os casos de uso e endpoints relacionados ao Ponto de Coleta.
- Criar os testes end-to-end da API.
- Apoiar a integração entre os três agregados e a execução da suíte completa de testes.
- Manter a automação de testes no GitHub Actions.

#### Responsável

André Meschesi Dantas.

## 5. Especificação

A especificação representa as faixas aceitáveis para diferentes medições. Inicialmente, será utilizada como configuração compartilhada pelos três agregados.

Na Fase 2, caso seja necessário versionar diferentes especificações por produto ou processo, sua modelagem poderá ser revista.

## 6. Casos de uso previstos

1. Registrar recebimento de matéria-prima.
2. Registrar resultados dos testes de recebimento.
3. Decidir se uma matéria-prima foi aprovada ou reprovada.
4. Registrar medição em um ponto de coleta.
5. Verificar se uma medição está dentro da especificação.
6. Gerar uma não conformidade para uma medição inválida.
7. Fechar o registro diário de monitoramento.
8. Abrir um lote de produção.
9. Registrar lecitinização.
10. Registrar amostras de peso.
11. Registrar resultados de qualidade do lote.
12. Liberar ou reprovar um lote de produção.
13. Consultar o histórico completo de um lote.
14. Consultar não conformidades por período ou origem.

## 7. Divisão de responsabilidades

| Integrante | GitHub | Agregado(s) ou módulo(s) | Responsabilidades na Fase 1 |
|---|---|---|---|
| Lucas Ardelino Alves da Silva | Lucas172UFF | Recebimento de matéria-prima | Modelo de domínio, testes unitários, repositório, testes de integração e casos de uso do agregado. |
| João Gabriel Pimentel | JoaogPimentel | Ponto de coleta | Modelo de domínio, regras do agregado, especificações, medições, não conformidades, repositório e testes de integração. |
| Aloysio Felipe Saad Silva | AloysioSaad | Lote de produção | Modelo de domínio, testes unitários, regras de liberação, amostras de peso, lecitinização e testes relacionados ao agregado. |
| André Meschesi Dantas | meschesiandre-maker | Infraestrutura compartilhada e API do Ponto de Coleta | ORM, abstrações de repositório, configuração Flask, serviços e endpoints do Ponto de Coleta, testes e2e e integração da aplicação. |

## 8. Uso de Inteligência Artificial

Foi utilizada inteligência artificial generativa como ferramenta de apoio ao desenvolvimento, dentro dos limites permitidos para a disciplina.

O uso incluiu esclarecimento de conceitos de arquitetura em camadas, DDD, TDD, SQLAlchemy, Flask, pytest, revisão de estrutura de código, discussão de regras de negócio e apoio na elaboração e revisão de testes.

As decisões sobre o domínio, a organização do projeto, a validação das regras de negócio e a integração final foram revisadas pelos integrantes do grupo.

## 9. Estrutura do projeto

O projeto utiliza uma organização em camadas, separando regras de domínio, persistência, serviços de aplicação, interface HTTP e testes.

LactoQC/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── LactoQC/
│       ├── __init__.py
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── orm.py
│       │   └── repository.py
│       ├── domain/
│       │   ├── __init__.py
│       │   └── model.py
│       ├── entrypoints/
│       │   ├── __init__.py
│       │   ├── collection_point_routes.py
│       │   └── flask_app.py
│       └── service_layer/
│           ├── __init__.py
│           └── services.py
├── tests/
│   ├── conftest.py
│   ├── e2e/
│   │   ├── test_app_base.py
│   │   └── test_collection_points_api.py
│   ├── integration/
│   │   ├── test_orm.py
│   │   └── test_repository.py
│   └── unit/
│       ├── test_collection_point.py
│       ├── test_collection_point_repository.py
│       └── test_production_batch.py
├── .gitignore
├── DECISIONS.md
├── PROPOSTA.md
├── README.md
├── pytest.ini
└── requirements.txt
