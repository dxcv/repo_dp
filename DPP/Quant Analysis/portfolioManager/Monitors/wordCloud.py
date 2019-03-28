"""
Created on Mon Feb 29 09:58:23 2016

@author: ngoldberger
"""

import newspaper
import numpy as np
from PIL import Image
from os import path
import matplotlib.pyplot as plt
import random

from bs4 import BeautifulSoup
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

class news(object):

    def __init__(self):
        self.headlines = {}

    def getNews(self, url = {'http://www.bloomberg.com': 'top-news-v3__story__headline__link',
                             'http://www.bloomberg.com/markets':'two-up-story__headline-link module-headline-link',
                             'http://www.bloomberg.com/markets':'three-up-story__headline-link module-headline-link',
                             'http://www.wsj.com/news/economy': 'subPrev headline',
                             'http://www.ft.com/intl/markets': 'ft-link ',
                             'http://www.businessinsider.com/clusterstock': 'title'}):
        self.text = []
        for i in range(0, len(url)):
            self.url = url.keys()[i]
            self.clas = url[self.url]
            self.structure = newspaper.build(self.url)
            self.html = self.structure.html
            self.soup = BeautifulSoup(self.html)
            for link in self.soup.find_all('a', class_=self.clas):
                    self.headlines.update({link.text:link.get('href')})
