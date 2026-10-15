# CAMPEÕES MECHA — progresso

## Novo escopo aprovado — PvP online real e conclusão das pendências
- Aprovado: fila pública + salas privadas por código; equipe de até quatro robôs; turnos de 60 segundos; reconexão; ações/tempo/resultado validados no servidor, nunca adversários IA disfarçados de players.
- Competitivo normalizado: todos os 256 robôs disponíveis; nível padronizado; sem equipamentos/pets/cards ou bônus oriundos de saves offline editáveis. Saves offline preservados e separados do competitivo.
- Remover AUTO em TODAS as batalhas, inclusive no motor/API; IA continua exclusivamente como adversário dos modos offline.
- Login só para PvP: Google gerenciado + e-mail/senha, tela única com abas, retorno ao lobby depois de autenticar. Jogar offline não exige conta.
- Implementação prevista em packages/web: auth/middleware e tabelas Drizzle de contas/salas/fila/partidas/ações/resultados; procedimentos oRPC para lobby/equipe/salas/fila/estado/ações/desistência; consultas tipadas e novas telas de acesso/lobby/batalha online. Servidor reutiliza regras compartilhadas sem executar decisões de IA no PvP. Atomicidade e idempotência obrigatórias.
- Pendências offline mantidas: auditoria completa de status/passivas/talentos, balanceamento, objetivos obrigatórios do tutorial, sequências exclusivas IA restantes. Sem locução, conforme confirmação; abertura/tutorial continuam sem voz. Sem E2E/Playwright/gameplay em navegador.
- BLOQUEIO constatado antes da implementação online: não existe .env no projeto e não há DATABASE_URL/DATABASE_AUTH_TOKEN/APPLICATION_ID/issuer no ambiente. Backend atual tem só ping e nenhuma autenticação. Credenciais reais de banco necessárias, sem placeholders. Não declarar PvP conectado ou concluído.

## Checkpoint atual — terreno, clima e absorção elemental
- [x] Climas filtram golpes de área/contundentes e elementos corretamente; ar rarefeito afeta todo dano, eclipse penaliza LUZ/beneficia SOMBRA, branco absoluto reduz crítico. Arenas derivadas herdam as regras.
- [x] Zonas de cura/MP/perigo aplicam efeitos por round; terrainMaster duplica benefícios reais e hazardWalker evita apenas dano de zona/converte em 6 MP. Vácuo bloqueia cura de terreno, não reparos; zonas void ampliam dano recebido sem bloquear cura. Sem ataques automáticos novos da reserva.
- [x] Buff de força da zona deixa de ser contado novamente no poder do golpe. marked/maldição/vulnerabilidade ampliam dano em vez de reduzi-lo. Clima/status drain retiram porcentagem do MP máximo; healIn modifica cura recebida, não produz cura espontânea.
- [x] Afinidade zero cura o alvo e não produz dano mínimo/status hostil/carga por dano recebido. Projeção de dano usa strike em cópias isoladas, incluindo multihit each, barreira/escudo/parry/passivas/clima; projeções probabilísticas são sinalizadas e não garantem todos os resultados de RNG.
- [x] IDs de golpe inválidos não viram ataque básico nem consomem turno pronto. Troca forçada só aceita fase forced_swap e índice inteiro vivo.
- [x] Tutorial orienta pelos painéis atuais de ataques/defesas/ultimate/SUPRIMENTOS, sem esferas obsoletas. Objetivos pedagógicos obrigatórios ainda NÃO implementados.
- [x] Dez suites passaram, TypeScript/build e validação de arte/HTTP passaram. Simulações das cinco missões: vitória em 3/4/8/6/4 rounds. Saves legado/vazio preservados. Sem E2E, Playwright ou gameplay em navegador; avisos conhecidos de Bun/Node/chunk permanecem.
- [ ] Ainda pendentes: auditoria exaustiva de status/talentos/passivas (incluindo thornMine e outras condições de terreno), balanceamento completo, objetivos pedagógicos obrigatórios, demais sequências exclusivas e plano de locução aprovado. Não declarar refinamento completo.

