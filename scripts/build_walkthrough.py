#!/usr/bin/env python3
"""
Genera el PDF del walkthrough divulgativo (WALKTHROUGH.md) con el mismo estilo
visual que el informe técnico.

Uso:
    python scripts/build_walkthrough.py [--out docs/AE1-pushfold-GA-walkthrough.pdf]

Reutiliza las fuentes y estilos de scripts/build_report.py. Las figuras se leen
de docs/img/, así que conviene correr antes scripts/run_ga.py.
"""

import argparse
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Reutilizamos los helpers del generador del informe.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_report import (  # noqa: E402
    REPO_URL,
    ROOT,
    build_styles,
    code,
    figure,
    register_fonts,
)

P = Paragraph


def extra_styles(styles):
    """Agrega estilos propios del walkthrough (cita, viñetas, subtítulo de parte)."""
    styles.add(ParagraphStyle("Quote", parent=styles["Body"], fontName="DejaVu-Oblique",
                              leftIndent=10, rightIndent=6, spaceBefore=4, spaceAfter=10,
                              textColor=colors.HexColor("#444444"),
                              backColor=colors.HexColor("#eef3f7"), borderPadding=7))
    styles.add(ParagraphStyle("Item", parent=styles["Body"], leftIndent=16,
                              bulletIndent=4, spaceAfter=4, alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle("Lead", parent=styles["Body"], fontSize=11,
                              leading=15, spaceAfter=8))
    return styles


def bullet(text, styles):
    return Paragraph(text, styles["Item"], bulletText="•")


def two_col_table(rows, styles, col_widths, header=True):
    data = [[P(c, styles["Body"]) for c in row] for row in rows]
    t = Table(data, colWidths=col_widths)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b0b0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce9f2")))
    t.setStyle(TableStyle(style))
    return t


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVu", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, A4[1] - 1.1 * cm,
                      "Algoritmos Evolutivos I (2026) · MIA · FIUBA")
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.1 * cm,
                           "Walkthrough — Push/Fold con GA")
    canvas.line(2 * cm, A4[1] - 1.25 * cm, A4[0] - 2 * cm, A4[1] - 1.25 * cm)
    canvas.drawString(2 * cm, 1.1 * cm, REPO_URL)
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Página {doc.page}")
    canvas.restoreState()


