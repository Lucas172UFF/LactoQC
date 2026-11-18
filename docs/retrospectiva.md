# Retrospectiva da arquitetura do LactoQC

Esta retrospectiva reúne o que o grupo aprendeu ao desenvolver o LactoQC nos três checkpoints. Mais do que listar tecnologias e padrões, buscamos avaliar como as ideias estudadas ajudaram a organizar o sistema, quais custos trouxeram e o que podemos levar para projetos futuros.

## Checkpoint 1 — arquitetura e separação de responsabilidades

No primeiro checkpoint, estruturamos o sistema em camadas e usamos ideias de Ports & Adapters para separar as regras de negócio de detalhes como HTTP e persistência. Essa organização ajudou a manter o domínio independente de Flask e SQLAlchemy e permitiu testar suas regras sem precisar iniciar a aplicação inteira ou acessar um banco de dados.

Ao longo do trabalho, percebemos que essa separação facilita localizar responsabilidades e mudar uma parte do sistema sem necessariamente reescrever as demais. Também entendemos seu custo: um caso de uso pode atravessar domínio, serviços, adaptadores e rotas, exigindo mais arquivos e testes. Portanto, dividir o sistema em camadas não elimina a complexidade; ajuda a organizá-la e a controlar onde ela aparece.

Essa experiência reforçou uma ideia importante da arquitetura de software: as fronteiras devem proteger as regras centrais e tornar as dependências mais claras. Ao mesmo tempo, abstrações precisam corresponder a necessidades reais. Se forem criadas sem um motivo concreto, podem aumentar a quantidade de código e dificultar o entendimento.

## Checkpoint 2 — SOLID aplicado ao sistema

As mudanças inspiradas em SOLID ajudaram a examinar responsabilidades e pontos de extensão em partes diferentes do projeto. A separação da inicialização da persistência, por exemplo, tornou mais clara a diferença entre configurar o banco e criar a aplicação. No recebimento de matéria-prima, representar explicitamente as etapas do ciclo de vida ajudou a organizar comportamentos que antes dependeriam de verificações condicionais.

O principal aprendizado foi que SOLID não é uma lista de regras para aplicar mecanicamente. Seus princípios servem como perguntas para avaliar o desenho: uma classe está acumulando responsabilidades? Uma nova regra exige alterar muitos lugares? As dependências estão apontando para a lógica de negócio ou para detalhes técnicos?

Quando essas perguntas identificam um problema concreto, uma refatoração pode tornar a mudança futura mais localizada. Mas cada abstração também tem um custo: novas classes e interfaces exigem nomes, testes e entendimento. O valor aparece quando esse custo reduz o impacto de mudanças que o sistema realmente pode precisar.

## Checkpoint 3 — padrões GoF

Os padrões GoF ajudaram a dar forma a problemas recorrentes do projeto. O **Observer** separou a ocorrência de uma não conformidade da comunicação com quem precisa reagir a ela. Isso reduz o conhecimento que o componente de origem precisa ter sobre seus destinatários e facilita acrescentar reações sem concentrar tudo no mesmo ponto.

O **Strategy** permitiu variar regras de qualidade sem transformar uma única implementação em uma sequência crescente de condicionais. Assim, cada estratégia pode representar uma política específica, e os testes podem verificar essas políticas separadamente. Esse padrão se relaciona com a ideia de deixar pontos de variação explícitos, embora adicionar uma estratégia também exija decidir como ela será escolhida e configurada.

O **State** representou as etapas do recebimento e as transições permitidas entre elas. Em vez de espalhar verificações sobre a situação atual por vários métodos, o comportamento fica associado ao estado correspondente. Isso torna o ciclo de vida mais compreensível, especialmente quando há operações válidas em uma etapa e inválidas em outra. O custo é manter as classes de estado e as regras de transição sincronizadas com as necessidades do negócio.

A **Abstract Factory** organizou a criação de famílias compatíveis de repositórios, como as implementações SQLAlchemy e em memória. Com isso, quem configura a aplicação pode escolher uma família sem precisar conhecer todos os detalhes de criação de cada repositório. O padrão é útil quando há mais de uma família que precisa ser trocada de forma coordenada; se houver apenas uma implementação estável, essa camada de indireção pode não compensar.

Em conjunto, esses exemplos mostram que padrões não são soluções universais nem objetivos por si só. Eles oferecem vocabulário e estruturas conhecidas para problemas de comunicação, variação, ciclo de vida e criação de objetos. Aprendemos que a escolha deve partir do problema observado, e não da vontade de incluir um padrão no sistema.

## Frameworks e limites das abstrações

Flask, SQLAlchemy e pytest cumprem papéis diferentes: Flask participa da interface HTTP e da composição da aplicação; SQLAlchemy apoia a persistência; e pytest organiza a execução dos testes. Manter o domínio separado de Flask e SQLAlchemy protege as regras de negócio contra detalhes dessas ferramentas.

A separação, porém, não é absoluta. A camada de serviço ainda conhece o tipo `Session` do SQLAlchemy. Isso não invalida a arquitetura atual, mas revela um ponto de acoplamento que pode merecer atenção se o sistema precisar trocar ou generalizar sua fronteira transacional. Também aprendemos que o uso de uma abstração não basta para remover dependências: é preciso observar concretamente quais módulos importam e conhecem cada tecnologia.

