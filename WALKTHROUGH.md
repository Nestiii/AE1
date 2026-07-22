# Walkthrough: cómo funciona este proyecto, paso a paso

> Una explicación pensada para **cualquier persona**, sin necesidad de saber de
> algoritmos evolutivos ni de programación. La idea es entender *qué* hacemos, *por qué*
> y *cómo* llegamos al resultado, sin meternos en las cuentas finas.

---

## La idea en 30 segundos

Queremos encontrar la **mejor forma de jugar** una situación concreta de póker. En vez
de calcularla a mano, dejamos que una idea prestada de la **naturaleza** la descubra
sola: creamos muchas estrategias al azar, dejamos que "sobrevivan" las mejores, que se
"reproduzcan" y "muten", y repetimos ese ciclo muchas veces. Generación tras generación,
las estrategias mejoran hasta dar con la óptima. A eso se lo llama **Algoritmo Genético**.

Piensen en la evolución de las especies, pero aplicada a estrategias de póker y acelerada
a miles de "años" por segundo dentro de la computadora.

---

## Parte 1 — El problema, en lenguaje humano

### El póker de la situación

Imaginen una partida de póker **uno contra uno** (en la jerga, *heads-up*) donde a los
dos jugadores les quedan **pocas fichas**. Cuando el stack (las fichas que tenés) es
chico, jugar con matices —apostar poco, ver cartas, farolear— casi no tiene sentido: el
riesgo es alto y el margen para maniobrar, mínimo.

Por eso, con pocas fichas, la jugada se reduce a una **decisión de sí o no**:

- **Push** → apostar *todas* las fichas de una (ir "all-in").
- **Fold** → tirar la mano y no jugar.

El jugador recibe sus dos cartas y, sin más vueltas, decide: **¿push o fold?**

### ¿Por qué es un problema interesante?

Porque no da igual con qué cartas hacés cada cosa. Con un par de ases, obviamente vas
all-in. Con un 7 y un 2 de distinto palo (la peor mano del póker), obviamente tirás. ¿Pero
qué hacés con las manos "del medio", como una jota con un diez? Ahí está la gracia.

En el póker hay **169 tipos de mano inicial distintos** (contando pares, cartas del mismo
palo y de distinto palo). Una **estrategia completa** es una decisión —push o fold— para
*cada una* de esas 169 manos.

¿Cuántas estrategias posibles hay? Como cada mano tiene 2 opciones y son 169 manos, el
total es **2¹⁶⁹**, un número con más de **50 cifras**. Para dimensionarlo: es
muchísimo más grande que la cantidad de átomos que hay en la Tierra. **Probarlas todas
una por una es imposible**, ni con todas las computadoras del mundo.

Y acá aparece la pregunta central del proyecto:

> Entre esas 2¹⁶⁹ estrategias posibles, ¿cuál es la que más fichas gana a la larga?

Buscar la mejor aguja en un pajar tan gigante es justo el tipo de problema donde brillan
los **algoritmos evolutivos**.

---

## Parte 2 — ¿Qué es un Algoritmo Genético?

Es una técnica de búsqueda inspirada en la **selección natural** de Darwin. En lugar de
razonar la respuesta, la hacemos *evolucionar*. Los ingredientes son los mismos que en la
biología:

| En la naturaleza | En nuestro algoritmo |
|---|---|
| Un **individuo** (un bicho) | Una **estrategia** de póker |
| Su **ADN** (cromosoma) | La lista de 169 decisiones push/fold |
| Una **población** | Un montón de estrategias conviviendo |
| Qué tan **apto** es para sobrevivir | Cuántas **fichas gana** la estrategia |
| **Reproducción** (los hijos heredan rasgos) | Combinar dos estrategias buenas en una nueva |
| **Mutación** (cambios al azar en el ADN) | Cambiar alguna decisión suelta al azar |
| Una **generación** | Una vuelta completa del ciclo |

La regla de oro es la misma que en la evolución: **los más aptos tienen más chances de
dejar descendencia**. Si repetimos el ciclo muchas veces, la población entera va
mejorando, porque las buenas características se acumulan y las malas se descartan.

Lo importante: el algoritmo **no sabe nada de póker**. Solo sabe comparar estrategias por
cuántas fichas ganan y aplicar estas reglas de "supervivencia del más apto". Aun así,
termina descubriendo una forma de jugar muy sensata. Eso es lo fascinante.

