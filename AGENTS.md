# AGENTS.md

## Caráter mandatório

- Todas as regras deste arquivo são obrigatórias e devem ser seguidas em conjunto.
- Nenhuma seção deste arquivo deve ser tratada como sugestão opcional.
- Em caso de conflito aparente, prevalecem a segurança, a proteção dos fluxos críticos, a privacidade dos usuários, a integridade dos créditos/pontos, a proteção contra abuso e as restrições explícitas de edição e colaboração.
- Se uma solicitação do usuário entrar em conflito com estas regras, o agente deve sinalizar o conflito, explicar o risco e propor uma alternativa segura.
- Se houver dúvida sobre como aplicar uma regra sem degradar segurança, desempenho, corretude ou manutenção, o agente deve parar e perguntar antes de prosseguir.

## Fluxo obrigatório de atuação

- Antes de qualquer alteração de código, configuração, dependências, infraestrutura, testes, dados ou documentação, o agente deve explicar objetivamente o que pretende alterar, por que isso será feito, quais riscos principais existem e aguardar confirmação do usuário.
- Antes de editar, o agente deve apresentar de forma explícita quais arquivos pretende alterar e descrever resumidamente o que será feito em cada arquivo.
- Sem confirmação explícita do usuário, o agente não deve editar arquivos, aplicar patches, executar comandos que gravem no repositório, alterar dependências, rodar migrações, semear dados, formatar arquivos em massa nem executar ações potencialmente destrutivas.
- Se o pedido estiver ambíguo, incompleto, tecnicamente arriscado ou com mais de uma interpretação razoável, o agente deve fazer perguntas curtas e relevantes antes de decidir.
- O agente deve assumir postura tecnicamente crítica e criteriosa, não apenas executar pedidos de forma automática.
- Toda decisão relevante deve priorizar segurança, desempenho, qualidade de código, previsibilidade e baixo risco de regressão.
- O agente deve preferir mudanças pequenas, testáveis, coesas e reversíveis logicamente.
- O agente não deve omitir riscos técnicos importantes para acelerar a entrega.

## Projeto

- Este projeto se chama **Postalia**.
- O Postalia é um SaaS para geração de posts para Instagram com apoio de IA.
- A aplicação permite que usuários criem marcas/perfis de empresa, definam identidade visual, nicho, público-alvo, tom de voz, produtos/serviços e plantillas base para gerar textos, legendas, hashtags, ideias de carrossel, prompts visuais e imagens.
- O projeto é composto por backend Django e frontend Vue.
- O projeto **não deve usar multitenancy com schemas separados**.
- A separação de dados deve ser feita por usuário e por marca, com checagem rigorosa de permissões em todas as APIs.
- Cada usuário pode possuir uma ou mais marcas conforme o plano contratado.
- O plano gratuito permite apenas uma marca.
- Planos pagos podem permitir mais marcas conforme suas regras.
- O ambiente de execução padrão é via containers.
- Não assumir Python, Node, npm, pnpm ou outras dependências instaladas no host.
- Sempre preferir comandos executados via `docker compose exec ...` ou `docker compose run ...`.

## Arquitetura relevante

- Backend principal em `backend/` com Django, Django REST Framework, SimpleJWT, PostgreSQL, Celery, Redis e drf-spectacular.
- Frontend principal em `frontend/` com Vue 3, TypeScript, Vite, Vue Router, i18n e biblioteca visual definida pelo projeto.
- O backend deve manter separação clara entre autenticação, marcas, geração de conteúdo, planos, pontos, referrals, anúncios recompensados, exports e segurança.
- Apps esperadas ou equivalentes no backend:
  - `accounts`: autenticação, usuários, Google OAuth, sessão, JWT e usuário administrador inicial.
  - `brands`: marcas, perfis de empresa e plantillas base.
  - `subscriptions`: planos, limites mensais e estado da assinatura.
  - `credits`: carteira de pontos, transações e consumo de créditos.
  - `generations`: geração de textos, carrosséis, prompts e imagens.
  - `ai_providers`: abstração para provedores fake/real de IA.
  - `referrals`: indicações e recompensas.
  - `ads`: eventos de anúncios recompensados.
  - `risk`: eventos de risco, device sessions e regras antiabuso.
  - `exports`: exportação de posts, marca d’água e arquivos gerados.
- O frontend deve manter fluxos simples, organizados e multilíngues:
  - landing page
  - pricing
  - login/registro
  - dashboard
  - wizard de marca
  - plantillas
  - geração de posts
  - histórico
  - carteira/pontos
  - indicações
  - assinatura
  - configurações

## Fluxos críticos do sistema

