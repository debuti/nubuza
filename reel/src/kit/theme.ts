import {loadFont} from '@remotion/google-fonts/Fredoka';
// Valores de style.md
export const {fontFamily} = loadFont('normal', {weights: ['500', '600', '700'], subsets: ['latin', 'latin-ext']});
export const C = {bg: '#1d1838', text: '#f4ecff', accent: '#ff8fbd', soft: '#7a6d96', board: '#f4ecff'};
// Zona segura (IG, TikTok, Shorts): nada legible fuera de esto
export const SAFE = {top: 250, bottom: 1920 - 450, left: 150, right: 1080 - 150};