---

## Parte 3 — Cómo lo resolvimos, paso a paso

### Paso 0 — Preparar un "árbitro" que sepa quién gana

Antes de que el algoritmo empiece a evolucionar, necesitamos algo que le diga, para
cualquier enfrentamiento de cartas, **qué tan probable es ganar**. Por ejemplo: un par de
ases le gana a un par de reyes el **82%** de las veces.

Calculamos por adelantado una **gran tabla** con la probabilidad de ganar de cada mano
contra cada otra (169 × 169 combinaciones). La calculamos una sola vez —simulando
repartos de cartas muchísimas veces— y la guardamos. A partir de ahí, el algoritmo la
consulta al instante, como quien mira un vademécum. Este árbitro es lo que en el proyecto
llamamos la **matriz de equity**.

### Paso 1 — Escribir una estrategia como una lista de ceros y unos

Cada estrategia se representa como una **grilla de 169 casilleros**, uno por cada tipo de
mano. En cada casillero ponemos:

- **1** si con esa mano vamos a hacer **push** (all-in), o
- **0** si vamos a hacer **fold** (tirar).

Esta grilla es exactamente el "ADN" de la estrategia. Los jugadores de póker ya usan este
tipo de tablas 13×13 para estudiar; acá simplemente la volvemos números que la computadora
puede manipular.

### Paso 2 — Medir qué tan buena es una estrategia (el "fitness")

Para comparar estrategias necesitamos un puntaje. El nuestro es muy natural:

> **¿Cuántas fichas gana (o pierde), en promedio, esta estrategia por cada mano jugada?**

Para calcularlo, recorremos las 169 manos y, según lo que diga la grilla (push o fold),
sumamos las fichas que se esperan ganar o perder en cada caso, usando el "árbitro" del
Paso 0 y teniendo en cuenta con qué manos nos paga el rival. El resultado es un único
número: el **fitness**. Cuanto más alto, mejor la estrategia. Ese es el puntaje que el
algoritmo intenta maximizar.

### Paso 3 — Arrancar con una población al azar

Creamos **80 estrategias completamente aleatorias** (grillas de 169 ceros y unos puestos
a los tumbos). Casi todas van a ser malísimas —hacen all-in con basura y tiran manos
buenas—, y eso está perfecto: son el "caldo primitivo" del que va a partir la evolución.

### Paso 4 — El ciclo de una generación

Acá pasa la magia. Con la población actual hacemos cuatro cosas:

1. **Selección (los más aptos "sobreviven").** Elegimos parejas de estrategias para que
   se reproduzcan, favoreciendo a las de mayor fitness. Usamos un mini-torneo: tomamos
   unas pocas al azar y gana la mejor. Las buenas se eligen más seguido.

2. **Cruza (reproducción).** De cada pareja de "padres" nace una estrategia "hija" que
   hereda algunas decisiones de uno y otras del otro. La idea es que combinar dos
   estrategias buenas pueda dar una todavía mejor.

3. **Mutación (variación al azar).** A la hija le cambiamos alguna decisión suelta al azar
   (un casillero que estaba en push pasa a fold o viceversa). Esto introduce novedad y
   evita que la población se estanque copiándose siempre lo mismo.

4. **Elitismo (no perder lo mejor).** Nos aseguramos de que las **2 mejores** estrategias
   de la generación pasen intactas a la siguiente. Así garantizamos que nunca demos un
   paso atrás: la mejor solución encontrada jamás empeora.

El resultado de estos cuatro pasos es una **nueva generación** de 80 estrategias, en
promedio un poquito mejores que las anteriores.

### Paso 5 — Repetir muchas veces

Repetimos el Paso 4 **120 veces** (120 generaciones). Al principio las mejoras son
enormes (partíamos de puro azar); después, cada vez más finas, hasta que la población deja
de mejorar porque ya encontró la mejor forma de jugar. En ese punto, **paramos**.

### Paso 6 — Verificar que la respuesta sea la correcta

¿Cómo sabemos que lo que encontró el algoritmo es de verdad lo óptimo y no "lo mejor que
pudo"? En esta versión del problema hay una ventaja: como el rival juega de una forma
fija, la respuesta perfecta se puede **calcular directamente con una cuenta** (mano por
mano, conviene ir all-in solo si eso gana más fichas que tirar).