## O que levamos do trabalho

O trabalho mostrou que arquitetura, princípios e padrões ajudam a discutir decisões de projeto com mais precisão. Em vez de perguntar apenas “qual tecnologia usar?”, passamos a perguntar onde uma regra deve ficar, quem deve conhecer uma dependência, como uma variação será isolada e qual é o custo de introduzir uma nova camada.

Também vimos a importância de equilibrar qualidade estrutural com simplicidade. Camadas, princípios e padrões tornam mudanças mais organizadas quando correspondem às necessidades do sistema. Aplicá-los sem considerar o contexto pode produzir complexidade adicional. Em projetos futuros, procuraríamos identificar primeiro a responsabilidade ou a variação que causa dificuldade e escolheríamos uma estrutura que a torne mais fácil de entender e testar.

## O papel da IA no desenvolvimento

A IA pode ajudar no trabalho de engenharia ao explicar conceitos, comparar alternativas, sugerir estruturas, produzir rascunhos de código e testes e apoiar a análise de documentação. No contexto deste projeto, esse apoio pode acelerar a exploração de opções como State ou Strategy e ajudar a transformar uma ideia em uma proposta que o grupo possa avaliar.

Esse auxílio não substitui a compreensão do sistema nem a revisão das pessoas responsáveis. Uma sugestão pode não corresponder às regras reais do domínio, introduzir abstrações desnecessárias ou deixar casos importantes sem cobertura. Por isso, o uso mais útil da IA é como apoio à análise e à produção inicial: a equipe precisa confrontar as sugestões com o código, os requisitos, os testes e os trade-offs do projeto, e responder pelo resultado entregue.

## Recomendação para o LactoQC

Com base no que observamos, recomendamos manter a arquitetura em camadas com Ports & Adapters e evoluí-la de forma seletiva. Ela preservou o isolamento do domínio e ofereceu pontos claros para testes e mudanças. Não identificamos, no trabalho realizado, uma necessidade que justificasse substituir toda essa estrutura por outra arquitetura ou por um framework full-stack.

Como próximos pontos de atenção, consideraríamos reduzir o conhecimento do tipo `Session` na camada de serviço caso a aplicação precise de uma fronteira transacional mais independente, preservar testes de integração para os mapeamentos do ORM e avaliar o custo de carregar agregados completos nas consultas. A decisão é continuar usando os princípios e padrões como ferramentas para resolver problemas concretos, revisando seus benefícios e custos à medida que o sistema evolui.

## Reflexão — João Gabriel Pimentel

Revisito aqui as previsões que fiz no Checkpoint 1 (`docs/arquitetura.md`) para o
agregado que acompanho, `CollectionPoint`, e o que a Fase 2 confirmou ou não.

**O que se confirmou.** CQ-01 (domínio testável sem banco) previu suíte unitária
em menos de 1s; mediram-se 0,14s para 113 testes no Checkpoint 1, e a suíte
continuou sem precisar de banco depois dos dois padrões que apliquei na Fase 2:
a correção de OCP (`6ad1830`) e o Observer (`232d03a`) levaram `tests/unit` de
173 para 174 e depois para 180 testes, sem nenhuma fixture de banco nova. CQ-04
(custo de um caso de uso em até 4 arquivos por camada) também se confirmou em
escala menor: o OCP tocou só `domain/model.py`; o Observer tocou três arquivos
(`domain/model.py`, `service_layer/notifications.py`,
`entrypoints/collection_point_routes.py`), nunca `adapters/` — nenhum dos dois
padrões mudava como o dado é persistido.

**O que não se confirmou como esperado.** O risco R-01 que registrei em
`docs/arquitetura.md` §4.4 (mapeamento global de classes; um erro em um
agregado derruba os outros) deixou de ser hipotético: chegou a derrubar 18
testes do Lote de Produção por um mapeamento duplicado em `orm.py`, pela mesma
razão que eu já havia previsto — só que mais cedo e mais concretamente do que
o documento antecipava.

**O que a Fase 2 mostrou sobre as camadas.** Nos dois padrões que apliquei, a
arquitetura em camadas não precisou ser contornada nem estendida para caber a
mudança — ela já tinha o lugar certo para cada peça: a política de tipos
obrigatórios (OCP) é regra de negócio, então ficou inteira em `domain/`; a
notificação (Observer) é efeito colateral de infraestrutura, então o
`ConcreteObserver` de log ficou no service layer e a composição de quais
observadores usar ficou na rota, que já era a camada que compunha dependências
de infraestrutura (o repositório). É evidência a favor de manter o estilo: um
padrão de projeto novo não exigiu reorganizar camada nenhuma no meu agregado.

**Decisão.** Pela minha parte, mantenho a recomendação deste documento:
continuar em camadas com Ports & Adapters, com os três ajustes que registrei em
`docs/arquitetura.md` §5.2 — Unit of Work explícito no lugar de `Session` solta
no service layer, uma porta de consulta separada do repositório de escrita, e
um único `start_mappers()` idempotente (que o risco R-01 confirmado deixou
ainda mais urgente).
