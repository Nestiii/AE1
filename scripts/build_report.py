#!/usr/bin/env python3
"""
Genera el informe en PDF del Desafío Práctico (>= 3 carillas).

Uso:
    python scripts/build_report.py [--author "Nombre Apellido"] [--out docs/informe.pdf]

Produce un PDF con: introducción y problema, modelo y función de fitness,
el algoritmo genético (con fragmentos de código relevantes), metodología,
resultados (gráfico de convergencia, box plot y grilla de rango), los
inconvenientes encontrados y cómo se resolvieron, y conclusiones.

Requiere `reportlab` y `matplotlib` (de este último se toman las fuentes
DejaVu para tener soporte unicode completo). Las figuras se leen de docs/img/,
así que conviene correr antes scripts/run_ga.py.
"""

import argparse
import os
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG = os.path.join(ROOT, "docs", "img")
REPO_URL = "https://github.com/Nestiii/AE1"


# --------------------------------------------------------------------------- #
# Fuentes (DejaVu, unicode) tomadas de matplotlib.
# --------------------------------------------------------------------------- #
def register_fonts() -> None:
    ttf = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    pairs = {
        "DejaVu": "DejaVuSans.ttf",
        "DejaVu-Bold": "DejaVuSans-Bold.ttf",
        "DejaVu-Oblique": "DejaVuSans-Oblique.ttf",
        "DejaVuMono": "DejaVuSansMono.ttf",
    }
    for name, fname in pairs.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(ttf, fname)))
    pdfmetrics.registerFontFamily(
        "DejaVu", normal="DejaVu", bold="DejaVu-Bold",
        italic="DejaVu-Oblique", boldItalic="DejaVu-Bold",
    )


# --------------------------------------------------------------------------- #
# Estilos.
# --------------------------------------------------------------------------- #
def build_styles():
    styles = getSampleStyleSheet()
    base = dict(fontName="DejaVu", leading=14, fontSize=10)
    styles.add(ParagraphStyle("Body", parent=styles["Normal"],
                              alignment=TA_JUSTIFY, spaceAfter=6, **base))
    styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontName="DejaVu-Bold",
                              fontSize=14, spaceBefore=12, spaceAfter=6,
                              textColor=colors.HexColor("#12507a")))
    styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontName="DejaVu-Bold",
                              fontSize=11.5, spaceBefore=8, spaceAfter=4,
                              textColor=colors.HexColor("#1f77b4")))
    styles.add(ParagraphStyle("TitleBig", parent=styles["Title"], fontName="DejaVu-Bold",
                              fontSize=18, leading=22, spaceAfter=4))
    styles.add(ParagraphStyle("Sub", parent=styles["Normal"], fontName="DejaVu",
                              fontSize=10.5, alignment=TA_CENTER, textColor=colors.grey,
                              spaceAfter=2))
    styles.add(ParagraphStyle("CodeBlock", parent=styles["Code"], fontName="DejaVuMono",
                              fontSize=7.6, leading=9.6, backColor=colors.HexColor("#f4f4f4"),
                              borderPadding=5, leftIndent=4, spaceBefore=4, spaceAfter=8,
                              textColor=colors.HexColor("#222222")))
    styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontName="DejaVu-Oblique",
                              fontSize=8.5, alignment=TA_CENTER, textColor=colors.grey,
                              spaceBefore=2, spaceAfter=10))
    styles.add(ParagraphStyle("Formula", parent=styles["Normal"], fontName="DejaVu",
                              fontSize=10.5, alignment=TA_CENTER, spaceBefore=4,
                              spaceAfter=6, textColor=colors.HexColor("#333333")))
    return styles


def P(text, style):
    return Paragraph(text, style)


def code(text, styles):
    return Preformatted(escape(text.strip("\n"), {"<": "&lt;"}), styles["CodeBlock"])


def figure(path, styles, caption, width=15.5 * cm):
    from reportlab.lib.utils import ImageReader
    ir = ImageReader(path)
    iw, ih = ir.getSize()
    h = width * ih / iw
    return [Image(path, width=width, height=h), P(caption, styles["Caption"])]