#            self.text += self.headlines.keys()
            self.text = {'1. Antecedentes y opciones Tanto la minuta de antecedentes como la presentacion preparada por la Gerencia de Division Estudios, basadas en informacion publicamente disponible, pueden ser consultadas en la pagina web del Banco1 /. Desde la publicacion del Informe de Politica Monetaria (IPoM) de septiembre, la principal preocupacion de corto plazo del escenario externo seguia siendo los efectos que pudieran tener los anuncios que hiciera la Reserva Federal de EE.UU. (Fed) en su reunion de septiembre. Sin desconocer que la probabilidad de escenarios disruptivos no era despreciable, la evaluacion mas razonable seguia siendo considerar un escenario donde, mas alla de la volatilidad de corto plazo, las condiciones financieras internacionales continuarian siendo holgadas y la actividad global seria algo mayor que lo observado en lo mas reciente. Esto, en linea con el escenario base del IPoM, que consideraba que la Fed subiria una vez las tasas este año y dos en el que sigue, y que estos movimientos no generarian disrupciones mayores y persistentes en los mercados financieros. En particular, no se esperaban reversiones significativas y duraderas de los premios por plazo y, por lo tanto, no habria cambios muy significativos en las tasas largas. En todo caso, la materializacion de un escenario distinto constituia un riesgo relevante. Con todo, la respuesta de la Tasa de Politica Monetaria (TPM) a cambios en la politica monetaria de EE.UU. distaba de ser mecanica. Dependia, principalmente, de su impacto en las proyecciones de inflacion de mediano plazo, el que, a priori, no era evidente. En lo interno, entre el cierre estadistico del IPoM y el de esta Reunion, se habia conocido el IMACEC de julio y la inflacion de agosto, ambos en linea con el escenario base del IPoM. La inflacion anual del IPC descendia desde 4 a 3,4%, ubicandose con claridad dentro del rango de tolerancia. La significativa caida de la inflacion anual se relacionaba mas con un efecto base que con un cambio material en la trayectoria del nivel de precios. La convergencia de la inflacion continuaba impulsada principalmente por la disminucion de la inflacion de transables (IPCSAE bienes), toda vez que la inflacion de los no transables (IPCSAE servicios) descendia moderadamente. Esto, en linea con la vision de que la convergencia de la inflacion estaba principalmente asociada a la estabilidad del tipo de cambio y que la contribucion de las holguras de capacidad continuaria acotada. El valor del dolar continuaba bajo los niveles observados al cierre del IPoM de junio, aun tras la reciente depreciacion. El analisis indicaba que el menor tipo de cambio empujaria el IPCSAE por debajo de 3% durante parte importante del 2017. Sin embargo, la evidencia no sugeria efectos de segunda vuelta que pusieran en riesgo la convergencia a la meta en el horizonte de proyeccion. Por esta razon, el escenario base no consideraba una reaccion de la politica monetaria muy significativa por este respecto. Situacion que, por lo demas, era simetrica a la observada durante la depreciacion del peso ocurrida desde mediados del 2013. En ese periodo, a pesar del aumento de la inflacion, la TPM disminuyo, ya que se considero que no era necesario combatir los efectos transitorios de la depreciacion del peso sobre la inflacion. Obviamente, existia un escenario de riesgo donde la apreciacion del peso era mas intensa y persistente —por ejemplo, si la Fed terminaba con una politica monetaria mucho mas expansiva y generaba una reaccion en la misma linea de otros bancos centrales—, lo que podria producir efectos de segunda vuelta mayores. Una situacion similar, BANCO CENTRAL DE CHILE Reunion de Politica Monetaria 3 aunque en sentido contrario, habia sido lo ocurrido a fines del 2015, cuando se evaluo que, dada la mayor intensidad y persistencia de la depreciacion cambiaria, el impacto sobre la inflacion estaba siendo mayor y mas duradero. En un escenario de ese tipo se requeriria revisar la instancia de politica, pero, en este momento, no parecia lo suficientemente relevante como para determinar las opciones propuestas para esta Reunion. Por otra parte, el nivel actual del tipo de cambio real (TCR) era 4% superior al promedio de los ultimos veinte años, y se encontraba dentro de los rangos que se consideraban alineados con sus fundamentos. Respecto de la brecha de actividad, se consideraba que su nivel actual no era muy distinto del esperado hace un año, a pesar de que las proyecciones de crecimiento se habian recortado del orden de un punto porcentual en el ultimo año. Esto, porque, al mismo tiempo, el crecimiento del PIB potencial cayo en torno a 0,5 puntos porcentuales y, tras la revision extraordinaria de las Cuentas Nacionales, el crecimiento en 2015 del PIB resto, el relevante para el calculo de la brecha, habia sido mayor. Con todo, se proyectaba que hacia adelante la brecha se abriria con mayor rapidez, para empezar a cerrarse solo entrado el 2018. Dicha evolucion de la brecha, unida a la relativa baja elasticidad de la inflacion a esta variable, explicaba por que no se esperaba un cambio relevante de la inflacion de los no transables. En este contexto, el IPoM de septiembre habia ampliado el impulso monetario respecto de Informes previos. Asi, se proyectaba que, de darse el escenario base, no seria necesario aumentar la TPM durante el horizonte de proyeccion. Esto no solo implicaba un mayor impulso monetario respecto de lo previsto en junio, sino que tambien de lo considerado hace un año, cuando se habia usado como supuesto de trabajo una trayectoria que a fines del 2017 dejaba la TPM en 4,25%, 75 puntos base (pb) por sobre el supuesto de trabajo actual. Asi, la politica monetaria seguiria entregando un impulso relevante a la economia, lo que era evidente del hecho que las diferentes tasas de interes estaban en o muy cerca de sus minimos historicos, con una TPM entre 50 y 100pb bajo su nivel neutral. En este escenario, la Division Estudios consideraba que la opcion de mantener se erigia como la adecuada con los antecedentes presentados y con el analisis del ultimo IPoM. Ademas, era coherente con la vision promedio del mercado, como se desprendia de las encuestas recientes a economistas y a operadores financieros. Estas ubicaban las expectativas de TPM en 3,5% por un periodo prolongado, en un contexto de expectativas de inflacion bien ancladas en 3% y un escenario de actividad similar al del IPoM. Respecto de opciones alternativas, se considero apropiado, como era tradicional, volver a presentar dos opciones. Dados los antecedentes disponibles, era facil descartar un alza como opcion, puesto que nada sugeria la existencia de riesgos significativos de mayores presiones inflacionarias a mediano plazo. Por otro lado, las sucesivas correcciones a la baja en las proyecciones de crecimiento, el bajo nivel y nula mejora de los indicadores de confianza, asi como una inversion que no repuntaba, podian dar paso a un escenario alternativo al base, donde el crecimiento de la economia era significativamente menor que el previsto en el escenario base y tenia una probabilidad de ocurrencia no despreciable. Este escenario requeriria un impulso monetario adicional. Asi, en razon de los antecedentes presentados, la Division Estudios proponia analizar las opciones de mantener la TPM en 3,5% y la de recortarla a 3,25%. Sin embargo, consideraba que esta ultima debia ser desestimada, puesto que, como se habia discutido ampliamente durante el proceso de elaboracion del IPoM y en los antecedentes presentados para la Reunion, todo sugeria que el escenario base permanecia firme y hacia innecesarios cambios en la orientacion de la politica monetaria. Por esto, la Division Estudios recomendaba mantener la TPM en 3,5% y el sesgo neutro. 2. Decision de politica monetaria Todos los Consejeros destacaron los efectos que la incertidumbre sobre la decision que tomaria la Fed la proxima semana estaba provocando sobre los mercados. Un Consejero resalto que aunque no podia descartarse una actitud mas agresiva en los proximos trimestres, fruto de cifras significativamente mejores en EE.UU., el escenario de aumento muy gradual de la tasa en ese pais y de expansividad monetaria en las principales economias desarrolladas seguia siendo dominante. Un Consejero destaco que la inminencia de una nueva decision de la Fed hacia resaltar la brecha entre las opiniones de algunos de sus integrantes y las expectativas del mercado. Indico que en la medida que estas diferencias expresaban, en parte, interpretaciones diferentes sobre la situacion de la economia estadounidense y que se iba acortando el horizonte para los ajustes previstos por la Fed para el 2016, la importancia de esta reunion estribaba no solo en su implicancia inmediata sobre las tasas de interes, sino tambien sobre la trayectoria prevista para el 2017. Asi, la prevalencia de las favorables condiciones financieras de los ultimos meses, con su efecto sobre los tipos de cambio, los precios de las materias primas y los flujos de capitales hacia economias emergentes, se veria sometida a un importante test en las proximas BANCO CENTRAL DE CHILE Reunion de Politica Monetaria 4 semanas. Un Consejero indico que mas relevante que el momento mismo en que la Fed decidiera ajustar la tasa, era el tono del mensaje que acompañase a la decision. A su juicio, era probable que un tono de mantencion de alta gradualidad tranquilizara a los mercados. Un Consejero señalo que lo mas destacable del ambito internacional era la reversion de las bajas tasas de interes de largo plazo en el mundo desarrollado, mas alla de que su impacto en las variables financieras chilenas habia sido bastante acotado, en particular sobre el tipo de cambio. En terminos reales, este seguia por debajo de los niveles de principios de año, a pesar de los vaivenes en el entorno externo. Y a diferencia de otras monedas, habia tenido una reaccion bastante leve a la reversion de primas por plazo en el mundo. Ademas, y como habia sido la tonica en el ultimo tiempo, las tasas de interes de largo plazo en Chile tambien se mantenian bastante estables. Respecto del escenario interno, todos los Consejeros concordaron en que los datos del Imacec de julio y el IPC de agosto eran coherentes con el escenario base del IPoM de septiembre. Un Consejero resalto que la actividad economica habia crecido menos que lo anticipado por el mercado, lo que se explicaba, en parte, por una combinacion de choques puntuales de oferta en el sector industrial y el prolongado ajuste del sector minero. Ademas, agrego, los indicadores de demanda mantenian su debil, pero positivo, ritmo de crecimiento de meses anteriores. Un Consejero menciono que, en lo fundamental, las perspectivas para la demanda interna y la actividad economica seguian marcadas por un continuado retroceso de la mineria, la debilidad de la inversion y un consumo algo mas estable, asociado a la evolucion de la masa salarial. Todo ello, agrego, no era suficiente para prever un retroceso de la actividad en el tercer trimestre de este año ni para descartar una recuperacion gradual en el proximo, pero si ratificaba un escenario de crecimiento muy acotado, significativamente por debajo de la estimacion del PIB potencial, aun despues de la correccion de este ultimo a la baja. Con esto, indico, la brecha de actividad se continuaria ampliando, al menos hasta fines del proximo año. Mientras ello ocurriera, concluyo, dificilmente se recuperaria el mercado del trabajo, el que continuaria ajustandose en sus diversas dimensiones. Un Consejero destaco que las condiciones de demanda y actividad interna seguian dando cuenta de un dinamismo acotado, que deberia contribuir a una disminucion gradual de la inflacion de servicios. En su opinion, sin embargo, mientras no se visualizara un escenario de deterioro mayor en la actividad y de ajuste mas marcado que el esperado en el mercado laboral, era dificil prever una desaceleracion mas rapida e intensa de dicho componente del IPC. Asi, al igual que en los meses anteriores, las perspectivas de inflacion a mediano plazo continuaban ancladas a un escenario de crecimiento modesto, donde no se anticipaba una desaceleracion mas aguda. Ello mantenia la necesidad de una politica monetaria expansiva. Por otra parte, la limitada generacion de holguras, de la mano de un crecimiento potencial mas bajo, tambien justificaba una revaluacion sobre la tasa neutral, que se habia ajustado a la baja en las estimaciones internas. Añadio que la suma de estos elementos estaba detras de la correccion a la baja en la trayectoria de tasas que se habia considerado en el ultimo IPoM, por lo que creia que una trayectoria estable para la TPM daba cuenta de un grado adecuado de expansividad. Respecto de la inflacion, un Consejero resalto que la velocidad de convergencia de la inflacion a la meta era especialmente notoria al observar los indicadores de inflacion subyacente. En particular, la variacion del IPCSAE volveria a las inmediaciones del 3% casi en la mitad del tiempo que le tomo subir del mismo 3% a su maxima expansion en doce meses, a comienzos de este año. A su juicio, que esto ocurriera con una apreciacion real del peso inferior a la depreciacion precedente sugeria que la brecha de actividad estaba teniendo una influencia en el comportamiento de la inflacion, que, aunque menor que la del tipo de cambio, podria ampliarse en los proximos trimestres. Un Consejero destaco que la inflacion de agosto estuvo en linea con lo esperado y su variacion en doce meses habia entrado al rango de tolerancia. Agrego que se esperaba una cifra mayor en septiembre y que terminaria el año en 3,5%. Indico que si bien esta era una buena noticia luego de dos años de inflaciones sobre dicho rango, y que si bien las proyecciones indicaban que iria convergiendo gradualmente a 3%, era muy temprano para sacar una conclusion definitiva. Los riesgos seguian existiendo y el deber del Banco era seguir atento a ellos. La inflacion de servicios, aunque con una desaceleracion gradual, seguia elevada. El IPCSAE estaba cerca del limite superior del rango de tolerancia, pero se esperaba que siguiera bajando. Con todo, en general, el panorama inflacionario era coherente con el escenario base del IPoM. Respecto de las opciones presentadas por la Division Estudios, varios Consejeros estimaron que la opcion de baja era por lo menos prematura y descartable, entre otras razones, porque no habia informacion que sugiriera un desvio relevante respecto de lo planteado en el ultimo IPoM. Algunos Consejeros, por su parte, valoraron su inclusion dentro del menu de opciones a discutir. Respecto de la decision de politica monetaria, un Consejero manifesto que la informacion disponible era coherente con el escenario base del IPoM de BANCO CENTRAL DE CHILE Reunion de Politica Monetaria 5 septiembre y no significaba un cambio relevante en las proyecciones de inflacion alli incluidas. A su juicio, de por si, esto aconsejaba una decision de politica monetaria consecuente con el supuesto de trabajo de una TPM estable. Sin embargo, continuo, reconocia la validez de incluir una opcion de reduccion de la TPM en esta oportunidad. En su opinion, se justificaba porque la proyeccion de una inflacion total en torno a 3% consideraba que los precios mas volatiles —no SAE— elevarian la inflacion el proximo año, no asi el componente subyacente, que se mantendria por debajo de 3% durante parte importante del 2017. Mientras esto fuese asi y la brecha de actividad siguiera ampliandose, creia necesario mantener abierta la posibilidad de adoptar una politica monetaria mas acomodaticia. Todo ello no debia considerarse contradictorio con la convergencia de la TPM a un nivel neutral, compatible con la meta de inflacion en un contexto economico balanceado en el largo plazo. En cualquier caso, concluyo, como los riesgos de un ajuste inflacionario mas intenso de lo previsto seguian acotados, creia que lo adecuado en esta oportunidad era mantener la TPM en 3,5%, lo mismo que el supuesto de trabajo de mantencion de la misma por un tiempo prolongado, en concordancia con el IPoM de septiembre. Un Consejero menciono tres consideraciones al momento de evaluar las opciones que se presentaban. Primero, desde principios de julio, la curva swap señalaba una trayectoria que primero fue plana y luego consideraba una reduccion de 25pb dentro de los seis meses siguientes, lo que indicaba que el mercado habia incorporado bastante antes la posibilidad de una reduccion leve de la TPM. Las opiniones de analistas y las encuestas habian sido menos categoricas, quizas en respuesta al sesgo al alza que solo se habia cambiado a neutral el mes pasado. En su opinion, esto sugeria que, en un contexto en que se obviara el reciente IPoM, ninguna de las dos opciones serian sorpresivas. Segundo, considerando la reciente publicacion del lPoM, una reduccion de la TPM en esta Reunion seria bastante contradictoria, ya que sugeriria que el Imacec y el IPC recientes habian sido mas desinflacionarios de lo que proyectaba el IPoM, en circunstancias que nosotros mismos habiamos comentado publicamente que los datos estaban en linea con el. Alternativamente, y a su juicio mas razonable, dicho movimiento daria cuenta de que el escenario base del IPoM admitia una TPM algo inferior a 3,5% sin producir cambios importantes en el. Esto, porque habia una incertidumbre razonable sobre la trayectoria mas eficiente para la TPM en un escenario base dado. La decision de reducir la TPM hoy deberia enmarcarse en este ultimo argumento, el que era dificil de explicar en el contexto de un breve Comunicado. Ademas, este debate, aunque legitimo, requeria de una conceptualizacion y discusion interna mayor. Por ultimo, una tercera consideracion sobre las opciones era la de realizar una discusion basada en gestion de riesgos. Era evidente que si la economia mostraba presiones desinflacionarias mayores en trimestres venideros, un relajamiento monetario adicional seria aconsejable. Incluso se podria actuar de forma preventiva frente a dicha situacion reduciendo la TPM ahora, si se consideraba que seria mas dificil actuar mas agresivamente en el futuro. Como no consideraba validos dichos impedimentos, tampoco creia necesario actuar de forma preventiva ahora. Un Consejero señalo que la informacion disponible desde la publicacion del IPoM era minima y no alteraba el escenario alli descrito. La inflacion habia bajado, tal como se esperaba, y las noticias parecian coherentes con una trayectoria suavemente descendente de la inflacion en los meses venideros, tambien en linea con lo proyectado. En este contexto, creia que lo decision correcta era mantener la TPM en 3,5%, lo mismo que el tenor del Comunicado. En relacion con las opciones planteadas, concordaba que era dificil hacer un caso por un aumento de la TPM en esta Reunion. Respecto de la opcion de bajarla, creia que las opciones planteadas por la Division Estudios daban buenos argumentos para descartarla, por lo que no le parecia necesario abundar en la materia. Sin perjuicio de ello, estimaba que era poco probable que ocurriera un escenario en que se diera, simultaneamente, un deterioro mayor de la demanda y la actividad interna junto a menores presiones inflacionarias, ya que seguramente estos factores tambien incidirian en las primas por riesgo de Chile y, de esa manera, impactarian el tipo de cambio. Un Consejero indico que, en su opinion, la trayectoria de inflacion en los proximos trimestres seguia dependiendo de la trayectoria cambiaria. A su juicio, mas alla de la volatilidad y la incertidumbre al respecto, si las condiciones monetarias externas fueran aun mas expansivas y duraderas de lo que se anticipaba, se podria generar una caida algo mas rapida de la inflacion y, al mismo tiempo, un mayor soporte para el crecimiento del 2017. En ese escenario, resultaba clave preguntarse como debia reaccionar la politica monetaria frente a un aumento permanente del apetito por riesgo de emergentes, que era el fenomeno que podria estar subyacente a esta mayor apreciacion de la moneda y apetito por riesgo. Por un lado, una trayectoria de politica monetaria que mantuviera tasas estables haria recaer el ajuste mayoritariamente sobre el tipo de cambio, permitiendo una apreciacion mayor del peso. Por otro, una politica monetaria que acomodara las mejores condiciones externas con menores tasas evitaria una mayor apreciacion del tipo de cambio. La pregunta era como dilucidar esta disyuntiva. A su juicio, en el esquema actual —que consideraba optimo—, la politica monetaria debia anclar su decision en aquella trayectoria para la TPM que fuera coherente con una inflacion en 3% a mediano plazo, apuntando a la estabilizacion de las condiciones de demanda y actividad, y permitiendo la fluctuacion del tipo de cambio. La experiencia de los ultimos años daba cuenta de que, para una economia como la chilena, esto podia generar variaciones de la inflacion en torno a la meta que fueran duraderas por algunos BANCO CENTRAL DE CHILE Reunion de Politica Monetaria 6 trimestres, pero la politica monetaria no debia desviarse de sus objetivos de inflacion de mediano plazo. Por ello, en las circunstancias actuales, consideraba que la unica opcion valida en esta Reunion era mantener la TPM en 3,5%. Un Consejero destaco que la politica monetaria mantenia su expansividad y se esperaba que continuase asi en el futuro. Los esfuerzos por suavizar el ciclo en un ambiente de inflaciones por arriba de la meta ilustraban el esquema de politica monetaria del Banco, donde lo relevante era como se visualizaba la inflacion en el horizonte de proyeccion, y, por lo mismo, factores puntuales sin incidencia en las tendencias inflacionarias tenian un rol menor. Respecto de las opciones, por una parte, descartaba inmediatamente la de subir la TPM. Por otra, no le convencia del todo que bajar la TPM fuera una opcion valida en esta Reunion. Creia que, en este momento, no habia razones para pensar en un escenario distinto del considerado en el IPoM, por lo que una decision de este tipo no solo seria prematura, sino ademas dificilmente entendible por el mercado. Asi, concluyo, le parecia que la unica opcion razonable era la de mantener la TPM. No podia olvidarse que la inflacion de servicios seguia elevada y que las holguras de capacidad eran limitadas. Ademas, los efectos cambiarios no solo eran inciertos, sino que tenian impactos por una vez.'}

    def exportHeadlines(self, outputFile = 'Output'):
        text_file = open(outputFile + '.txt', "w")
        for news in self.text:
            text_file.write("%s\n" % news)
        text_file.close()

    def displayHeadlines(self):
        for news in self.text:
            print(news)

    def grey_color_func(self,word, font_size, position, orientation, random_state=None, **kwargs):
        return "hsl(0, 0%%, %d%%)" % random.randint(60, 100)

    def generateWordCloud(self, shape = 'splash.jpg'): # parrot.png is also available
        self.shape = shape
        self.d = path.dirname(__file__)
        # Read the mask image. Mask provides a figure for the Word Cloud
        mask = np.array(Image.open(path.join(self.d, self.shape)))
        # Read the text to create the cloud
        hlines = ''.join(self.text)
        # Preprocessing the text to replace words
        #text = text.replace("HAN", "Han")
        #text = text.replace("LUKE'S", "Luke")
        # Adding specific stopwords, these are words we will skip
        self.stopwords = STOPWORDS.copy()
        lista = '''million world est am market markets years picture label claims 
        see billion give trillion need year month new great gain thing returns
        need self top bottom leave upset price prices really must best auto
        made gets bid will things time hit says brings big wall call street
        pay missing report sees bank manager hedge fund rate sets next since
        set going now crazy looks study back en la de por tica sobre como el
        un que ha es ciento esto se ser ger sido son otra si no o esta una
        un Y y de del lo para las con pol este todo mas los al os le han ello
        entre hay hemos muy pero tambien dos su sus sin desde hacia hace asi
        nuestra sera dia eso era'''.split()
        for palabra in lista:
            self.stopwords.add(palabra)

        # The actual creation of the cloud
        self.wc = WordCloud(background_color = (48,48,48), max_words = 1000,
                            mask = mask, stopwords = self.stopwords, margin = 10,
                            random_state = 42).generate(hlines)
        image_colors = ImageColorGenerator(mask)
        # Store default colored image
#        default_colors = self.wc.to_array()
        #plt.title("Custom colors")
        #plt.imshow(wc.recolor(color_func=grey_color_func, random_state=3))
        #wc.to_file("a_new_hope.png")
        #plt.axis("off")
        plt.figure(figsize=(15,12))
        #plt.title("Default colors")
        #plt.imshow(default_colors)
        plt.imshow(self.wc.recolor(color_func=image_colors))
        plt.axis("off")
        plt.show()

if __name__ == '__main__':

    trend = news()
    trend.getNews()
    trend.displayHeadlines()
    trend.generateWordCloud()
#    trend.exportHeadlines()