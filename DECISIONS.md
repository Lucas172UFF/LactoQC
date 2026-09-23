# DECISIONS.md

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
| Aloysio Saad| Lote de produção |

---

# Fase 1

## Checkpoint 1 — Modelo de domínio
**Tag:** `fase1-checkpoint-1`  
**Semana:** 2

Objetivo do checkpoint:

- modelar entidades e objetos de valor do domínio;
- implementar pelo menos dois agregados;
- criar testes unitários correspondentes;
- manter o domínio independente de infraestrutura;
- garantir que os testes unitários sejam executados pela CI.