## Checkpoint atual — passivas, segurança e interface anime mecha
- [x] Holograma/orbs removidos da batalha; quatro ataques e duas defesas sempre renderizados com nomes/custos, informação separada, ultimate em painel próprio, retratos/HUD maiores, deck inferior responsivo e molduras pixel existentes. Estrutura verificada por renderização React no servidor; não verificada visualmente em navegador, conforme restrição.
- [x] Hooks de início/fim de turno, erro, dano recebido, crítico e pós-ataque conectados; reações diretas não acionam recursivamente outras reações. Reserva não produz dano de passiva de abertura de round. Bônus escopados limitados, reiniciados por round.
- [x] Núcleos fênix/imortal e segundo fôlego com consumo único; reviver antes de conceder abate. Primeiro abate do portador cura uma vez; onFaint duplicado removido. Predador usa HP do alvo, guarda completa anula golpe e prisma reflete em vez de aumentar dano recebido.
- [x] onAllyFaint/cura coletiva, onMpSpend, onPurge e onStatusApply conectados; statusWeaver/pyromaniac ajustam duração/potência, purgeAura remove um negativo e battleRhythm responde à alternância ataque/defesa.
- [x] Mineração rejeita NaN/Infinity/minérios desconhecidos/profundidades inválidas/tempo regressivo; quantidades discretas. Refinaria/venda têm consumo único. Sockets inteiros e proprietário obrigatório; laboratório valida peças/núcleo/hue antes de gastar e desmontagem conserva equipe válida.
- [x] Callbacks finais de ranked/torneios protegidos contra repetição local; ranked conta sobreviventes só da equipe real, não entradas auxiliares do snapshot.
- [x] Nove suites passaram (seis anteriores + passive-lifecycle, economy-safety e battle-command-layout). Tutorial simulado 3/4/8/6/4 rounds, legado e vazio preservados. TypeScript/build passaram; avisos conhecidos de chunk >500kB e Node permanecem.
- [x] HTTP 200 da prévia; 26 assets de entrada/especiais e 15 referências de imagem da interface com MIME/hash corretos. Sem E2E, Playwright ou gameplay em navegador.
- [ ] Ainda pendentes: paridade exaustiva de todas as descrições/passivas/terreno/talentos, equilíbrio, objetivos pedagógicos obrigatórios do tutorial, demais sequências exclusivas dos robôs atuais e aprovação de plano de locução. Este checkpoint NÃO conclui todos os itens restantes.

## Escopo atual e checkpoint verificado
- Expansão de novos robôs CANCELADA pelo usuário. Manter 256 recrutáveis + oito NPCs, sem produzir/cadastrar mc_257…mc_500. Manifestos antigos ficam como histórico, não trabalho ativo.
- Nenhum E2E, Playwright ou gameplay no navegador. Não executar scripts de reconstrução antigos.
- [x] Remulu Games: logo IA sobre preto com fade, pular, timeout/fallback e sem voz.
- [x] Novo carregamento: 50 frames, três fundos, progresso real de imagens, falhas explícitas e tentativa novamente; peças modulares também reportam falhas e permitem nova tentativa.
- [x] Ultimate dentro da arena: ator/alvo reais, HUD preservado; dez pares exclusivos recortados, demais usam sprite e VFX existentes. Timeout de arte evita bloqueio. Não declarar todas as sequências exclusivas concluídas.
- [x] Compras e treino com saldo atual; equipe única de até quatro, equipe não vazia quando há robôs; briefing de todos os sistemas e rota por nível.
- [x] Golpes carregados pagam MP/recurso uma vez, respeitam multihit, não duplicam carga e limpam preparação na queda. UI distingue preparo/liberação e bloqueia golpes silenciados/impagáveis.
- [x] Cura coletiva de teamPlayer e disparo onUltReady de ultimateBattery; descrições atualizadas. COBRIR explícito protege aliado, sem ataques automáticos da reserva.
- [x] Dimensões: draft exige exatamente quatro únicos; campanha válida; carry HP/MP finito em 0–1 e núcleo em 0–100; fases e recompensas idempotentes testadas.
- [x] Usina/capacitor, expedição/pesquisa, cargas da academia/talentos, ressonância do museu, resgates encadeados/marcos dos contratos testados. Inputs inválidos da expedição e história não alteram save.
- [x] Equipamentos/skins exigem robô e skin possuídos; venda repetida não duplica ouro. Tutorial não paga antes de iniciar.
- [x] Seis suites estáticas passaram: combat-refinement, city-refinement, polish, overhaul, legacy, empty. Cinco missões simuladas vencidas em 3/3/7/6/4 rounds; saves legado e vazio preservados nos testes.
- [x] TypeScript e build passaram (204 módulos). Avisos: chunk >500 kB e depreciação Node; sem erro de build.
- [x] Validação pós-build: 26 imagens HTTP 200 com MIME de imagem e hash idêntico ao arquivo, 50 células de loader distintas e 20 strips transparentes com dez células distintas. Preview HTTP 200.
- [ ] Refinamento profundo restante: auditar todas as passivas/hooks/status/talentos, mineração/cards/pets/laboratório/ranked/torneios e equilíbrio completo. Briefing não substitui mecânica auditada.
- [ ] Sequências IA exclusivas de ultimate/VFX dos demais robôs atuais. Nenhuma nova identidade pendente.
- [ ] Locução do tutorial somente após aprovação de plano de voz/custo/duração. Abertura permanece sem voz.