# --------------------------------------------------------------------------- #
# Encabezado / pie con número de página.
# --------------------------------------------------------------------------- #
def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVu", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, A4[1] - 1.1 * cm,
                      "Algoritmos Evolutivos I (2026) · MIA · FIUBA — Desafío Práctico")
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.1 * cm, "Push/Fold con GA")
    canvas.line(2 * cm, A4[1] - 1.25 * cm, A4[0] - 2 * cm, A4[1] - 1.25 * cm)
    canvas.drawString(2 * cm, 1.1 * cm, REPO_URL)
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Página {doc.page}")
    canvas.restoreState()


# --------------------------------------------------------------------------- #
# Contenido.
# --------------------------------------------------------------------------- #
def build_story(styles, author):
    S = styles
    story = []

    # --- Portada / encabezado ---
    story.append(P("Optimización de un rango de <i>push/fold</i> en póker "
                   "heads-up con un Algoritmo Genético", S["TitleBig"]))
    story.append(P("Desafío Práctico — Algoritmos Evolutivos I (2026)", S["Sub"]))
    story.append(P("Maestría en Inteligencia Artificial — Facultad de Ingeniería, "
                   "Universidad de Buenos Aires", S["Sub"]))
    story.append(P(f"Autor: {escape(author)} &nbsp;·&nbsp; Técnica: Algoritmos "
                   f"Genéticos (GA)", S["Sub"]))
    story.append(P(f'Repositorio con el código fuente: <font name="DejaVuMono">'
                   f'{REPO_URL}</font>', S["Sub"]))
    story.append(Spacer(1, 8))

    # --- Resumen ---
    story.append(P("Resumen", S["H2"]))
    story.append(P(
        "Se aplica un Algoritmo Genético a un problema real de teoría de juegos del "
        "póker: hallar la estrategia óptima de <i>push/fold</i> (ir all-in o retirarse) "
        "en Texas Hold'em <i>heads-up</i> con stacks cortos. La estrategia se codifica "
        "como un cromosoma binario de 169 bits —uno por cada mano inicial distinta— y "
        "se evalúa con un modelo de valor esperado construido sobre <i>equities</i> "
        "reales de póker. El GA converge de forma estable al óptimo, que en esta "
        "formulación se conoce analíticamente y se usa para validar el resultado: la "
        "solución hallada coincide con él en las 169 manos.", S["Body"]))

    # --- 1. Problema ---
    story.append(P("1. El problema", S["H1"]))
    story.append(P(
        "En Texas Hold'em <i>heads-up</i> (un jugador contra otro) con stacks cortos, "
        "la teoría de juegos muestra que la estrategia óptima antes del flop se reduce "
        "a una decisión binaria del botón / ciega chica (SB): <b>ir all-in (push) o "
        "retirarse (fold)</b>. Jugar «push o fold» evita las decisiones posteriores "
        "(flop, turn, river), que con stacks cortos aportan poco valor y mucho riesgo, "
        "y por eso es la forma en que se juega y se estudia esta etapa del torneo.",
        S["Body"]))
    story.append(P(
        "El jugador debe decidir, para <b>cada una de las 169 manos iniciales</b> "
        "estratégicamente distintas (13 pares, 78 <i>suited</i> y 78 <i>offsuit</i>), "
        "si la pushea o la foldea. Esa decisión conjunta es un <i>rango de push</i>, y "
        "existen 2¹⁶⁹ ≈ 7,5·10⁵⁰ rangos posibles: un espacio de búsqueda enorme, "
        "imposible de recorrer por fuerza bruta e ideal para una metaheurística como un "
        "Algoritmo Genético.", S["Body"]))
    story.append(P(
        "La elección del GA es natural porque el rango se representa directamente como "
        "un <b>vector binario de 169 bits</b> (1 = push, 0 = fold), que es exactamente "
        "el cromosoma de un GA binario clásico.", S["Body"]))

    # --- 2. Modelo y fitness ---
    story.append(P("2. Modelo del juego y función de <i>fitness</i>", S["H1"]))
    story.append(P(
        "Con un stack efectivo de S <i>big blinds</i> (BB), ciega chica 0,5 y ciega "
        "grande 1, el valor esperado (EV) de la SB en cada resultado es:", S["Body"]))
    ev_table = Table([
        [P("<b>Acción de la SB</b>", S["Body"]), P("<b>Resultado</b>", S["Body"]),
         P("<b>EV (BB)</b>", S["Body"])],
        [P("Fold", S["Body"]), P("pierde su ciega chica", S["Body"]),
         P("−0,5", S["Body"])],
        [P("Push y la BB foldea", S["Body"]), P("se lleva la ciega grande", S["Body"]),
         P("+1,0", S["Body"])],
        [P("Push y la BB paga", S["Body"]), P("showdown all-in", S["Body"]),
         P("S·(2·eq − 1)", S["Body"])],
    ], colWidths=[5 * cm, 6.5 * cm, 4 * cm])
    ev_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce9f2")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b0b0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(ev_table)
    story.append(Spacer(1, 6))
    story.append(P(
        "donde <i>eq</i> es la <i>equity</i> (probabilidad de ganar el showdown) del "
        "héroe contra la mano del villano. Para cada mano h del héroe, promediando "
        "sobre el rango con el que la BB paga:", S["Body"]))
    story.append(P("EV_push(h) = Σⱼ wⱼ · [ cⱼ · S·(2·eq_hⱼ − 1) + (1 − cⱼ)·1 ] "
                   "&nbsp;&nbsp;&nbsp; EV_fold = −0,5", S["Formula"]))
    story.append(P(
        "donde j recorre las 169 clases del villano, wⱼ es la probabilidad a priori de "
        "esa clase y cⱼ ∈ {0,1} indica si la BB paga con ella. El <i>fitness</i> de un "
        "cromosoma x (ganancia esperada por mano) es:", S["Body"]))
    story.append(P("fitness(x) = Σₕ wₕ · [ xₕ · EV_push(h) + (1 − xₕ) · EV_fold ]",
                   S["Formula"]))
    story.append(P(
        "El siguiente fragmento (de <font name=\"DejaVuMono\">src/pushfold/game.py</font>) "
        "vectoriza el cálculo de EV_push contra el rango fijo de la BB:", S["Body"]))
    story.append(code(
        "def _compute_ev_push(self):\n"
        "    S = self.stack_bb\n"
        "    w = self.weights                       # prob. a priori de cada mano\n"
        "    call = self.bb_call_mask.astype(float) # 1 si la BB paga con esa mano\n"
        "    fold = 1.0 - call\n"
        "    showdown = S * (2.0 * self.equity - 1.0)      # EV all-in héroe vs villano\n"
        "    ev_when_called = (showdown * (w * call)).sum(axis=1)\n"
        "    ev_when_folded = 1.0 * float((w * fold).sum()) # gana la ciega grande\n"
        "    return ev_when_called + ev_when_folded", S))
    story.append(P(
        "Como el rango de la BB es fijo, EV_push(h) no depende de las demás manos: el "
        "problema es <b>separable</b> y su óptimo se conoce en forma cerrada —pushear si "
        "y solo si EV_push(h) &gt; EV_fold—. Ese óptimo analítico se usa como verdad de "
        "referencia para validar la convergencia del GA.", S["Body"]))

    # --- 3. El GA ---
    story.append(P("3. El Algoritmo Genético", S["H1"]))
    story.append(P(
        "Se implementó un GA binario clásico con los operadores estándar. Cada individuo "
        "es un vector de 169 bits y la población, una matriz (tamaño_población × 169).",
        S["Body"]))
    story.append(P(
        "<b>Selección por torneo</b> (tamaño 3): se eligen 3 individuos al azar y gana "
        "el de mayor fitness. <b>Cruza uniforme</b>: cada gen del hijo se hereda de uno "
        "u otro padre. <b>Mutación bit-flip</b>: cada gen se invierte con probabilidad "
        "≈ 1/169 (≈ 1 bit esperado por cromosoma). <b>Elitismo</b>: los 2 mejores pasan "
        "intactos, lo que garantiza que el mejor fitness nunca empeore (curva de "
        "convergencia monótona).", S["Body"]))
    story.append(P("Núcleo del bucle evolutivo "
                   "(<font name=\"DejaVuMono\">src/pushfold/ga.py</font>):", S["Body"]))
    story.append(code(
        "for gen in range(config.n_generations):\n"
        "    new_pop = np.empty_like(pop)\n"
        "    elite = np.argsort(-fitness)[:config.elitism]   # elitismo\n"
        "    new_pop[:config.elitism] = pop[elite]\n"
        "    for i in range(config.elitism, config.pop_size):\n"
        "        p1 = _tournament_select(pop, fitness, k, rng)\n"
        "        p2 = _tournament_select(pop, fitness, k, rng)\n"
        "        child = _uniform_crossover(p1, p2, cx_rate, rng)\n"
        "        new_pop[i] = _mutate(child, mut_rate, rng)  # bit-flip\n"
        "    pop = new_pop\n"
        "    fitness = fitness_fn(pop)                       # fitness vectorizado", S))
    params = Table([
        [P("<b>Parámetro</b>", S["Body"]), P("<b>Valor</b>", S["Body"])],
        [P("Tamaño de población", S["Body"]), P("80", S["Body"])],
        [P("Generaciones", S["Body"]), P("120", S["Body"])],
        [P("Prob. de cruza", S["Body"]), P("0,9", S["Body"])],
        [P("Prob. de mutación", S["Body"]), P("1/169 por gen", S["Body"])],
        [P("Torneo / Elitismo", S["Body"]), P("3 / 2", S["Body"])],
    ], colWidths=[7 * cm, 4 * cm])
    params.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce9f2")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b0b0")),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(params)

    # --- 4. Metodología ---
    story.append(P("4. Metodología experimental", S["H1"]))
    story.append(P(
        "La pieza de datos central es una <b>matriz 169×169 de equity all-in preflop</b>: "
        "equity[i][j] es la probabilidad de que la mano i gane el showdown contra la j "
        "con las 5 cartas comunitarias repartidas al azar. Se estima por Monte Carlo con "
        "el evaluador de manos en C <font name=\"DejaVuMono\">eval7</font> (25.000 "
        "repartos por matchup), respetando el <i>card removal</i>, y se precomputa una "
        "sola vez (≈25 s) guardándola en el repositorio. Como el GA y el óptimo analítico "
        "se calculan sobre esa misma matriz, la validación es exacta con independencia del "
        "pequeño ruido de estimación.", S["Body"]))
    story.append(P(
        "Los experimentos usan un stack efectivo de 10 BB y una BB que paga con el 50% de "
        "las manos más fuertes (rival fijo). Para medir robustez se corre el GA con 30 "
        "semillas independientes.", S["Body"]))

    # --- 5. Resultados ---
    story.append(P("5. Resultados", S["H1"]))
    story.append(P(
        "El GA converge de forma estable al óptimo analítico: coincide con él en las "
        "<b>169/169 manos</b> y alcanza un fitness de 0,0149 BB/mano, pusheando el 43% de "
        "las manos. La Figura 1 muestra la curva de convergencia (entregable obligatorio): "
        "el mejor y el promedio de la población suben hasta estabilizarse en el óptimo.",
        S["Body"]))
    story += figure(os.path.join(IMG, "convergencia.png"), S,
                    "Figura 1. Convergencia del GA: mejor y promedio de la población por "
                    "generación, con el óptimo analítico de referencia.")
    story.append(P(
        "Como el problema es separable, todas las corridas terminan alcanzando el óptimo. "
        "Para que el diagrama de caja sea informativo, la Figura 2 muestra el fitness "
        "final a distintos presupuestos de generaciones (15/30/60/120) sobre las 30 "
        "corridas: al aumentar el presupuesto, la mediana sube hacia el óptimo y la "
        "dispersión entre corridas se reduce, evidenciando la fiabilidad del método.",
        S["Body"]))
    story += figure(os.path.join(IMG, "boxplot.png"), S,
                    "Figura 2. Diagrama de caja del fitness final vs. presupuesto de "
                    "generaciones (30 corridas independientes).", width=13 * cm)
    story.append(P(
        "Finalmente, la Figura 3 presenta el cromosoma ganador como la clásica grilla "
        "13×13 de manos (verde = push, gris = fold). El rango obtenido tiene pleno sentido "
        "pokerístico: se pushean todos los pares, cualquier mano con un as o un rey (incluso "
        "K2), las manos altas (<i>broadways</i>) y algunos conectores <i>suited</i>. Que "
        "manos débiles como K2 entren se explica por el modelo de EV: con la BB foldeando "
        "casi la mitad de las veces y la ciega chica ya posteada, empujar pierde menos que "
        "rendirse. No hay ninguna celda marcada en rojo, es decir, no hay diferencias con "
        "el óptimo analítico.", S["Body"]))
    story += figure(os.path.join(IMG, "rango.png"), S,
                    "Figura 3. Rango de push evolucionado (stack 10 BB). Verde = push, "
                    "gris = fold; borde rojo marcaría diferencias con el óptimo (ninguna).",
                    width=11.5 * cm)

    # --- 6. Inconvenientes ---
    story.append(P("6. Inconvenientes encontrados y cómo se resolvieron", S["H1"]))
    story.append(P(
        "<b>a) Costo de calcular las equities.</b> Estimar por Monte Carlo en Python puro "
        "las equities de las 169×169 combinaciones era demasiado lento (no terminaba en "
        "minutos). Se resolvió delegando la evaluación de manos al evaluador en C "
        "<font name=\"DejaVuMono\">eval7</font> y, sobre todo, <b>precomputando la matriz "
        "una sola vez</b> y versionándola en el repositorio; así el GA corre después solo "
        "con NumPy, en segundos.", S["Body"]))
    story.append(P(
        "<b>b) Advertencias espurias de <font name=\"DejaVuMono\">matmul</font>.</b> En "
        "macOS con Apple Accelerate y NumPy 2.0, el producto matriz-vector emitía "
        "<i>warnings</i> de <i>divide-by-zero/overflow</i> pese a devolver el resultado "
        "correcto (se verificó comparando contra el producto calculado a mano). Se "
        "reemplazó el <font name=\"DejaVuMono\">matmul</font> por una reducción "
        "<i>elementwise</i> equivalente, que no dispara el problema en ningún backend.",
        S["Body"]))
    story.append(P(
        "<b>c) Diagrama de caja degenerado.</b> Al ser el problema separable, las 30 "
        "corridas alcanzaban exactamente el mismo óptimo y el box plot colapsaba a un "
        "punto, sin información. Se replanteó para mostrar el fitness final a distintos "
        "presupuestos de generaciones, que sí exhibe dispersión y comunica la velocidad "
        "de convergencia (Figura 2).", S["Body"]))

    # --- 7. Conclusiones ---
    story.append(P("7. Conclusiones y trabajo futuro", S["H1"]))
    story.append(P(
        "El Algoritmo Genético resolvió con éxito el problema de <i>push/fold</i>: "
        "codificando la estrategia como 169 bits y evaluándola con un modelo de EV sobre "
        "equities reales, converge de forma estable y reproducible al óptimo, validado "
        "contra su solución analítica (0/169 manos de diferencia). El resultado no solo es "
        "correcto numéricamente sino interpretable: reproduce un rango de all-in con "
        "sentido para cualquier jugador de póker.", S["Body"]))
    story.append(P(
        "La principal limitación es que el rival (rango de call de la BB) es fijo, lo que "
        "vuelve el problema separable. La extensión natural es <b>coevolucionar</b> los "
        "rangos de push de la SB y de call de la BB como un juego de suma cero, para "
        "aproximar el <b>equilibrio de Nash</b> de push/fold; allí el problema deja de ser "
        "separable y el Algoritmo Genético cobra un rol más rico como buscador de "
        "equilibrios. El código completo, la notebook reproducible en Google Colab y las "
        "instrucciones están en el repositorio enlazado más abajo.", S["Body"]))

    # --- Enlaces (al pie del documento) ---
    story.append(Spacer(1, 10))
    colab_url = ("https://colab.research.google.com/drive/"
                 "1y-XuN03sDg1YcVJO2KtwqX7zpu5MHd1E?usp=sharing")
    links = Table([
        [P("<b>Repositorio (código fuente)</b>", S["Body"]),
         P(f'<font name="DejaVuMono" size="9"><a href="{REPO_URL}" '
           f'color="#12507a">{REPO_URL}</a></font>', S["Body"])],
        [P("<b>Notebook reproducible (Colab)</b>", S["Body"]),
         P(f'<font name="DejaVuMono" size="7.5"><a href="{colab_url}" '
           f'color="#12507a">{colab_url}</a></font>', S["Body"])],
    ], colWidths=[5 * cm, 10.5 * cm])
    links.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef3f7")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#12507a")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c5d5e2")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(links)

    return story


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", default="[Completar nombre del/la estudiante]")
    parser.add_argument("--out", default=os.path.join(ROOT, "docs",
                                                       "AE1-pushfold-GA-informe.pdf"))
    args = parser.parse_args()

    register_fonts()
    styles = build_styles()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    doc = SimpleDocTemplate(
        args.out, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="Push/Fold con GA — Algoritmos Evolutivos I 2026",
        author=args.author,
    )
    doc.build(build_story(styles, args.author),
              onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"PDF generado: {args.out}")


if __name__ == "__main__":
    main()
