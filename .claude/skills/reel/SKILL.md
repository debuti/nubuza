---
name: reel
description: Hace un reel vertical terminado (1080 × 1920, voz, subtítulos por palabra, gráficos animados en código) a partir de una línea. Úsala cuando la persona escriba /reel o pida un reel, un short o un vídeo explicativo animado.
---

# Hacer un reel

Entra una línea y sale un vídeo terminado en `reel/reels/<nombre-corto>/<nombre-corto>.mp4`. Todo vive en `reel/` (proyecto Remotion, `.venv` de Python, modelos en `reel/models/`). Lee siempre `reel/style.md` primero. El repo es público: los vídeos, audios, `plan.md` y storyboards van en `reel/reels/` (ignorado por git); nunca los subas. La persona aprueba dos cosas: el guion y el storyboard. Nunca te saltes ninguna.

Los reels salen mejor con Claude Opus 5.5 o un modelo más potente, con esfuerzo alto. Si no es lo que estás usando, o no lo sabes, díselo y pregúntale si quiere cambiar antes de empezar.

1. La idea. Si la línea no deja claro qué debe decir el reel, para quién es y de qué app de nubuza va, haz dos o tres preguntas cortas.
2. El guion. Entre 70 y 120 palabras habladas (25 a 45 s). Usa el idioma de `style.md` salvo que te pidan otro.
   - Estructura por defecto: problema → solución. A nadie le interesa un producto si no sabe qué le resuelve.
     1. El problema (40-50 % del guion): empieza por el dolor concreto que tiene quien ve el vídeo, en sus palabras y con una situación reconocible. La primera frase es ese dolor, no la app.
     2. Por qué duele o por qué lo de siempre no funciona: una o dos frases, con una cifra real si la hay.
     3. La solución: la app aparece aquí, nunca antes. Enseña cómo resuelve ese mismo problema, en pantalla, paso a paso.
     4. Cierre: la última idea es el resultado para la persona más dónde conseguir la app (nombre y web). Sin resumen.
   - Usa otra estructura solo si la persona la pide.
   - El valor real empieza antes del segundo 10.
   - Frases completas, como se dirían en voz alta. Cifras concretas y verdaderas. Nunca inventes resultados ni funciones de la app.
   - Una idea por frase, porque cada frase será una imagen. Termina en la última idea, sin resumen.
   - Enseña el guion y espera a que lo apruebe.
3. La voz. Ejecuta `reel/scripts/tts.py` con el guion y luego `reel/scripts/align.mjs`. El guion manda: conserva sus palabras y toma solo los tiempos.
4. El plan. Escribe `plan.md` con una escena por frase: sus palabras, su inicio y su fin, qué se ve y qué componentes de `reel/src/kit/` usa. Revísalo contra «Que quede bien» antes de dibujar nada.
5. El storyboard. Saca cada escena en su momento más lleno con `npx remotion still` y júntalas en una sola hoja con ffmpeg (tile), numeradas y con su texto debajo. Mándale la hoja y espera a que la apruebe; redibuja solo las escenas que pida cambiar.
6. La construcción. Anima cada escena en Remotion siguiendo las skills de Remotion y reutilizando `reel/src/kit/`. Si creas algo que servirá para otros reels, añádelo al kit.
   - Todo movimiento se calcula a partir del frame. Nada de animaciones ni transiciones CSS.
   - Cada cambio en pantalla cae sobre la palabra a la que pertenece.
7. Los subtítulos. Usa `Captions`. En español, cortes de 2 a 5 palabras, sin separar el artículo de su nombre ni la preposición de lo que sigue.
8. El sonido. Pocos efectos de `Sfx`, solo en los momentos clave. Si `style.md` lo pide y hay pista en `music/`, música de fondo baja. La voz siempre es lo que más se oye.
9. El render. MP4 a 1080 × 1920 y 30 fps; después normaliza el volumen con ffmpeg `loudnorm` al valor de `style.md`.
10. La autocomprobación: primero mide, luego mira.
    - Huecos muertos: ffmpeg `freezedetect` con la duración de `style.md`.
    - Exceso de movimiento: compara fotogramas cada 0,5 s. Si gran parte de la imagen cambia sin que cambie la escena, o se mueven más cosas de las permitidas, está demasiado cargado.
    - Lectura: hoja con un fotograma cada segundo y su tiempo. Busca texto borroso, cortado, demasiado pequeño para un móvil o fuera de la zona segura.
    - Sonido: compara la duración del audio con la de la última palabra; ninguna frase debe quedar cortada.
    - Arregla lo que falle y vuelve a renderizar, como mucho tres rondas. Di qué mediste, qué falló y qué cambiaste.
11. La entrega. Manda el vídeo, di su ruta y una cosa que mejorarías la próxima vez.

Cuando pida un cambio concreto («el hook más grande»), cambia solo eso y vuelve a renderizar.

Cuando diga cómo debe sentirse («más calmado», «más movimiento», «texto más grande»), cambia el reel y luego ajusta los números y reglas de `style.md` para que el siguiente reel ya salga a su gusto. Dile qué has cambiado allí.

## Que quede bien

- Explica la idea con un dibujo: un diagrama, un gráfico, un objeto, una maquinita funcionando. Poco texto en pantalla.
- Un solo foco cada vez. Antes de sustituir algo, transforma lo que ya está (crecer, llenarse, romperse).
- La imagen cambia en cada frase y siempre con movimiento. Nada se queda quieto mientras sigue la voz.
- Movimientos cortos y con peso: llegan rápido y se asientan. Nada de fundidos lentos, giros ni derivas.
- Los números suben. Las líneas se dibujan solas. Si se habla de una app, sale su pantalla (de `brand/` o dibujada) y se mueve.
- Una fuente, los colores de `style.md` y el acento solo en lo importante. Nada de degradados, brillos, emojis ni iconos de stock.
- El primer frame ya muestra el hook en texto y algo se está moviendo.
- Todo lo que haya que leer queda dentro de la zona segura de `style.md`.
- Todo se lee en un móvil. Si un frame podría ser de cualquier vídeo, haz que sea de este.