## Overhaul MECHA CHAMPIONS — aprovado, em execução (2026-10-07)
- Decisões e curva de carga/desbloqueios registradas em design.md. Todos os lotes IA autorizados diretamente; não executar E2E/Playwright.
- [x] Motor: remover combo coletivo, ultimate individual sem MP, carga por ação/dano, IA e loadout 4+2 (regras testadas; auditoria total pendente).
- [x] Arte de interface: esfera, dois hologramas 25 frames, título e símbolos; inspeção e recorte.
- [x] Interface de batalha: comandos orbitais, informação separada, especial na arena e fallbacks.
- [x] Entrada, estado vazio válido, migração sem apagar saves e cinco batalhas de tutorial.
- [x] Desbloqueios por nível em prédios, atalhos e navegação; HUD de piloto.
- CANCELADO: 244 novos e respectivos lotes. Não retomar.
- [x] Verificação estática de regras, TypeScript/build, dimensões/contagem/HTTP. Entrega do checkpoint, não conclusão de toda a auditoria.

## Cidade imersiva — seis sistemas (2026-10-07)
- Escopo aprovado: seis experiências únicas + mecânicas aprofundadas; lotes IA completos sem prévia. Só web; sem E2E/Playwright.
- [x] Direção registrada em design.md; seis cenários animados, dez portais 16 frames e 24 relíquias gerados.
- [x] Inspeção/recorte e assets públicos: seis folhas 12 frames, dez folhas 16 frames e 24 relíquias repaginadas em 6×4. Dimensões e células distintas verificadas.
- [x] Migração implementada: protocolos/capacitor, rotas pesquisadas, simulações, ressonância, rastreamento/marcos, calibração/tier dimensional. Distribuição sobrecarregada ajustada sem apagar demais campos do save.
- [x] Seis telas próprias ligadas às ações persistentes; animações pausam fora da área visível e respeitam movimento reduzido.
- [x] TypeScript e Vite build passaram; preview e todos os 25 assets novos responderam HTTP 200. Nenhum E2E/Playwright nem teste de gameplay no navegador executado.

## Batalha imersiva (2026-10-07)
- [x] Oito materiais de chão gerados por IA, inspecionados e exportados WebP: madeira, aço, lava, gelo, cristal, floresta, carpete real e mosaico abissal. Mapeados às 41 arenas com fallback.
- [x] Mundo separado do HUD: plano panorâmico, robôs afastados e redimensionados, plataformas em perspectiva, piso contínuo e sombras de contato.
- [x] Câmera por eventos reais: antecipa ações anunciadas, aproxima autor/entrada/ultimate, acompanha impactos e retorna ao plano aberto no fim da fila. UIDs mostram o participante correto mesmo em ações da reserva.
- [x] Projéteis percorrem a distância real entre lados, avanços ajustados ao palco. Console centralizado e rolável, HUD/ordem sem zoom. Câmera fixa e movimento reduzido desativam câmera/tremores; movimento reduzido oculta VFX de tela.
- [x] TypeScript/build aprovados após integração. Sem alterações deliberadas nas regras de dano, recursos, fila ou recompensas; gameplay visual não verificado, conforme proibição de E2E/Playwright.

## Vitória cinematográfica (2026-10-07)
- [x] Três imagens geradas por IA e inspecionadas: duas folhas 5×5 com 25 frames distintos cada; um santuário animado 3×3 com 9 frames distintos.
- [x] Assets WebP em public/victory; reprodução de 50 frames a ~14 fps com luz contínua e dissolução de 850 ms. Pré-carregamento durante a batalha, timeout de segurança e botão de pular.
- [x] Vitória integrada ao encerramento real do BattleScreen, somente após esvaziar os eventos. Derrota preserva relatório anterior; continuação mantém gravação e snapshot existentes, sem duplicar recompensas.
- [x] Tela dividida: arte/MVP aliado à esquerda, resultado/estatísticas reais/abas de equipe, adversários e cronologia à direita; empilhamento em largura pequena.
- [x] Foco de diálogo, navegação por teclado, movimento reduzido e proteção de clique duplicado.
- [x] TypeScript e Vite build passaram; HTTP do preview respondeu 200. Sem execução de E2E/Playwright ou verificação visual de gameplay no navegador.

