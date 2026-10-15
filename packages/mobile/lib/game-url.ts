import Constants from "expo-constants";

/** URL do jogo web (mesma origem da API do template). */
export const GAME_URL = String(
  Constants.expoConfig?.extra?.apiUrl ?? process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:4200",
).replace(/\/+$/, "");