- Autenticação com JWT, refresh token e suporte a Google OAuth.
- Criação automática do usuário administrador inicial a partir de variáveis de ambiente.
- Controle de permissões por usuário em todas as entidades.
- Controle de marcas por plano.
- Controle de limites mensais por plano.
- Controle de pontos e transações.
- Geração de conteúdo com gasto correto de créditos/pontos.
- Modo de IA fake/real controlado explicitamente por variável de ambiente.
- Anúncios recompensados e callbacks futuros sem dupla contabilização.
- Sistema de referrals sem autoindicação, fraude simples ou crédito duplicado.
- Exportação de posts com marca d’água obrigatória no plano gratuito.
- Conteúdo gerado deve respeitar moderação mínima e regras de segurança.
- Billing real pode ser preparado, mas no MVP pode ser controlado manualmente pelo admin.

## Planos e pontos

- Os planos oficiais do MVP são: `free`, `starter`, `pro` e `agency`.
- Plano Free:
  - página com anúncios
  - 10 pontos no cadastro
  - 3 textos/mês grátis ou texto por 5 pontos após a quota
  - imagem custa 30 pontos
  - anúncio completo gera 5 pontos
  - máximo 2 anúncios recompensados por dia
  - login diário gera 1 ponto
  - streak de 7 dias gera +5 pontos
  - indicação free válida gera 15 pontos
  - indicação paga gera 100 pontos
  - exportação com marca d’água
  - limite de 1 marca
- Plano Starter:
  - €5/mês
  - 50 textos/mês
  - 10 imagens/mês
  - sem marca d’água
  - pode farmar pontos
  - limite de 1 marca
- Plano Pro:
  - €12/mês
  - 200 textos/mês
  - 40 imagens/mês
  - calendário editorial
  - identidade visual salva
  - pode farmar pontos
  - limite de até 3 marcas
- Plano Agency:
  - €29/mês
  - 800 textos/mês
  - 150 imagens/mês
  - múltiplas marcas
  - geração em lote
  - pode farmar pontos
- Créditos incluídos no plano e pontos bônus devem ser tratados de forma clara e auditável.
- Toda alteração de pontos deve gerar uma transação.
- Nunca atualizar saldo de pontos diretamente sem registrar `CreditTransaction` ou equivalente.
- Não permitir saldo negativo.
- Gastos de pontos devem usar transação atômica no banco de dados.

## Modo de IA

- O uso de IA deve ser controlado explicitamente por variável de ambiente.
- A variável obrigatória é `AI_PROVIDER_MODE`.
- Valores permitidos:
  - `fake`
  - `real`
- Se `AI_PROVIDER_MODE=fake`:
  - usar provedores locais determinísticos
  - não chamar APIs externas
  - não exigir chaves externas
  - retornar respostas realistas de demonstração
  - permitir testes e desenvolvimento sem custo
- Se `AI_PROVIDER_MODE=real`:
  - usar provedores configurados por env
  - exigir chaves necessárias
  - falhar de forma clara se configurações obrigatórias estiverem ausentes
  - não expor segredos em logs ou respostas de erro
- Em produção, com `DJANGO_DEBUG=false`, o modo fake só pode ser permitido se `ENABLE_FAKE_AI_IN_PRODUCTION=true`.
- O sistema não deve decidir automaticamente entre fake e real apenas pela ausência de chaves.
- O modo deve ser explícito.

## Segurança

- Evitar introduzir ou ampliar enumeração de usuários, vazamento de informação sensível, bypass de permissão, exposição indevida de detalhes internos ou redução de proteções existentes.
- Não aceitar nem executar mudanças que piorem claramente a segurança sem deixar isso explícito.
- Em autenticação, preferir respostas públicas seguras e consistentes, diferenciando apenas o que for estritamente necessário para a UX.
- Ter cuidado especial com JWT, refresh token, cookies, CORS, CSRF, OAuth, rate limiting, upload de arquivos, geração de conteúdo, pontos e billing.
- Não hardcodear segredos, tokens, chaves de API, usuários, senhas ou credenciais.
- Todas as configurações sensíveis devem vir de variáveis de ambiente.
- O arquivo `.env.example` deve conter todos os nomes de variáveis necessários sem valores sensíveis reais.
- O usuário administrador inicial deve ser criado somente com credenciais vindas de env vars.
- Não expor stack traces, segredos, tokens, prompts internos completos ou respostas internas de provedores em APIs públicas.
- Validar rigorosamente permissões: um usuário nunca pode acessar marcas, templates, gerações, exports, carteira, transações, referrals ou assinatura de outro usuário.
- Toda geração de conteúdo deve verificar limites, plano, saldo e permissões no backend.
- Nunca confiar apenas no frontend para controle de plano, pontos ou limites.
- Aplicar rate limiting em login, registro, geração, referrals, anúncios recompensados e endpoints sensíveis.
- Usar CAPTCHA ou mecanismo equivalente em fluxos suspeitos ou de alto risco quando implementado.
- Eventos de anúncios recompensados devem ter proteção contra dupla contabilização.
- Referrals devem impedir autoindicação e abuso por múltiplas contas.
- Device/IP/cookie/localStorage podem ser usados como sinais de risco, mas não devem bloquear clientes legítimos de forma rígida sem critério.
- Uploads de logo ou imagens devem validar tipo, tamanho, extensão e conteúdo quando possível.
- Conteúdo gerado deve passar por camada mínima de moderação para evitar abuso, golpes, conteúdo adulto explícito, ódio, violência, ilegalidades e prompts maliciosos.