Entonces comparamos la estrategia que evolucionó el algoritmo contra esa respuesta
calculada. Y coinciden en **las 169 manos**: el Algoritmo Genético llegó, solo y sin
saber póker, exactamente a la jugada óptima. Esa es nuestra prueba de que todo funciona.

---

## Parte 4 — Cómo leer los resultados

El proyecto produce tres gráficos. Así se interpretan.

### 1. La curva de convergencia — "cómo aprende el algoritmo"

![Convergencia](docs/img/convergencia.png)

El eje horizontal son las generaciones (el paso del tiempo) y el vertical, el fitness
(fichas ganadas por mano; **más arriba es mejor**). Se ve cómo las estrategias arrancan
muy abajo (perdiendo fichas, porque son al azar) y **suben rápido** hasta pegarse a la
línea punteada verde, que marca la jugada óptima. Esa forma de "subida que se aplana" es
la firma típica de un algoritmo que **converge**: mejora mucho al principio y después se
estabiliza en la mejor respuesta.

### 2. El diagrama de caja — "qué tan confiable es"

![Box plot](docs/img/boxplot.png)

Corrimos el experimento **30 veces** (cada una arranca de un azar distinto) y miramos qué
tan bien le va según cuántas generaciones la dejemos correr (15, 30, 60, 120). Cada
"caja" resume esas 30 corridas. Se ve que, con **más generaciones**, las cajas suben hacia
la línea óptima y se vuelven **más chiquitas**: no solo mejora el promedio, sino que
**todas** las corridas terminan dando lo mismo. En criollo: el método es **consistente**,
no depende de tener suerte.

### 3. La grilla de la estrategia — "el resultado, en idioma póker"

![Rango](docs/img/rango.png)

Esta es la estrategia ganadora traducida de vuelta al póker. En verde, las manos con las
que conviene ir **all-in**; en gris, las que conviene **tirar**. El resultado tiene todo
el sentido del mundo para cualquier jugador: se va all-in con **todos los pares**, con
**cualquier mano que tenga un as o un rey** (sí, incluso K2), con las manos altas
(*broadways*) y con algunos conectores del mismo palo; y se tiran las manos bajas y
descoordinadas. Que hasta K2 entre no es porque sea fuerte, sino porque, con el rival
foldeando casi la mitad de las veces y habiendo ya posteado la ciega, **rendirse pierde
todavía más**. En total, se hace push con alrededor del **43%** de las manos. El algoritmo
redescubrió, por su cuenta, una tabla que los jugadores tardaron años en pulir.

---

## Parte 5 — Qué aprendimos (y qué falta)

**Lo importante:** un procedimiento que solo sabe "quedarse con lo mejor y variar un
poco", repetido muchas veces, es capaz de resolver un problema con más combinaciones
posibles que átomos en el planeta, y llegar a una respuesta **correcta y con sentido**.
Esa es la potencia de los algoritmos evolutivos.

**La limitación honesta:** en esta versión el rival juega de una forma **fija**. Eso hace
el problema más sencillo (por eso pudimos verificar la respuesta con una cuenta directa).
El paso siguiente, más ambicioso, sería que **los dos jugadores evolucionen a la vez**,
adaptándose el uno al otro, hasta encontrar un punto de equilibrio en el que ninguno pueda
mejorar cambiando su estrategia (lo que en teoría de juegos se llama **equilibrio de
Nash**). Ahí el problema se vuelve mucho más rico y el algoritmo evolutivo se luce todavía
más.

---

## Mapa mental para recordarlo

```
        169 decisiones push/fold  =  una estrategia (el "ADN")
                     │
        80 estrategias al azar     =  la población inicial
                     │
   ┌─────────────► repetir 120 veces ◄─────────────┐
   │                                               │
   │   1. seleccionar las mejores (fitness)        │
   │   2. cruzarlas  → estrategias hijas           │
   │   3. mutar un poco al azar                    │
   │   4. conservar las 2 mejores (elitismo)       │
   │                                               │
   └───────────────────► ↑ ──────────────────────┘
                     │
        la población converge a la mejor jugada
                     │
        verificamos: coincide con la respuesta óptima  ✓
```

---

*Para el detalle técnico completo (fórmulas, código y decisiones de implementación), ver
el [README](README.md), el [informe en PDF](docs/AE1-pushfold-GA-informe.pdf) y el código
comentado en [`src/pushfold/`](src/pushfold/).*
