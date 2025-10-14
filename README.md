# Asistencias Transistemas

## Qué es

`transis-assist` es un script que se conecta al drive de asistencias y en base a distintos archivos forma una tabla de alumnes y las asistencias a través de la cursada.

## Cómo funciona

El script se conecta a drive y toma:
* Logs de zoom subidos
* Respuestas de formulario de asistencia
* Datos de asistencias justificadas
Una vez recopila estos datos de manera local, los cruza entre sí para obtener:
* Las fechas de cada clase (de manera dinámica, en caso de haber cambiado el día de alguna)
* Quiénes estuvieron presentes; a su vez, para mantener un trackeo más preciso, este presente se divide en:
  * `ambos`: quienes estuvieron presentes en los logs de zoom y respondieron al formulario de asistencia
  * `log`: quienes solo estuvieron presentes en el log
  * `form`: quienes solo completaron el formulario de asistencia, pero no estuvieron registrados en el log
  * `parcial`: quienes estuvieron presentes un tiempo determinado (de momento, menor a 30 minutos) en la clase en zoom
  * `ausente`
  * `justificado`
Una vez los datos son recopilados y comparados entre sí, el script crea un par de archivos de utilidad:
* `final_results`: lista final de asistencia, la cual es actualizada directamente en el drive (actualmente se sube a una sección de datos, dado que el script sigue en modo de prueba)
* `review`: lista de personas que aparecen en los logs de zoom o en las respuestas a formularios, pero sus datos no corresponden a los de ningún alumne

## Cómo ejecutarlo

El script en sí solo requiere tener nuestras propias `keys.json` setteadas en el archivo `datamanager.py` (abajo mejor explicado), luego de eso solo es necesario correr el script como cualquier script de python via cmd/terminal o desde mismo un IDE.
```
python3 main.py
```

## Qué necesita para ejecutarse

Para correr el script, lo básico es tener python 3 y las dependencias del proyecto.
Adicionalmente, van a haber valores a modificar en `util/datamanager.py`, la cual es una clase donde están los valores de las carpetas de drive donde el script busca datos y donde actualiza archivos como el de resultados. Esta clase también requiere de un archivo `keys.json` que corresponde a las keys de una cuenta de google utilizada para correr scripts.
La organización de la carpeta de asistencia es la siguiente:
* 📁 Asistencia
  * 📁 Logs zoom
  * 📁 Forms
  * 📝 Asistencia (hoja de resultados)
  * 📝 Ausencias justificadas
  * 📝 Revisión (review)
En sí la organización no es lo más importante, dado que el script toma los ids de cada carpeta o archivo, pero es bueno para darle claridad.

## Tareas a realizar y completadas

* ✔️ **Done:** Obtener archivos dinámicamente desde el drive
* ✔️ **Done:** Actualizar o subir archivos directo a drive
* ✔️ **Done:** Agregar los datos de faltas justificadas de manera dinámica
* ✔️ **Done:** Descarga de archivos solo si no existen en local o si hay versiones actualizadas (sobre respuestas de form)
* 🔶 **To do:** Separar las variables relacionadas al drive en un archivo separado, para no tenerlas explícitas en `datamanager`
