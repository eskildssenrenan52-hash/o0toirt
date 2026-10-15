# CAMPEÕES MECHA — Design

Jogo de batalha por turnos (RPG tático 1v1 com equipe de 4 robôs), web mobile-first, 100% pixel art
gerada por IA. Mecânicas replicadas de "Ben 10 Campeões Galácticos" (fórmulas de dano, evasão,
crítico, XP, treino e torneios extraídas do SWF original), com 20 robôs originais estilo anime.

## Direção de arte

- Revisão anime mecha (pedido mais recente): REMOVER holograma e console orbital. Painéis blindados com molduras pixel existentes, retratos grandes espelhados, HP/MP legíveis, quatro ataques sempre visíveis com nome/custo e duas defesas em faixa distinta. Ultimate recebe painel dourado próprio; utilitários ficam subordinados. Arena e HUD fora da câmera; console inferior com largura responsiva e sem sobrepor o palco. Sem alteração de roster ou exigência de E2E.
- Revisão de escopo: expansão para 500 robôs cancelada pelo usuário. Manter os 256 recrutáveis e oito NPCs existentes; não produzir ou cadastrar as 244 identidades planejadas. Continuar abertura, arena, tutorial, interface e refinamento de sistemas. O manifesto antigo é somente histórico, não uma fila ativa.
- Revisão aprovada (2026-10-07): abertura Remulu Games com logo IA em pixel art sobre preto, fade in/hold/fade out e sem locução. Depois, carregamento com 50 desenhos IA em duas folhas 5×5, três fundos selecionáveis (Hangar, Cidade Noturna, Órbita), progresso baseado em requisições concluídas/decodificadas, erros explícitos e repetição dos assets que falharam. Preferência visual separada do save de jogo.
- O pedido novo substitui a tela preta do ultimate: especial acontece dentro da arena, no ator e no alvo reais, mantendo o palco e HUD visíveis. Carga continua individual e regras/recompensas não dependem da animação. Redução de movimento mantém um frame estático, sem deslocamentos nem flashes.
- Refinamento de todos os sistemas é incremental: abertura/batalha primeiro; orientação contextual, Hangar/equipe e tutorial em seguida; aprofundamento restante continua pendente até implementação e validação, nunca chamado de completo só por um plano. Não há expansão de robôs em execução.
- Overhaul aprovado (2026-10-07): entrada MECHA CHAMPIONS com Jogar/Tutorial; console orbital no canto inferior esquerdo, elevado, holograma de 50 frames (duas folhas 5×5), quatro símbolos de ataque em linha com informação independente, duas defesas, itens e ultimate separado. Ultimate individual 0–100%, sem MP: ataque +18%, defesa +14%, dano recebido +4–16% proporcional ao HP perdido; ultimate não recarrega a si mesmo. Tela preta desce para a sequência exclusiva. Combos de batalha removidos; coleta de núcleos na cidade continua independente.
- Progressão nova: zero ouro/itens/robôs; Aurorion entregue ao começar o tutorial. Cinco batalhas reais com diálogo de missão e checkpoints. Hangar/Arena/Coliseu no nível 1; Loja 2, Oficina/Contratos 3, Ranqueado/Academia 4, Mina 5, Pets 6, Cards 7, Usina 8, Observatório 9, Museu 10, Laboratório 12, Portal 15. Saves anteriores preservam acessos existentes. Piloto no topo direito; atalhos simbólicos agrupados.
- Arte de especiais para os robôs atuais: distinguir sequências exclusivas prontas dos efeitos existentes usados como fallback; nenhum recorte repetido/recolorido conta como sequência IA exclusiva. Expansão de identidades cancelada.
- Batalha imersiva (2026-10-07): palco panorâmico com robôs afastados, oito materiais de chão IA mapeados às 41 arenas, plataformas em perspectiva e sombras de contato. Câmera aproxima o autor da ação e acompanha o impacto conforme a fila real de eventos; retorna ao plano aberto entre turnos. HUD/menus ficam fora da câmera, comandos centralizados com largura limitada. Movimento reduzido ou botão CÂMERA FIXA desliga aproximação e tremores, sem alterar regras, ordem ou recursos.
- Cidade imersiva (2026-10-07): seis telas com composições próprias, não listas de painéis idênticos. Usina = mapa isométrico com fios/fluxos e despacho por prédio; Observatório = carta estelar e percurso ramificado; Academia = bancada de chassi com três árvores visuais; Contratos = mapa de 24 operações e rastreamento de até três missões; Museu = salão/vitrines com peças IA e ressonância de conjuntos; Portal = salão de dez portais, cada qual com 16 frames IA, preparação e mapa de etapas.
- Novas regras: protocolos de energia e capacitores por batalhas; melhorias de rotas/sondas e escolhas de expedição; simulações da academia com cargas por batalhas; pesquisas de ressonância do museu; marcos e resgate encadeado dos contratos; calibração dimensional, tiers de desafio e bênção inicial. Todas persistentes, sem relógio obrigatório, sem dinheiro real. Regras e custos visíveis, saves antigos migrados sem perder progresso.
- Cenários IA com 12 frames por folha; fluxos e câmera com movimentos contínuos suaves, portais em folhas 4×4; pausar animação fora da área visível e respeitar movimento reduzido. Textos/hotspots permanecem DOM acessível, imagens não contêm labels necessários ao jogo.
- Vitória cinematográfica: ignição suave → 50 frames IA em duas folhas 5×5 (25 por imagem) → dissolução de 800 ms para tela dividida. Metade ilustrada com santuário dourado/ciano de nove frames IA, metade com resultado, MVP aliado e estatísticas reais. Em telas estreitas as metades ficam empilhadas. Sem cópia de marcas; referência de composição de RPG mobile. Movimento reduzido pula o espetáculo e mantém resultado estático; botão permite pular animação.
- Expansão dimensional: cidade estendida com seis prédios físicos IA; telas de sistemas mantêm painéis pixel, arte do prédio no cabeçalho e indicadores ciano/âmbar. Portal usa cards ilustrados por modo, mapa ramificado, escolhas entre lutas e HUD de objetivos.
- Perfil: 12 novas cenas em folhas 3×3 (9 frames), compráveis com diamantes de jogo. Contratos: 360 missões em 24 cadeias, filtros, dois objetivos combinados por missão e resgate único persistente.
- NPCs exclusivos usam tiras de 16 frames e nunca entram no catálogo de recrutamento. Movimento reduzido desativa flashes de tela; alertas de objetivo devem ter texto além da cor.
- **Tudo é pixel art gerada por IA**: robôs (16 frames cada), botões, painéis, ícones, barras,
  molduras, VFX, logo, fundo do menu, arenas (4 frames a 4fps).
