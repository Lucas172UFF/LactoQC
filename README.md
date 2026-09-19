# LactoQC
Sistema de controle de qualidade para indústria de laticínios — rastreabilidade de lotes de produção, monitoramento contínuo de água/ambiente e gestão de não conformidades. Projeto acadêmico (UFF — Projeto de Software 2026.2).


# O sistema: LactoQC

A ideia do projeto veio da experiência de um dos integrantes do grupo, que trabalha com controle de qualidade em uma fábrica de laticínios (uma indústria que recebe leite em pó a granel e o reembala em pacotes menores para diferentes marcas). O sistema simula, de forma simplificada, o controle de qualidade real desse tipo de fábrica — hoje feito manualmente, em papel e planilhas.


# O controle de qualidade acontece em três momentos:

Quando a matéria-prima chega. Antes de qualquer produção começar, cada lote de leite em pó recebido de um fornecedor passa por uma bateria de testes de laboratório: teste de umidade (leite muito úmido estraga mais rápido), teor de gordura, acidez (indica se o leite já começou a se decompor), presença de partículas queimadas (indica problema no processo de secagem do fornecedor) e teste de antibióticos, que precisa sempre dar negativo. Se o teste de antibiótico der positivo, o lote é reprovado automaticamente, não importa o resultado dos outros testes — e é devolvido ao fornecedor.

Quando um lote é produzido. Cada Ordem de Produção passa pelos seus próprios testes: peso real do produto embalado comparado ao peso esperado (verificado por amostragem), se o produto se dissolve corretamente em água (teste de molhabilidade) e — só para os produtos de leite de cabra — se a lecitina (um aditivo usado para melhorar a solubilidade do pó) foi adicionada na proporção e no tempo certos.

Monitoramento contínuo da fábrica. Todo dia, antes de começar a produção, são medidos o cloro e o pH da água usada na fábrica, além da temperatura de diferentes salas (armazenamento, envase etc.), porque essas condições afetam diretamente a qualidade do produto final e são exigidas por regulação sanitária.

Quando qualquer uma dessas medições sai da faixa esperada, o sistema precisa registrar automaticamente uma não conformidade, hoje isso é percebido manualmente e às vezes demora a ser identificado.


# Entidades principais

Recebimento de matéria-prima — o registro da chegada e da análise de um lote de leite em pó.
Lote de produção — uma Ordem de Produção e os testes de qualidade feitos nela.
Ponto de coleta — um local físico da fábrica onde se mede água ou temperatura (são 7 pontos fixos).
Medição — uma leitura específica feita em um ponto de coleta.
Lecitinização — o registro da adição de lecitina em um lote, quando aplicável.
Amostra de peso — uma pesagem individual feita para conferir se o produto embalado está no peso certo.
Não conformidade — qualquer ocorrência de uma medição fora da faixa esperada, seja no recebimento, no lote ou no ponto de coleta.
Especificação — a faixa aceitável de cada tipo de medição (por exemplo: "o peso pode variar até 5% do esperado").


# Os três agregados e as regras que eles protegem
# Recebimento de matéria-prima

Decide se um lote de matéria-prima pode ou não entrar em produção.

Umidade não pode passar de 5%.
Gordura tem que ser no mínimo 26%.
Acidez não pode passar de um limite máximo definido.
Partículas queimadas não podem passar de um nível aceitável.
O teste de antibiótico tem que dar negativo — se der positivo, o lote é reprovado automaticamente.
Um lote só pode ser aprovado se todos os testes obrigatórios tiverem sido feitos e estiverem dentro da faixa.


# Lote de produção

Cuida de cada Ordem de Produção.

Só pode usar matéria-prima que já foi aprovada no recebimento.
O peso real do produto embalado não pode variar mais que 5% do peso esperado.
Leite de vaca e leite de cabra nunca são processados no mesmo dia, para evitar contaminação cruzada entre os dois tipos de produto.
Um lote só pode ser liberado se passar em todos os testes acima; caso contrário, fica marcado como não conforme e não pode ser reaberto sem justificativa.


# Ponto de coleta

Cuida do monitoramento contínuo da fábrica.

Cloro da água tem que estar entre 0,5 e 5,0 mg/L.
pH da água tem que estar entre 6,0 e 9,5.
Cada sala da fábrica tem sua própria faixa de temperatura aceitável.
Essas medições precisam ser feitas antes de cada início de produção.
Se uma medição sair da faixa, isso precisa gerar uma não conformidade automaticamente.


# Casos de uso que o sistema precisa cobrir

Registrar a chegada de um lote de matéria-prima e seus resultados de análise
Decidir automaticamente se esse lote é aprovado ou reprovado
Registrar uma medição em um ponto de coleta (cloro, pH ou temperatura)
Verificar se essa medição está dentro da faixa aceitável
Fechar o registro do dia, conferindo que os 7 pontos de coleta foram medidos
Abrir um novo lote de produção, vinculado a uma matéria-prima já aprovada
Registrar a lecitinização de um lote, quando aplicável
Registrar as pesagens de amostra de um lote
Registrar os resultados de sensorial e molhabilidade de um lote
Liberar um lote de produção, se ele passar em todos os testes exigidos
Consultar o histórico completo de um lote — da matéria-prima usada até o resultado final
Gerar um relatório de não conformidades, filtrando por período, produto ou ponto de coleta