## Privacidade e dados

- Coletar apenas os dados necessários para o funcionamento do produto.
- Tratar dados de marca, prompts, gerações e histórico como dados privados do usuário.
- Não usar conteúdo de um usuário para outro.
- Não expor exemplos reais de prompts ou gerações em logs públicos.
- Logs devem ser úteis para auditoria, mas não devem vazar dados sensíveis.
- Considerar requisitos de GDPR, especialmente para usuários na União Europeia.
- Permitir estrutura futura para exclusão/exportação de dados do usuário.

## Qualidade de implementação

- Sempre sugerir a melhor implementação viável, não apenas a mais rápida.
- Antes de editar, entender o contexto do código e o comportamento atual.
- Ao mexer em fluxos sensíveis, preferir mudanças pequenas e testáveis.
- Preservar compatibilidade com o que já está funcionando.
- Evitar duplicação, acoplamento desnecessário e lógica espalhada.
- Quando houver heurística frágil, preferir contratos explícitos entre backend e frontend.
- Em frontend, manter coerência com i18n e evitar mensagens cruas vindas da API quando houver alternativa melhor.
- Qualquer alteração de texto de UI deve ser traduzida em todos os idiomas disponíveis.
- Idiomas mínimos esperados:
  - `en`
  - `es`
  - `pt`
- Se novos idiomas forem adicionados, qualquer mudança futura de UI deve atualizar todos os locales disponíveis.
- Em backend, preferir respostas estáveis, testáveis e semanticamente claras.
- Separar responsabilidades:
  - regras de plano em serviços próprios
  - pontos em serviço próprio
  - provedores de IA em abstrações próprias
  - regras antiabuso em módulo próprio
  - serializers/views sem lógica de negócio excessiva
- Seguir princípios SOLID quando fizer sentido prático.
- Favorecer clean code: nomes claros, fluxo legível, responsabilidades bem separadas e baixa complexidade acidental.

## Postura técnica

- Não concordar automaticamente com o usuário quando a solicitação piorar segurança, arquitetura, legibilidade, consistência ou manutenção.
- Se houver uma alternativa tecnicamente melhor, explicar de forma objetiva e propor a melhor implementação.
- Discordar do usuário quando necessário para proteger o projeto de decisões ruins, mas de forma direta e respeitosa.
- Manter postura crítica no sentido técnico, sem ser agressivo, arrogante ou desnecessariamente confrontacional.
- Não implementar soluções frágeis apenas para satisfazer rapidamente o pedido sem antes considerar impacto técnico.
- Na dúvida antes de tomar decisões relevantes, fazer perguntas curtas e objetivas que aumentem a qualidade da implementação.
- Não reduzir o nível de exigência técnica apenas para agradar o usuário ou acelerar uma entrega.

## Execução

- Todos os testes, validações e comandos relevantes devem ser executados nos containers.
- Ao validar backend, preferir `docker compose exec backend ...`.
- Ao validar frontend, preferir `docker compose exec frontend ...`.
- Se for necessário descobrir caminhos ou contexto no container, verificar primeiro com comandos de leitura.
- O backend deve rodar no container em `/app` ou caminho equivalente definido no Dockerfile.
- Comandos úteis esperados:
  - Subir ambiente: `docker compose up --build`
  - Backend tests: `docker compose exec backend python -m pytest`
  - Frontend tests: `docker compose exec frontend npm run test:run`
  - Migrações: `docker compose exec backend python manage.py migrate`
  - Criar admin inicial: automático via entrypoint/command seguro
  - Swagger/OpenAPI: endpoint documentado no README
- Não assumir que o ambiente local fora do Docker possui as dependências necessárias.

## Testes e verificação

