# PROPOSTA.md

## 1. Integrantes

| Nome | GitHub | E-mail |
|---|---|---|
| Lucas Ardelino Alves da Silva | Lucas172UFF | ardelino_lucas@id.uff.br |
| João Gabriel Pimentel | JoaogPimentel | j_gabriel@id.uff.br |
| Aloysio Felipe Saad Silva | AloysioSaad | aloysiosaad@id.uff.br |

## 2. Sistema proposto

### LactoQC

O LactoQC é um sistema de controle de qualidade para uma indústria de laticínios.

O projeto foi inspirado na rotina de uma fábrica que recebe leite em pó a granel e realiza o reenvase do produto para diferentes marcas.

Atualmente, parte do controle de qualidade é realizado utilizando registros manuais e planilhas.

O objetivo do sistema é representar de forma simplificada esse processo e aplicar regras de negócio relacionadas à aprovação de matérias-primas, controle de produção e monitoramento da fábrica.

O sistema não é apenas um cadastro de informações. Existem regras que precisam ser protegidas, como:

- faixas aceitáveis para medições;
- aprovação ou reprovação automática;
- obrigatoriedade de determinados testes;
- restrições para liberação de lotes;
- criação automática de não conformidades.

## 3. Entidades principais

O domínio possui inicialmente as seguintes entidades:

1. Recebimento de matéria-prima
2. Lote de produção
3. Ponto de coleta
4. Medição
5. Lecitinização
6. Amostra de peso
7. Não conformidade
8. Especificação

## 4. Agregados de domínio

O sistema será organizado inicialmente em três agregados.

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

---

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

---

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

Aloysio Saad

## 5. Especificação

A especificação representa as faixas aceitáveis para diferentes medições.

Inicialmente, ela será utilizada como uma configuração compartilhada pelos três agregados.

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

Cada integrante será responsável principalmente por um agregado.

| Integrante | Agregado |
|---|---|
| Lucas Ardelino | Recebimento de matéria-prima |
| João Gabriel | Ponto de coleta |
| Aloysio Saad| Lote de produção |

A responsabilidade acompanha o agregado ao longo das fases do projeto.

Isso significa que cada integrante participará da implementação de:

- modelo de domínio;
- testes unitários;
- repositório;
- testes de integração;
- camada de serviço;
- endpoints relacionados ao agregado;
- testes de ponta a ponta;
- evoluções da Fase 2 relacionadas ao mesmo agregado.

Dessa forma, todos os integrantes terão participação técnica contínua ao longo dos checkpoints.

Alterações nessa divisão serão documentadas no DECISIONS.md.