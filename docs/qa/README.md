# QA Learning Loop

Este diretório documenta o QA (Perguntas e Respostas), das decisões, construções, validações, correções, aprendizado e vocabulário técnico usado no projeto e em decisões de arquitetura.

## Objetivo

Garantir que cada alteração no código seja compreendida conceitualmente e tecnicamente,
evitando dependência cega de IA.

## Processo

Para cada commit relevante:

1. Gerar perguntas com IA (foco em entendimento, não memorização)
2. Responder sem consultar código inicialmente
3. Revisar respostas com apoio da IA
4. Identificar gaps de conhecimento
5. Registrar aprendizados

## Princípios

- Não copiar respostas
- Explicar com suas próprias palavras
- Priorizar "porquê" ao invés de "o quê"
- Buscar clareza, não perfeição

## Como escrever corretamente

Use uma escrita técnica direta, com foco em clareza, precisão e progressão lógica. A resposta deve primeiro apresentar a ideia principal, depois explicar o motivo e, por fim, conectar com um exemplo do código quando necessário.

- **Comece pela conclusão**: declare a resposta principal logo no início. Evite começar com muitas condicionais ou contexto excessivo.
- **Use frases curtas**: cada frase deve comunicar uma ideia central. Se uma frase tiver muitas vírgulas, provavelmente deve ser dividida.
- **Evite repetição de estruturas**: reduza o uso repetido de expressões como "através de", "podemos", "por isso", "isso faz com que" e "no caso de".
- **Prefira verbos assertivos**: use "define", "valida", "reduz", "aumenta", "garante", "expõe" e "depende" em vez de construções vagas como "serve para fazer" ou "acaba fazendo".
- **Use termos técnicos consistentes**: mantenha termos comuns em inglês quando forem padrão na área, como `test case`, `contract test`, `Protocol`, `interface`, `implementation`, `coupling` e `refactor`.
- **Explique um conceito por vez**: não misture definição, exemplo, justificativa e exceção na mesma frase.
- **Diferencie causa e consequência**: deixe claro o que causa o problema e qual efeito isso gera no projeto.
- **Evite tom inseguro sem necessidade**: substitua "pode ser que nós estamos incorrendo" por "isso pode indicar" ou "isso sugere".
- **Use exemplos do código com função clara**: cite um teste, classe ou módulo apenas quando ele reforçar a explicação.
- **Revise gramática e digitação**: erros como "objetvios", "intefaces" ou "balisadores" reduzem a autoridade da resposta, mesmo quando o raciocínio está correto.

Estrutura recomendada para respostas:

1. Afirmação principal.
2. Justificativa técnica.
3. Exemplo concreto do projeto.
4. Risco ou consequência, quando aplicável.

## Tipos de Perguntas

- Conceituais (por que isso foi feito?)
- Arquiteturais (onde isso se encaixa?)
- Técnicas (como funciona internamente?)
- Alternativas (existiam outras soluções?)
- Trade-offs (vantagens/desvantagens)
