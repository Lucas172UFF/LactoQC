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

O projeto foi inspirado na rotina de uma fábrica que recebe leite em pó a granel e realiza o reenvase do produto para diferentes marcas. Atualmente, parte do controle de qualidade é realizada utilizando registros manuais e planilhas.

O objetivo do sistema é representar, de forma simplificada, esse processo e aplicar regras de negócio relacionadas à aprovação de matérias-primas, ao controle de produção e ao monitoramento da fábrica.

O sistema não é apenas um cadastro de informações. Existem regras que precisam ser protegidas, como:

- faixas aceitáveis para medições;
- aprovação ou reprovação automática;
- obrigatoriedade de testes;
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

O sistema é organizado em três agregados de domínio e um módulo técnico compartilhado.

### 4.1 Recebimento de matéria-prima

Responsável por registrar e avaliar a qualidade da matéria-prima antes de ela ser utilizada na produção.

#### Regras de negócio

- Umidade não pode ultrapassar 5%.
- Gordura deve ser de pelo menos 26%.
- Acidez deve respeitar o limite máximo definido.
- Partículas queimadas devem permanecer dentro do limite aceitável.
- O teste de antibiótico deve ser negativo.
- Um resultado positivo para antibiótico reprova automaticamente o recebimento.
- Um recebimento só pode ser aprovado após a realização de todos os testes obrigatórios.
- Um lote de produção somente pode utilizar matéria-prima aprovada.

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

Este módulo concentra os componentes técnicos compartilhados necessários para integrar os agregados e disponibilizar operações pela API.

#### Responsabilidades

- Configurar o mapeamento objeto-relacional com SQLAlchemy em `adapters/orm.py`.
- Criar e manter abstrações de repositório em `adapters/repository.py`.
- Configurar a aplicação Flask em `entrypoints/flask_app.py`.
- Implementar os casos de uso, rotas e testes end-to-end da API do Ponto de Coleta.
- Apoiar a integração entre os agregados e a execução da suíte de testes.
- Manter a automação de testes no GitHub Actions.

#### Responsável

André Meschesi Dantas.

## 5. Especificação

A especificação representa as faixas aceitáveis para diferentes medições. Inicialmente, ela é utilizada como configuração compartilhada pelos agregados.

Na Fase 2, caso seja necessário versionar especificações por produto ou processo, sua modelagem poderá ser revista.

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

| Integrante | Módulo principal | Responsabilidades na Fase 1 |
|---|---|---|
| Lucas Ardelino Alves da Silva | Recebimento de matéria-prima | Evolução do agregado de recebimento, regras de aprovação/reprovação, resultados de testes obrigatórios e testes unitários relacionados. |
| João Gabriel Pimentel | Ponto de coleta | Modelo de domínio do Ponto de Coleta, especificações, medições, não conformidades e testes de integração do agregado. |
| Aloysio Felipe Saad Silva | Lote de produção | Modelo de domínio do Lote de Produção, peso, lecitinização, liberação/reprovação e testes unitários do agregado. |
| André Meschesi Dantas | Infraestrutura compartilhada e API | ORM, abstrações de repositório, configuração Flask, serviços, rotas, testes e2e e integração da API do Ponto de Coleta. |

Todos os integrantes participam da revisão do código, documentação, integração e execução da suíte de testes.

## 8. Estrutura do projeto

```text
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