def build_story(S):
    IMG = os.path.join(ROOT, "docs", "img")
    st = []

    st.append(P("Cómo funciona este proyecto, paso a paso", S["TitleBig"]))
    st.append(P("Una guía accesible sobre la resolución del Desafío Práctico "
                "(Push/Fold con un Algoritmo Genético)", S["Sub"]))
    st.append(Spacer(1, 6))
    st.append(P("Una explicación pensada para <b>cualquier persona</b>, sin necesidad de "
                "saber de algoritmos evolutivos ni de programación. La idea es entender "
                "<i>qué</i> hacemos, <i>por qué</i> y <i>cómo</i> llegamos al resultado, "
                "sin meternos en las cuentas finas.", S["Quote"]))

    # La idea en 30 segundos
    st.append(P("La idea en 30 segundos", S["H1"]))
    st.append(P("Queremos encontrar la <b>mejor forma de jugar</b> una situación concreta "
                "de póker. En vez de calcularla a mano, dejamos que una idea prestada de "
                "la <b>naturaleza</b> la descubra sola: creamos muchas estrategias al "
                "azar, dejamos que «sobrevivan» las mejores, que se «reproduzcan» y "
                "«muten», y repetimos ese ciclo muchas veces. Generación tras generación, "
                "las estrategias mejoran hasta dar con la óptima. A eso se lo llama "
                "<b>Algoritmo Genético</b>.", S["Lead"]))
    st.append(P("Piensen en la evolución de las especies, pero aplicada a estrategias de "
                "póker y acelerada a miles de «años» por segundo dentro de la "
                "computadora.", S["Body"]))

    # Parte 1
    st.append(P("Parte 1 — El problema, en lenguaje humano", S["H1"]))
    st.append(P("El póker de la situación", S["H2"]))
    st.append(P("Imaginen una partida de póker <b>uno contra uno</b> (en la jerga, "
                "<i>heads-up</i>) donde a los dos jugadores les quedan <b>pocas "
                "fichas</b>. Cuando el stack (las fichas que tenés) es chico, jugar con "
                "matices —apostar poco, ver cartas, farolear— casi no tiene sentido: el "
                "riesgo es alto y el margen para maniobrar, mínimo. Por eso la jugada se "
                "reduce a una <b>decisión de sí o no</b>:", S["Body"]))
    st.append(bullet("<b>Push</b> → apostar <i>todas</i> las fichas de una (ir «all-in»).", S))
    st.append(bullet("<b>Fold</b> → tirar la mano y no jugar.", S))
    st.append(P("El jugador recibe sus dos cartas y, sin más vueltas, decide: "
                "<b>¿push o fold?</b>", S["Body"]))
    st.append(P("¿Por qué es un problema interesante?", S["H2"]))
    st.append(P("Porque no da igual con qué cartas hacés cada cosa. Con un par de ases, "
                "obviamente vas all-in. Con un 7 y un 2 de distinto palo (la peor mano "
                "del póker), obviamente tirás. ¿Pero qué hacés con las manos «del medio», "
                "como una jota con un diez? Ahí está la gracia.", S["Body"]))
    st.append(P("En el póker hay <b>169 tipos de mano inicial distintos</b>. Una "
                "<b>estrategia completa</b> es una decisión —push o fold— para <i>cada "
                "una</i> de esas 169 manos. ¿Cuántas estrategias posibles hay? Como cada "
                "mano tiene 2 opciones y son 169 manos, el total es <b>2¹⁶⁹</b>, un número "
                "con más de <b>50 cifras</b>: muchísimo más grande que la cantidad de "
                "átomos que hay en la Tierra. <b>Probarlas todas una por una es "
                "imposible</b>, ni con todas las computadoras del mundo.", S["Body"]))
    st.append(P("Y acá aparece la pregunta central del proyecto: entre esas 2¹⁶⁹ "
                "estrategias posibles, ¿cuál es la que más fichas gana a la larga? Buscar "
                "la mejor aguja en un pajar tan gigante es justo el tipo de problema donde "
                "brillan los <b>algoritmos evolutivos</b>.", S["Body"]))

    # Parte 2
    st.append(P("Parte 2 — ¿Qué es un Algoritmo Genético?", S["H1"]))
    st.append(P("Es una técnica de búsqueda inspirada en la <b>selección natural</b> de "
                "Darwin. En lugar de razonar la respuesta, la hacemos <i>evolucionar</i>. "
                "Los ingredientes son los mismos que en la biología:", S["Body"]))
    st.append(two_col_table([
        ["En la naturaleza", "En nuestro algoritmo"],
        ["Un <b>individuo</b> (un bicho)", "Una <b>estrategia</b> de póker"],
        ["Su <b>ADN</b> (cromosoma)", "La lista de 169 decisiones push/fold"],
        ["Una <b>población</b>", "Un montón de estrategias conviviendo"],
        ["Qué tan <b>apto</b> es para sobrevivir", "Cuántas <b>fichas gana</b> la estrategia"],
        ["<b>Reproducción</b> (los hijos heredan)", "Combinar dos estrategias buenas en una nueva"],
        ["<b>Mutación</b> (cambios al azar)", "Cambiar alguna decisión suelta al azar"],
        ["Una <b>generación</b>", "Una vuelta completa del ciclo"],
    ], S, [7.5 * cm, 8 * cm]))
    st.append(Spacer(1, 6))
    st.append(P("La regla de oro es la misma que en la evolución: <b>los más aptos tienen "
                "más chances de dejar descendencia</b>. Si repetimos el ciclo muchas "
                "veces, la población entera va mejorando, porque las buenas "
                "características se acumulan y las malas se descartan.", S["Body"]))
    st.append(P("Lo importante: el algoritmo <b>no sabe nada de póker</b>. Solo sabe "
                "comparar estrategias por cuántas fichas ganan y aplicar estas reglas de "
                "«supervivencia del más apto». Aun así, termina descubriendo una forma de "
                "jugar muy sensata. Eso es lo fascinante.", S["Body"]))

    # Parte 3
    st.append(P("Parte 3 — Cómo lo resolvimos, paso a paso", S["H1"]))

    st.append(P("Paso 0 — Preparar un «árbitro» que sepa quién gana", S["H2"]))
    st.append(P("Antes de que el algoritmo empiece a evolucionar, necesitamos algo que le "
                "diga, para cualquier enfrentamiento de cartas, <b>qué tan probable es "
                "ganar</b>. Por ejemplo: un par de ases le gana a un par de reyes el "
                "<b>82%</b> de las veces. Calculamos por adelantado una <b>gran tabla</b> "
                "con la probabilidad de ganar de cada mano contra cada otra (169 × 169). "
                "La calculamos una sola vez —simulando muchísimos repartos— y la "
                "guardamos; a partir de ahí el algoritmo la consulta al instante, como "
                "quien mira un vademécum. En el proyecto la llamamos <b>matriz de "
                "equity</b>.", S["Body"]))

    st.append(P("Paso 1 — Escribir una estrategia como una lista de ceros y unos", S["H2"]))
    st.append(P("Cada estrategia se representa como una <b>grilla de 169 casilleros</b>, "
                "uno por cada tipo de mano. En cada casillero ponemos <b>1</b> si con esa "
                "mano vamos a hacer <b>push</b>, o <b>0</b> si vamos a hacer <b>fold</b>. "
                "Esta grilla es exactamente el «ADN» de la estrategia: los jugadores ya "
                "usan estas tablas 13×13 para estudiar; acá las volvemos números que la "
                "computadora puede manipular.", S["Body"]))

    st.append(P("Paso 2 — Medir qué tan buena es una estrategia (el «fitness»)", S["H2"]))
    st.append(P("Para comparar estrategias necesitamos un puntaje. El nuestro es muy "
                "natural: <b>¿cuántas fichas gana (o pierde), en promedio, esta "
                "estrategia por cada mano jugada?</b> Lo calculamos recorriendo las 169 "
                "manos y, según lo que diga la grilla, sumando las fichas esperadas en "
                "cada caso (usando el árbitro del Paso 0 y con qué manos nos paga el "
                "rival). El resultado es un único número, el <b>fitness</b>: cuanto más "
                "alto, mejor. Ese es el puntaje que el algoritmo intenta maximizar.",
                S["Body"]))

    st.append(P("Paso 3 — Arrancar con una población al azar", S["H2"]))
    st.append(P("Creamos <b>80 estrategias completamente aleatorias</b>. Casi todas van a "
                "ser malísimas —hacen all-in con basura y tiran manos buenas—, y eso está "
                "perfecto: son el «caldo primitivo» del que va a partir la evolución.",
                S["Body"]))

    st.append(P("Paso 4 — El ciclo de una generación", S["H2"]))
    st.append(P("Con la población actual hacemos cuatro cosas:", S["Body"]))
    st.append(bullet("<b>1. Selección (los más aptos «sobreviven»).</b> Elegimos parejas "
                     "para que se reproduzcan, favoreciendo a las de mayor fitness "
                     "mediante un mini-torneo: tomamos unas pocas al azar y gana la "
                     "mejor.", S))
    st.append(bullet("<b>2. Cruza (reproducción).</b> De cada pareja nace una estrategia "
                     "«hija» que hereda algunas decisiones de un padre y otras del otro; "
                     "combinar dos buenas puede dar una mejor.", S))
    st.append(bullet("<b>3. Mutación (variación al azar).</b> A la hija le cambiamos "
                     "alguna decisión suelta al azar. Esto introduce novedad y evita que "
                     "la población se estanque.", S))
    st.append(bullet("<b>4. Elitismo (no perder lo mejor).</b> Las <b>2 mejores</b> "
                     "estrategias pasan intactas a la siguiente generación, así nunca "
                     "damos un paso atrás.", S))
    st.append(P("El resultado es una <b>nueva generación</b> de 80 estrategias, en "
                "promedio un poquito mejores que las anteriores.", S["Body"]))

    st.append(P("Paso 5 — Repetir muchas veces", S["H2"]))
    st.append(P("Repetimos el Paso 4 <b>120 veces</b> (120 generaciones). Al principio "
                "las mejoras son enormes; después, cada vez más finas, hasta que la "
                "población deja de mejorar porque ya encontró la mejor forma de jugar. En "
                "ese punto, paramos.", S["Body"]))

    st.append(P("Paso 6 — Verificar que la respuesta sea la correcta", S["H2"]))
    st.append(P("¿Cómo sabemos que es de verdad lo óptimo? En esta versión el rival juega "
                "de una forma fija, así que la respuesta perfecta se puede <b>calcular "
                "directamente con una cuenta</b> (mano por mano, conviene ir all-in solo "
                "si eso gana más fichas que tirar). Comparamos la estrategia evolucionada "
                "contra esa respuesta calculada y coinciden en <b>las 169 manos</b>: el "
                "Algoritmo Genético llegó, solo y sin saber póker, exactamente a la jugada "
                "óptima. Esa es nuestra prueba de que todo funciona.", S["Body"]))

    # Parte 4
    st.append(P("Parte 4 — Cómo leer los resultados", S["H1"]))
    st.append(P("1. La curva de convergencia — «cómo aprende el algoritmo»", S["H2"]))
    st.append(P("El eje horizontal son las generaciones y el vertical, el fitness (fichas "
                "por mano; <b>más arriba es mejor</b>). Las estrategias arrancan muy abajo "
                "(perdiendo, porque son al azar) y <b>suben rápido</b> hasta pegarse a la "
                "línea verde punteada, que marca la jugada óptima. Esa «subida que se "
                "aplana» es la firma de un algoritmo que <b>converge</b>.", S["Body"]))
    st += figure(os.path.join(IMG, "convergencia.png"), S,
                 "La curva de convergencia: el algoritmo mejora mucho al principio y luego "
                 "se estabiliza en la mejor respuesta.", width=13.5 * cm)
    st.append(P("2. El diagrama de caja — «qué tan confiable es»", S["H2"]))
    st.append(P("Corrimos el experimento <b>30 veces</b> (cada una desde un azar "
                "distinto) y miramos qué tan bien le va según cuántas generaciones la "
                "dejemos correr. Con <b>más generaciones</b>, las cajas suben hacia la "
                "línea óptima y se vuelven <b>más chiquitas</b>: no solo mejora el "
                "promedio, sino que <b>todas</b> las corridas terminan dando lo mismo. El "
                "método es <b>consistente</b>, no depende de la suerte.", S["Body"]))
    st += figure(os.path.join(IMG, "boxplot.png"), S,
                 "Con más generaciones, todas las corridas convergen al óptimo y la "
                 "dispersión desaparece.", width=12 * cm)
    st.append(P("3. La grilla de la estrategia — «el resultado, en idioma póker»", S["H2"]))
    st.append(P("La estrategia ganadora traducida de vuelta al póker. En verde, las manos "
                "con las que conviene ir <b>all-in</b>; en gris, las que conviene "
                "<b>tirar</b>. El resultado tiene todo el sentido del mundo: all-in con "
                "<b>todos los pares</b> y con <b>cualquier mano que tenga un as o un "
                "rey</b> (sí, incluso K2), más las manos altas y algunos conectores del "
                "mismo palo; y se tiran las manos bajas y descoordinadas. Que hasta K2 "
                "entre no es porque sea fuerte, sino porque —con el rival foldeando casi "
                "la mitad de las veces y la ciega ya posteada— <b>rendirse pierde todavía "
                "más</b>. En total, push con alrededor del <b>43%</b> de las manos. El "
                "algoritmo redescubrió, por su cuenta, una tabla que los jugadores tardaron "
                "años en pulir.", S["Body"]))
    st += figure(os.path.join(IMG, "rango.png"), S,
                 "La estrategia óptima hallada por el algoritmo, en la clásica grilla "
                 "13×13 del póker (verde = push, gris = fold).", width=9.8 * cm)

    # Parte 5
    st.append(P("Parte 5 — Qué aprendimos (y qué falta)", S["H1"]))
    st.append(P("<b>Lo importante:</b> un procedimiento que solo sabe «quedarse con lo "
                "mejor y variar un poco», repetido muchas veces, es capaz de resolver un "
                "problema con más combinaciones que átomos en el planeta y llegar a una "
                "respuesta <b>correcta y con sentido</b>. Esa es la potencia de los "
                "algoritmos evolutivos.", S["Body"]))
    st.append(P("<b>La limitación honesta:</b> en esta versión el rival juega de una "
                "forma <b>fija</b>. Eso hace el problema más sencillo (por eso pudimos "
                "verificar la respuesta con una cuenta directa). El paso siguiente, más "
                "ambicioso, sería que <b>los dos jugadores evolucionen a la vez</b>, "
                "adaptándose el uno al otro, hasta un punto de equilibrio en el que "
                "ninguno pueda mejorar cambiando su estrategia (el <b>equilibrio de "
                "Nash</b>). Ahí el problema se vuelve más rico y el algoritmo evolutivo se "
                "luce todavía más.", S["Body"]))

    # Mapa mental
    st.append(P("Mapa mental para recordarlo", S["H1"]))
    st.append(code(
        "        169 decisiones push/fold  =  una estrategia (el \"ADN\")\n"
        "                     │\n"
        "        80 estrategias al azar     =  la poblacion inicial\n"
        "                     │\n"
        "   ┌──────────────► repetir 120 veces ◄─────────────┐\n"
        "   │                                                │\n"
        "   │   1. seleccionar las mejores (fitness)         │\n"
        "   │   2. cruzarlas  → estrategias hijas            │\n"
        "   │   3. mutar un poco al azar                     │\n"
        "   │   4. conservar las 2 mejores (elitismo)        │\n"
        "   │                                                │\n"
        "   └────────────────────► ↑ ───────────────────────┘\n"
        "                     │\n"
        "        la poblacion converge a la mejor jugada\n"
        "                     │\n"
        "        verificamos: coincide con la respuesta optima  ✓", S))

    st.append(Spacer(1, 4))
    st.append(P("Para el detalle técnico completo, ver el README, el informe en PDF y el "
                "código comentado en src/pushfold/ del repositorio.", S["Body"]))
    return st


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=os.path.join(ROOT, "docs",
                                                       "AE1-pushfold-GA-walkthrough.pdf"))
    args = parser.parse_args()

    register_fonts()
    styles = extra_styles(build_styles())
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    doc = SimpleDocTemplate(
        args.out, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="Walkthrough — Push/Fold con GA (Algoritmos Evolutivos I 2026)",
        author="Facundo Rivas",
    )
    doc.build(build_story(styles),
              onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"PDF generado: {args.out}")


if __name__ == "__main__":
    main()
