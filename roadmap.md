# Campeões Mecha — Roadmap do mega-escopo

Entrega **incremental**: uma fase (ou parte de fase) por sessão, sempre com
`bun run typecheck` + `bun run build` verdes, E2E sem erros de console e `deliver`
(mobile na 4300 no índice 0, website na 4200 no índice 1).

| Fase | Sistema | Estado |
|---|---|---|
| A | **Cards de combate** — 30 cards pixel art por IA, 3 slots, custo de deck, sinergias por tag + combos nomeados, decks também para os inimigos/IA | ✅ concluída |
| B | **Parallax do hub** — céu, montanhas, skyline distante, construções separadas e decorações, todas geradas por IA em camadas independentes | ✅ concluída |
| C | **Exploração** — modo side/top-down com sprites animados por ação (andar, correr, atacar, dano), todos os robôs jogáveis, chão/plataformas/props por IA (mesma técnica 4x4 + magenta) | ✅ concluída |
| D | **1000+ robôs** — cada robô com sprite sheet 4x4 próprio gerado por IA, entregue em lotes sessão após sessão (insetoides, ninjas, colossos, alienígenas, cavaleiros/samurais) | ⏸️ congelada a pedido do usuário (256 robôs) |
| E | **Mineração em tempo real** — sala de mineração, personagem jogável, veios, refino, produção offline | ✅ concluída |
| F | **Laboratório** — construir o próprio robô com 1000+ opções por parte do corpo (peças da Fase D), stats derivados das peças | ✅ concluída |
| G1 | **Pets em carrossel + sistema 100x** — tela de pets refeita como carrossel (um pet no centro, setas nas laterais), 144 pets (12 espécies × 12 linhagens), 20 níveis em 3 estágios de evolução, afinidade secundária, 2 traços, 3 slots de equipe | ✅ concluída |
| G2 | **Cards e gadgets 100x** — 210 cards (30 bases × 7 selos), refino +9, 5 slots de deck, 3 camadas de sinergia; gadgets até Lv30 em 3 marcos MK, 3 sockets e 48 chips forjáveis | ✅ concluída |
| G3 | **Batalha 100x + 100 animações** — catálogo de 100 animações nomeadas (entrada, preparo, impacto, buff, status, morte, combo, ultimate, tela), 20 novos VFX de ataque (28 no total), 6 novas arenas animadas (11 no total) em spritesheet único | ✅ concluída |
| G4 | **Mundo dos torneios** — tela de torneios vira um mundo enorme explorável com a gameplay do hub: cada prédio é um torneio, com puzzles, inimigos e NPCs no caminho; tiles, fundos e construções diferentes em cada região | pendente |
| G5 | **Controles novos** — joystick analógico (intensidade = correr, sem botão de correr), botão de ataque e botão de ataque especial | pendente |
| H | **+50 sistemas** — em lotes de ~6 por sessão, cada um com construção própria no hub e objetivo real de gameplay | pendente |

## Decisão de engenharia (Fase D/F)

1000 sprite sheets gerados por IA é inviável em custo e tempo. Em vez disso:
peças pixel art geradas por IA → composição programática. Isso produz ao mesmo
tempo os 1000+ robôs jogáveis e as 1000+ opções por parte do corpo do laboratório,
mantendo o padrão de animação (grade 4x4, chroma key magenta).