## Expansão da cidade e dimensões (2026-10-05)
- Plano aprovado: 6 construções físicas (Observatório, Academia, Contratos, Usina, Museu, Portal).
- 10 modos aprovados: Draft, Caravana, Fenda, Espelhos, Cerco, Caça, Reatores, Monoelemental, Apostas, Labirinto.
- Arte: lotes de vários assets por imagem; inimigos exclusivos com 16 frames/chassi, não recrutáveis; 10 arenas novas com 4 frames.
- Sem E2E/Playwright conforme instrução do usuário. Só TypeScript e build.
- [ ] Integrar VFX gl/ult/imp/st_burst/sup/wld e 14 cenários antigos.
- [ ] Recortar e inspecionar arte nova (6 prédios, 8 inimigos, 10 cenários).
- [ ] Estado/migração: sistemas da cidade, talentos, contratos, energia, relíquias, campanhas e percursos.
- [ ] Telas e entradas físicas da cidade.
- [ ] Modos com regras reais de combate e escolhas entre etapas.
- [ ] TypeScript/build e entrega.

### Estado anterior
- Perfil, 250 conquistas, 12 ranks de maestria, equipamentos e skins implementados; tsc/build passaram.
- 106 VFX e 20 fundos gerados na fase H2, parte ainda sem uso no código.
- Último E2E anterior falhou no painel pós-luta; rodada posterior interrompida. Não retomar.
- As regras históricas de proibir arte nova abaixo foram substituídas: nova arte IA autorizada.

## Histórico (fases A–G3)
ver roadmap.md — cards, parallax, exploração, 256 robôs, mineração, laboratório,
pets, cards/gadgets 100x, batalha 100x (100 animações + 28 VFX + 11 arenas).

## FASE H1 — Batalha 100x mais profunda (EM ANDAMENTO)

Pedido do usuário (2026-09-30):
- aprofundar o combate 1v1 por turnos **E** criar modos novos por cima
- **cada um dos 256 robôs com ataques e defesas escritos à mão**, nenhum repetido
- sistemas marcados: passivas/talentos, elementos com fraqueza/resistência/absorção,
  status avançados, timing (parry/esquiva/carga), combos + ultimate combinado,
  IA tática com dificuldades, chefes multi-fase, terreno com hazards, raid/sobrevivência,
  log detalhado + análise pós-luta, UI de combate nova
- entrega: só web por enquanto

### Checklist
- [x] recon do repo (battle.ts, skills.ts, robots.ts, engin/config, save.ts, battle.tsx)
- [ ] game/status.ts — 36 status avançados com mods/tick/reações
- [ ] game/elements.ts — 18 famílias + matriz de afinidade (fraco/resiste/imune/absorve)
- [ ] game/skills.ts — Skill estendida (tags, mecânicas, status, carga, recurso)
- [ ] game/kits/types.ts + index.ts — DSL autoral
- [ ] game/kits/b01..b08.ts — 256 kits autorais (32 por arquivo)
- [ ] game/passives.ts — ~26 hooks + passivas/talentos de cada robô
- [ ] game/mechanics.ts — ~60 mecânicas nomeadas resolvidas no motor
- [ ] game/terrain.ts — terreno/zona/hazard por arena
- [ ] game/combat.ts — motor profundo (iniciativa, formação, timing, combos, fases, IA)
- [ ] game/raid.ts — modo raid/sobrevivência com ondas
- [ ] screens/battle.tsx — UI nova (ordem de turno, preview de dano, fraquezas, combo, log)
- [ ] screens/codex.tsx — arquivo de combate (256 kits navegáveis)
- [ ] fiação: save.ts (formação/raid/loadout 6), menu, game-shell
- [ ] typecheck + build + E2E + deliver website

### Regras mantidas
- NENHUMA arte de personagem nova (só composição/recoloração + 28 VFX existentes)
- 4 fps idle / 8 fps ações; `image-rendering: pixelated`
- salvar em localStorage via save.ts

## 2026-10-07 — PvP integrado + pedido de publicação na Play Store
- OnlineScreen integrada (título "ONLINE · PvP", dock PILOTO, guia). Redirect do login gerenciado concluído no Provider.
- Servidor recusa ações durante golpe carregado (só pass). Replay online com teto (3 revisões/140 eventos).
- Testes: API real 49 ✓, motor competitivo (48 partidas 1v1–4v4, simetria, travas) ✓, regressões 10 ✓, build ✓, HTTP 4200 root/health/auth ✓.
- Pendente: Google login não verificado; .env veio do scaffold mechach-hkul1er (app = campeoe-xwr5e13); exclusão de conta exigida pela Play Store não implementada.
- Play Store: publicar site → publicar mobile pelo painel do preview (conta Expo). Nunca buildar no sandbox.