- Nenhum ícone vetorial/lucide, nenhuma borda CSS "moderna": bordas vêm de `border-image` sobre os
  PNGs de painel/botão.
- `image-rendering: pixelated` global; escalas em múltiplos inteiros quando possível.
- Animação em **4 fps** (arenas e sprites idle), 8 fps em ações rápidas (ataque/dano).

## Online PvP (aprovado 2026-10-07)

- Servidor próprio no mesmo app (Hono + oRPC + Turso), autoritativo: cliente só envia comandos; motor, sorte (sal secreto), turnos, prazos e resultado ficam no servidor. Contas Better Auth (Google gerenciado + e-mail/senha).
- Acesso pela tela inicial (ONLINE · PVP) e pelo dock PILOTO na cidade; sem exigência de progresso offline. Fila pública por tamanho de equipe e salas privadas por código de 10 caracteres.
- Equipe de 1–4 robôs únicos escolhidos entre os 256 recrutáveis (sem NPCs/laboratório); nível 10 fixo, sem treino, equipamento, pets, cards ou itens. Turno de 60 s; tempo esgotado passa a vez; 3 perdas seguidas = derrota por abandono.
- Tela online mantém o visual de painéis blindados ciano/âmbar: cabeçalho com piloto e V/D, abas FILA / SALA, grade de retratos com busca e filtro por elemento, faixa da equipe com 4 slots, ranking dos 10 primeiros. Espera mostra código grande copiável e cancelamento.
- Batalha online reutiliza palco, câmera, comandos de anime mecha e ultimate na arena. Sem AUTO e sem SUPRIMENTOS. Barra superior do servidor: relógio do turno (âmbar < 15 s), "SUA VEZ"/"VEZ DO OPONENTE", nome do rival, perdas de turno e botão DESISTIR com confirmação. A reprodução usa eventos compactos do servidor; o estado final sempre vem do servidor.
- AUTO removido de todas as batalhas (online e offline).

## Paleta (derivada dos assets)

| Token | Hex | Uso |
|---|---|---|
| bg | #070b14 | fundo geral |
| bg-2 | #0e1524 | superfícies |
| panel | #1b3a5c | interior de painel |
| accent | #35e2f0 | ciano tech (destaque, MP) |
| accent-2 | #ffb43a | âmbar (XP, ouro) |
| hp | #e2453a | vida |
| ok | #57d76a | confirmar |
| text | #e8f4ff | texto |
| muted | #7d94ad | texto secundário |

## Tipografia

- Títulos/HUD: `Press Start 2P` (`/fonts/press-start-2p.woff2`).
- Corpo/números: `Silkscreen` (`/fonts/silkscreen.woff2`).
- Sem antialias suave: `letter-spacing` mínimo 0.02em, tamanhos 8/10/12/16px.

## Telas

1. **Splash/Menu** — logo pixel, fundo `bg_menu`, botões: Jogar, Equipe, Treino, Torneios, Loja.
2. **Coleção/Equipe** — grid de robôs desbloqueados, moldura bronze/prata/ouro por raridade,
   escolha de 4 para a equipe.
3. **Robô (detalhe)** — retrato + strip animado, atributos (HP/MP/STR/DEF/AGL), skills, XP.
4. **Treino** — gastar ouro para subir STR/DEF/AGL até `maxTrained` do nível.
5. **Loja** — itens de batalha (reparo, energia, revive, buffs) e cápsulas de robô.
6. **Torneios** — 5 torneios (dojo, vulcão, orbital, congelada, céu), chave de lutas sequenciais.
7. **Batalha** — arena animada 4fps, HUD com barras HP/MP, menu Atacar/Defender/Item/Trocar,
   VFX por skill, entrada/saída de robô, log de turno.
8. **Resultado** — vitória/derrota, ouro/XP, level up, recompensas (robô/item/medalha).

## Fluxo

Menu → Torneio → seleção de equipe (4) → batalha em série (n lutas) → recompensa → volta ao mapa.
Progresso salvo em `localStorage` (offline total, nenhuma chamada de rede necessária).