- Toda mudança relevante deve ser validada com testes ou verificações objetivas.
- Se houver testes existentes para a área alterada, executá-los no container correspondente.
- Ao alterar autenticação, autorização, permissões, planos, pontos, IA, referrals, anúncios, exports ou billing, adicionar ou ajustar testes.
- Ao alterar textos de UI, i18n, rotas, guards, interceptors ou fluxo de geração, validar o frontend.
- Preferir validar a menor superfície relevante primeiro e depois ampliar se o risco justificar.
- Não declarar que algo está correto sem verificar quando houver uma forma razoável de validação.
- Ao finalizar, informar de forma clara o que foi testado e o que não foi.
- Testes mínimos esperados:
  - autenticação
  - permissões por usuário
  - criação de marca
  - limite de marcas por plano
  - limites mensais de texto/imagem
  - gasto de pontos
  - integridade da carteira
  - bloqueio de saldo negativo
  - anúncios recompensados com limite diário
  - prevenção de dupla contabilização de anúncio
  - referrals válidos e inválidos
  - modo fake de IA
  - modo real de IA sem chave configurada
  - exportação com marca d’água no plano free
  - acesso negado a dados de outro usuário

## Edição e colaboração

- Antes de qualquer alteração de código ou configuração, explicar claramente o que será alterado, por que a mudança é necessária e aguardar confirmação do usuário.
- Antes de editar, listar os arquivos que serão afetados e explicar objetivamente a finalidade de cada alteração em cada arquivo.
- Se houver ambiguidade, falta de contexto ou mais de uma direção razoável, fazer perguntas relevantes antes de editar.
- Sem confirmação do usuário, limitar-se a análise, leitura, levantamento de contexto e proposta técnica.
- Não reverter alterações do usuário sem pedido explícito.
- Nunca executar comandos de gravação no Git, incluindo:
  - `git add`
  - `git commit`
  - `git merge`
  - `git rebase`
  - `git cherry-pick`
  - `git stash`
  - `git tag`
  - `git push`
  - equivalentes que alterem o estado do repositório
- Não usar comandos destrutivos como `rm -rf`, `git reset --hard` ou similares sem autorização explícita.
- Em worktree suja, trabalhar ao redor das mudanças existentes com cuidado.
- Fazer alterações cirúrgicas e minimizar o diff quando possível.
- Manter consistência com o estilo e os padrões já adotados no repositório, salvo quando houver motivo técnico forte para melhorar.
- Ao identificar instruções do usuário que conflitem com segurança, desempenho, qualidade ou manutenção, interromper a execução e explicar a objeção técnica antes de continuar.

## Regras específicas do Postalia

- Não implementar multitenancy com schemas separados.
- O isolamento principal deve ser por usuário, marca e permissões no backend.
- Não bloquear globalmente nomes de empresas/marcas repetidos.
- Bloquear apenas duplicidade de marca dentro do mesmo usuário quando fizer sentido.
- Nome da marca, logo ou identificador visual deve aparecer nos exports.
- Plano Free deve incluir marca d’água visível: `Created with Postalia` ou texto equivalente traduzido.
- Plano pago não deve exibir marca d’água da plataforma, mas deve manter identificação da marca do usuário quando exigido pelo template.
- O controle de pontos deve ser transacional e auditável.
- O backend deve ser a fonte única da verdade para planos, limites, pontos e permissões.
- O frontend pode exibir limites e custos, mas nunca deve ser responsável pela validação final.
- Modo fake de IA deve funcionar para desenvolvimento e demonstração sem custo.
- Modo real de IA deve depender exclusivamente de env vars.
- Não expor chaves de IA no frontend.
- Chamadas a provedores de IA devem ocorrer no backend.
- Anúncios recompensados devem ter simulação apenas em desenvolvimento.
- Endpoint de simulação de anúncio deve ser desabilitado em produção.
- Referências futuras a pagamentos devem ser isoladas em serviços, para permitir integração posterior com Stripe, Paddle, Creem ou outro provedor.
- Billing real não deve ser acoplado diretamente à lógica de geração.
- Mudanças em planos, pontos, geração, referrals e anúncios devem ser tratadas como áreas sensíveis.

## Prioridades

- Priorizar segurança, clareza, manutenção e previsibilidade.
- Considerar que o código será auditado e, por isso, manter rigor alto em segurança desde a análise até a entrega.
- Priorizar segurança, desempenho e qualidade de código acima de conveniências de implementação.
- Priorizar implementações simples, coesas e com baixo risco de regressão.
- Evitar efeitos colaterais em fluxos que já funcionam.
- Ter atenção especial a regressão em:
  - autenticação
  - permissões
  - pontos
  - planos
  - geração de IA
  - exports
  - referrals
  - anúncios recompensados
  - i18n
  - uploads
  - billing futuro

## Resultado esperado

- Entregar soluções seguras, legíveis, testadas e com baixo risco.
- Preservar o comportamento correto do sistema existente.
- Melhorar o código sem sacrificar segurança, boas práticas ou manutenção futura.
- Fazer com que o agente atue de forma disciplinada, previsível e aderente a todas as regras deste arquivo.